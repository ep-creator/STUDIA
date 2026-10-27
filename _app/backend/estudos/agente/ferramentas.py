"""Ferramentas que o modelo pode chamar. As de leitura usam a busca e o índice da matéria; as que gravam (resolução,
resumo, cartão de fórmula) abrem uma ação do Histórico com origem "agente", desfazível como qualquer edição.
"""

import sqlite3
import unicodedata
from collections.abc import Callable
from contextlib import AbstractContextManager, closing
from dataclasses import dataclass
from pathlib import Path

from estudos.agente.calculadora import calcular
from estudos.agente.contexto import nome_fonte, rotulo_de
from estudos.config import Settings
from estudos.historico import Operacao
from estudos.rag.busca import buscar_modo, exercicio_de, resposta_de
from estudos.rag.indice import abrir_indice, indice_desatualizado
from estudos.repos import documentos, formulas

_MAX_TRECHO = 1500
_MAX_SECAO = 12_000


@dataclass
class Ambiente:
    con: sqlite3.Connection
    raiz: Path
    settings: Settings
    alvo: str
    acao: Callable[[str], AbstractContextManager[Operacao]]


@dataclass(frozen=True)
class Ferramenta:
    nome: str
    descricao: str
    parametros: dict
    grava: bool
    executar: Callable[[Ambiente, dict], dict]
    aviso: str   # o que a tela mostra enquanto ela roda


class ErroFerramenta(Exception):
    pass


def _indice(ambiente: Ambiente):
    if indice_desatualizado(ambiente.raiz):
        raise ErroFerramenta("o índice da busca está sendo refeito; tente de novo em alguns minutos")
    return abrir_indice(ambiente.raiz)


def _texto(indice, trecho_id: int) -> str:
    linha = indice.execute("SELECT texto FROM trecho WHERE id = ?", (trecho_id,)).fetchone()
    return (linha["texto"] if linha else "")[:_MAX_TRECHO]


def _secao_por_codigo(con: sqlite3.Connection, codigo: str):
    linha = con.execute("SELECT s.id, s.codigo, s.titulo FROM secao_livro s JOIN livro l ON l.fonte_id = s.livro_id "
                        "WHERE s.codigo = ? ORDER BY l.papel = 'principal' DESC, s.id LIMIT 1", (str(codigo).strip(),)).fetchone()
    if linha is None:
        raise ErroFerramenta(f"seção {codigo} não está cadastrada")
    return linha


def _alvo(ambiente: Ambiente, tipo: str) -> int:
    nome, _, valor = ambiente.alvo.partition(":")
    if nome != tipo or not valor.isdigit():
        raise ErroFerramenta(f"esta conversa não é sobre uma {tipo}")
    return int(valor)


def _buscar(ambiente: Ambiente, args: dict) -> dict:
    consulta = str(args.get("consulta", ""))
    tipos = [args["tipo"]] if args.get("tipo") else None
    with closing(_indice(ambiente)) as indice:
        _, teoria = buscar_modo(indice, consulta, tipos=tipos, limite=5, partes=["teoria"])
        _, exercicios = buscar_modo(indice, consulta, limite=2, partes=["exercicio"])
        trechos = [{"rotulo": rotulo_de(ambiente.con, r), "texto": _texto(indice, r.trecho_id)} for r in teoria]
        trechos += [{"rotulo": rotulo_de(ambiente.con, r) + " (exercício do livro)", "texto": _texto(indice, r.trecho_id)}
                    for r in exercicios]
    return {"trechos": trechos} if trechos else {"trechos": [], "aviso": "nada encontrado; tente outras palavras"}


def _ler_secao(ambiente: Ambiente, args: dict) -> dict:
    secao = _secao_por_codigo(ambiente.con, args.get("codigo", ""))
    partes, total = [], 0
    with closing(_indice(ambiente)) as indice:
        for t in indice.execute("SELECT fonte_id, pagina, texto FROM trecho WHERE secao_id = ? AND parte = 'teoria' "
                                "AND fonte_id IS NOT NULL ORDER BY ordem", (secao["id"],)):
            if total > _MAX_SECAO:
                break
            total += len(t["texto"])
            partes.append({"rotulo": f"[{nome_fonte(ambiente.con, t['fonte_id'])} p. {t['pagina']}]", "texto": t["texto"]})
    return {"secao": f"{secao['codigo']} {secao['titulo']}", "trechos": partes}


def _exercicio_do_livro(ambiente: Ambiente, args: dict) -> dict:
    secao = _secao_por_codigo(ambiente.con, args.get("secao", ""))
    numero = int(args.get("numero", 0))
    with closing(_indice(ambiente)) as indice:
        ex = exercicio_de(indice, secao["id"], numero)
        if ex is None:
            raise ErroFerramenta(f"exercício {numero} da seção {secao['codigo']} não está no índice")
        resp = resposta_de(indice, secao["id"], numero)
    return {"rotulo": f"[{nome_fonte(ambiente.con, ex.fonte_id)} {secao['codigo']} exercício {numero} p. {ex.pagina}]",
            "enunciado": ex.trecho, "resposta_do_gabarito": resp.trecho if resp else None}


def _calcular(ambiente: Ambiente, args: dict) -> dict:
    return calcular(args)


def _slug(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return "-".join("".join(c if c.isalnum() else " " for c in base).split())[:60] or "documento"


def _gravado(tipo: str, ident: int, titulo: str, op: Operacao) -> dict:
    return {"gravado": {"tipo": tipo, "id": ident, "titulo": titulo, "grupo_id": op.grupo_id}}


def _salvar_resolucao(ambiente: Ambiente, args: dict) -> dict:
    questao_id = _alvo(ambiente, "questao")
    q = ambiente.con.execute("SELECT q.rotulo, l.codigo, l.unidade_id, l.id AS lid FROM questao q JOIN lista l "
                             "ON l.id = q.lista_id WHERE q.id = ?", (questao_id,)).fetchone()
    secao = ambiente.con.execute("SELECT secao_id FROM lista_secao WHERE lista_id = ? LIMIT 1", (q["lid"],)).fetchone()
    titulo = f"Resolução {q['codigo']}-{q['rotulo']}"
    with ambiente.acao(f"Agente: {titulo.lower()}") as op:
        did = documentos.salvar(op, "resolucao", _slug(f"{q['codigo']}-{q['rotulo']}"), titulo, str(args.get("texto", "")),
                                unidade_id=q["unidade_id"], secao_id=secao["secao_id"] if secao else None,
                                questao_id=questao_id, origem="agente")
    return _gravado("documento", did, titulo, op)


def _salvar_resumo(ambiente: Ambiente, args: dict) -> dict:
    secao_id = _alvo(ambiente, "secao")
    secao = ambiente.con.execute("SELECT codigo, titulo FROM secao_livro WHERE id = ?", (secao_id,)).fetchone()
    existente = ambiente.con.execute("SELECT caminho, titulo, unidade_id FROM documento WHERE tipo = 'resumo' AND secao_id = ? "
                                     "ORDER BY atualizado_em DESC LIMIT 1", (secao_id,)).fetchone()
    if existente:  # reescreve o resumo da seção (a versão anterior fica no Histórico)
        nome, titulo, unidade = existente["caminho"].rsplit("/", 1)[-1], existente["titulo"], existente["unidade_id"]
    else:
        nome, titulo, unidade = _slug(f"{secao['codigo']} {secao['titulo']}"), f"{secao['codigo']} {secao['titulo']}", None
    with ambiente.acao(f"Agente: resumo {secao['codigo']}") as op:
        did = documentos.salvar(op, "resumo", nome, titulo, str(args.get("texto", "")), unidade_id=unidade,
                                secao_id=secao_id, origem="agente")
    return _gravado("documento", did, titulo, op)


def _unidade_da_secao(con: sqlite3.Connection, secao_id: int) -> int:
    linha = (con.execute("SELECT t.unidade_id FROM topico_secao ts JOIN topico t ON t.id = ts.topico_id "
                         "WHERE ts.secao_id = ? LIMIT 1", (secao_id,)).fetchone()
             or con.execute("SELECT l.unidade_id FROM lista_secao ls JOIN lista l ON l.id = ls.lista_id "
                            "WHERE ls.secao_id = ? LIMIT 1", (secao_id,)).fetchone()
             or con.execute("SELECT id AS unidade_id FROM unidade ORDER BY numero LIMIT 1").fetchone())
    if linha is None:
        raise ErroFerramenta("a matéria ainda não tem unidades para guardar o cartão de fórmula")
    return linha["unidade_id"]


def _adicionar_formula(ambiente: Ambiente, args: dict) -> dict:
    tipo, _, valor = ambiente.alvo.partition(":")
    if tipo == "secao":
        secao_id = int(valor)
    elif tipo == "questao":
        linha = ambiente.con.execute("SELECT ls.secao_id FROM questao q JOIN lista_secao ls ON ls.lista_id = q.lista_id "
                                     "WHERE q.id = ? LIMIT 1", (int(valor),)).fetchone()
        if linha is None:
            raise ErroFerramenta("a lista desta questão não está ligada a uma seção do livro")
        secao_id = linha["secao_id"]
    else:
        raise ErroFerramenta("cartão de fórmula precisa de uma seção")
    titulo = str(args.get("titulo", "")).strip() or "Fórmula"
    with ambiente.acao(f"Agente: fórmula {titulo}") as op:
        fid = formulas.criar(op, _unidade_da_secao(ambiente.con, secao_id), titulo, str(args.get("latex", "")),
                             notas_md=str(args.get("quando", "")), secao_id=secao_id, origem="agente")
    return _gravado("formula", fid, titulo, op)


def _objeto(propriedades: dict, obrigatorios: list[str]) -> dict:
    return {"type": "object", "properties": propriedades, "required": obrigatorios}


_TEXTO = {"type": "string"}
FERRAMENTAS: dict[str, Ferramenta] = {f.nome: f for f in [
    Ferramenta("buscar", "Busca nos materiais da matéria (livro, slides, listas, resumos). Devolve trechos de teoria e "
               "exercícios do livro parecidos, cada um com o rótulo para citar.",
               _objeto({"consulta": _TEXTO, "tipo": {"type": "string", "description": "livro, slides, lista ou resumo"}},
                       ["consulta"]), False, _buscar, "Buscando nos materiais…"),
    Ferramenta("ler_secao", "Lê a teoria de uma seção do livro pelo código (ex.: 14.7).",
               _objeto({"codigo": _TEXTO}, ["codigo"]), False, _ler_secao, "Lendo a seção do livro…"),
    Ferramenta("exercicio_do_livro", "Enunciado original de um exercício do livro e a resposta do gabarito, se houver.",
               _objeto({"secao": _TEXTO, "numero": {"type": "integer"}}, ["secao", "numero"]), False, _exercicio_do_livro,
               "Abrindo o exercício no livro…"),
    Ferramenta("calcular", "Confere uma conta com SymPy/SciPy. operacao: integral (limites de dentro para fora, um par por "
               "variável), derivada (ordem), limite (ponto), resolver (expressoes, com '='), pontos_criticos ou avaliar. "
               "Use ^ ou ** para potência e as funções sin, cos, tan, exp, log, sqrt, pi, oo.",
               _objeto({"operacao": _TEXTO, "expressao": _TEXTO, "expressoes": {"type": "array", "items": _TEXTO},
                        "variaveis": {"type": "array", "items": _TEXTO},
                        "limites": {"type": "array", "items": {"type": "array", "items": _TEXTO}},
                        "ponto": _TEXTO, "ordem": {"type": "array", "items": _TEXTO}}, ["operacao", "variaveis"]),
               False, _calcular, "Conferindo a conta…"),
    Ferramenta("salvar_resolucao", "Grava a resolução completa (Markdown) da questão desta conversa.",
               _objeto({"texto": _TEXTO}, ["texto"]), True, _salvar_resolucao, "Gravando a resolução…"),
    Ferramenta("salvar_resumo", "Grava o resumo (Markdown) da seção desta conversa; substitui o resumo atual.",
               _objeto({"texto": _TEXTO}, ["texto"]), True, _salvar_resumo, "Gravando o resumo…"),
    Ferramenta("adicionar_formula", "Cria um cartão de fórmula da seção: título curto, a fórmula em LaTeX e quando usar.",
               _objeto({"titulo": _TEXTO, "latex": _TEXTO, "quando": _TEXTO}, ["titulo", "latex"]), True,
               _adicionar_formula, "Criando o cartão de fórmula…"),
]}


def declaracoes(nomes: list[str]) -> list[dict]:
    return [{"name": f.nome, "description": f.descricao, "parameters": f.parametros}
            for n in nomes if (f := FERRAMENTAS.get(n))]


def executar(ambiente: Ambiente, permitidas: list[str], nome: str, argumentos: dict) -> dict:
    """Resultado para o modelo; erro vira {"erro": …} (o modelo segue, não quebra a resposta)."""
    if nome not in permitidas or nome not in FERRAMENTAS:
        return {"erro": f"ferramenta não permitida aqui: {nome}"}
    try:
        return FERRAMENTAS[nome].executar(ambiente, argumentos or {})
    except ErroFerramenta as e:
        return {"erro": str(e)}
    except (ValueError, KeyError, TypeError, sqlite3.DatabaseError) as e:
        return {"erro": f"não consegui: {e}"}
