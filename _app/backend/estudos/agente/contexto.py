"""Contexto inicial do assistente: o que a tela tem aberto, já buscado nos materiais da matéria (abordagem C da spec:
o app entrega o óbvio de saída, e o modelo tem ferramentas para buscar mais).

Cada pedaço leva o rótulo de citação que o modelo deve usar ("[Stewart p. 312]", "[resumo 14.1 Polares]").
"""

import datetime
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from estudos.rag.busca import Resultado, buscar_modo, exercicio_de, resposta_de
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice, indice_desatualizado
from estudos.repos import documentos

_TRECHOS_TEORIA = 3
_MAX_CARACTERES_SECAO = 30_000   # teoria da seção para o resumidor (o resto o modelo busca)
_MAX_CARACTERES_DOCUMENTO = 8_000
_AVISO_INDICE = "O índice da busca está sendo refeito: os trechos do livro ficaram de fora desta resposta."
_NOMES_MARCA = {"err": "errei", "dub": "dúvida", "ok": "acertei"}


@dataclass(frozen=True)
class Pedaco:
    rotulo: str
    texto: str


def nome_fonte(con: sqlite3.Connection, fonte_id: int) -> str:
    linha = con.execute("SELECT titulo, caminho FROM fonte WHERE id = ?", (fonte_id,)).fetchone()
    if linha is None:
        return "fonte"
    return linha["titulo"] or linha["caminho"].rsplit("/", 1)[-1].removesuffix(".pdf")


def rotulo_de(con: sqlite3.Connection, r: Resultado) -> str:
    """Rótulo de citação de um resultado da busca: "[<livro ou slides> p. N]" ou "[<título do texto>]"."""
    if r.fonte_id is not None:
        return f"[{nome_fonte(con, r.fonte_id)} p. {r.pagina}]" if r.pagina else f"[{nome_fonte(con, r.fonte_id)}]"
    return f"[{r.titulo}]"


def _texto_do_trecho(indice: sqlite3.Connection, trecho_id: int) -> str:
    linha = indice.execute("SELECT texto FROM trecho WHERE id = ?", (trecho_id,)).fetchone()
    return linha["texto"] if linha else ""


def _documento(con: sqlite3.Connection, raiz: Path, rotulo: str, onde: str, valor: int) -> list[Pedaco]:
    linha = con.execute(f"SELECT id FROM documento WHERE {onde} = ? ORDER BY atualizado_em DESC LIMIT 1", (valor,)).fetchone()
    if linha is None:
        return []
    doc = documentos.obter(con, linha["id"])
    try:
        corpo = documentos.ler_corpo(raiz, doc)
    except OSError:
        return []
    return [Pedaco(f"[{rotulo} {doc.titulo}]", corpo[:_MAX_CARACTERES_DOCUMENTO])]


def _indice(con: sqlite3.Connection, raiz: Path):
    """Índice pronto para ler, ou None quando está sendo refeito (versão antiga no disco)."""
    if indice_desatualizado(raiz):
        return None
    sincronizar(con, raiz, esperar=False)
    return abrir_indice(raiz)


def _secao_da_lista(con: sqlite3.Connection, lista_id: int):
    return con.execute("SELECT s.id, s.codigo, s.titulo FROM lista_secao ls JOIN secao_livro s ON s.id = ls.secao_id "
                       "WHERE ls.lista_id = ? ORDER BY s.id LIMIT 1", (lista_id,)).fetchone()


def _de_questao(con: sqlite3.Connection, raiz: Path, questao_id: int) -> list[Pedaco]:
    q = con.execute("SELECT q.*, l.codigo AS lista_codigo, l.id AS lid FROM questao q JOIN lista l ON l.id = q.lista_id "
                    "WHERE q.id = ?", (questao_id,)).fetchone()
    if q is None:
        raise ValueError(f"questão {questao_id} não encontrada")
    pedacos = [Pedaco(f"[Lista {q['lista_codigo']} #{q['rotulo']}]", q["enunciado_md"] or "(enunciado só no PDF da lista)")]
    secao = _secao_da_lista(con, q["lid"])
    indice = _indice(con, raiz)
    if indice is None:
        pedacos.append(Pedaco("aviso", _AVISO_INDICE))
    else:
        with closing(indice):
            if secao and secao["codigo"] == q["lista_codigo"] and q["rotulo"].isdigit():
                ex = exercicio_de(indice, secao["id"], int(q["rotulo"]))
                if ex is not None:
                    resp = resposta_de(indice, secao["id"], int(q["rotulo"]))
                    texto = ex.trecho + (f"\n\nResposta do gabarito do livro: {resp.trecho}" if resp else "")
                    rotulo = f"[{nome_fonte(con, ex.fonte_id)} {secao['codigo']} exercício {q['rotulo']} p. {ex.pagina}]"
                    pedacos.append(Pedaco(rotulo, texto))
            consulta = " ".join(filter(None, [q["enunciado_md"], secao["titulo"] if secao else ""]))
            _, achados = buscar_modo(indice, consulta, secao_id=secao["id"] if secao else None, limite=_TRECHOS_TEORIA,
                                     partes=["teoria"])
            pedacos += [Pedaco(rotulo_de(con, r), _texto_do_trecho(indice, r.trecho_id)) for r in achados]
    if secao:
        pedacos += _documento(con, raiz, "resumo", "tipo = 'resumo' AND secao_id", secao["id"])
    pedacos += _documento(con, raiz, "resolução", "tipo = 'resolucao' AND questao_id", questao_id)
    return pedacos


def _de_secao(con: sqlite3.Connection, raiz: Path, secao_id: int) -> list[Pedaco]:
    secao = con.execute("SELECT id, codigo, titulo FROM secao_livro WHERE id = ?", (secao_id,)).fetchone()
    if secao is None:
        raise ValueError(f"seção {secao_id} não encontrada")
    pedacos = [Pedaco(f"[seção {secao['codigo']}]", f"{secao['codigo']} {secao['titulo']}")]
    indice = _indice(con, raiz)
    if indice is None:
        pedacos.append(Pedaco("aviso", _AVISO_INDICE))
    else:
        with closing(indice):
            total = 0
            for t in indice.execute("SELECT id, fonte_id, pagina, texto FROM trecho WHERE secao_id = ? AND parte = 'teoria' "
                                    "AND fonte_id IS NOT NULL ORDER BY ordem", (secao_id,)):
                if total > _MAX_CARACTERES_SECAO:
                    break
                total += len(t["texto"])
                pedacos.append(Pedaco(f"[{nome_fonte(con, t['fonte_id'])} p. {t['pagina']}]", t["texto"]))
            _, slides = buscar_modo(indice, secao["titulo"], tipos=["slides"], limite=_TRECHOS_TEORIA, partes=["teoria"])
            pedacos += [Pedaco(rotulo_de(con, r), _texto_do_trecho(indice, r.trecho_id)) for r in slides]
    return pedacos + _documento(con, raiz, "resumo", "tipo = 'resumo' AND secao_id", secao_id)


def _geral(con: sqlite3.Connection) -> list[Pedaco]:
    hoje = datetime.date.today().isoformat()
    prova = con.execute("SELECT e.data, e.descricao, u.numero FROM evento e LEFT JOIN unidade u ON u.id = e.unidade_id "
                        "WHERE e.tipo = 'prova' AND e.data >= ? ORDER BY e.data LIMIT 1", (hoje,)).fetchone()
    pedacos = []
    if prova:
        pedacos.append(Pedaco("[próxima prova]", f"{prova['descricao'] or 'Prova'} da {prova['numero']}ª unidade em "
                                                 f"{prova['data']} (hoje é {hoje})."))
    marcadas = con.execute(
        "SELECT m.estado, l.codigo, q.rotulo, q.enunciado_md, s.codigo AS secao FROM marcacao m "
        "JOIN questao q ON q.id = m.questao_id JOIN lista l ON l.id = q.lista_id "
        "LEFT JOIN lista_secao ls ON ls.lista_id = l.id LEFT JOIN secao_livro s ON s.id = ls.secao_id "
        "WHERE m.estado IN ('err', 'dub') ORDER BY l.codigo, q.ordem").fetchall()
    if marcadas:
        linhas = [f"- Lista {m['codigo']} #{m['rotulo']} ({_NOMES_MARCA[m['estado']]}"
                  f"{', seção ' + m['secao'] if m['secao'] else ''}): {(m['enunciado_md'] or '')[:120]}" for m in marcadas]
        pedacos.append(Pedaco("[marcações]", "\n".join(linhas)))
    unidade = prova["numero"] if prova else None
    topicos = con.execute("SELECT t.titulo, t.status FROM topico t JOIN unidade u ON u.id = t.unidade_id "
                          + ("WHERE u.numero = ? " if unidade else "") + "ORDER BY t.unidade_id, t.ordem",
                          (unidade,) if unidade else ()).fetchall()
    if topicos:
        pedacos.append(Pedaco("[tópicos]", "\n".join(f"- {t['titulo']} ({t['status']})" for t in topicos)))
    return pedacos or [Pedaco("[matéria]", "Nenhuma marcação, prova ou tópico cadastrado ainda.")]


def montar_contexto(con: sqlite3.Connection, raiz: Path, alvo: str, papel: str) -> list[Pedaco]:
    """Alvo "questao:<id>", "secao:<id>" ou "geral"."""
    tipo, _, valor = alvo.partition(":")
    if tipo == "questao" and valor.isdigit():
        return _de_questao(con, raiz, int(valor))
    if tipo == "secao" and valor.isdigit():
        return _de_secao(con, raiz, int(valor))
    if alvo == "geral":
        return _geral(con)
    raise ValueError(f"alvo inválido: {alvo}")


def contexto_em_texto(pedacos: list[Pedaco]) -> str:
    return "\n\n".join(f"{p.rotulo}\n{p.texto}" for p in pedacos)
