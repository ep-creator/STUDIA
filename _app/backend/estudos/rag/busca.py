"""Busca no índice: BM25 do FTS5 (modo "texto"), cosseno dos embeddings ("vetor") ou os dois fundidos por RRF ("hibrida"),
sempre com os mesmos filtros exatos de unidade, seção e tipo.

A unidade é resolvida na hora pelo banco da matéria (anexado como "m"): seção ligada a tópico da unidade, fonte de
lista da unidade, ou documento da unidade (ou global, ou com a unidade como extra).
"""

import dataclasses
import re
import sqlite3
from dataclasses import dataclass

from estudos.importacao.idioma import STOPWORDS, radical, sem_acento

_PALAVRA = re.compile(r"[a-z0-9]+")
_MIN_PREFIXO = 5      # palavras com 5+ letras viram prefixo do radical (casa singular/plural e flexões)
_PESO_TITULO, _PESO_TEXTO = 3.0, 1.0
_TAMANHO_SNIPPET = 24


@dataclass(frozen=True)
class Resultado:
    trecho_id: int
    origem: str
    tipo: str
    titulo: str
    trecho: str
    pagina: int | None
    secao_id: int | None
    secao_codigo: str | None
    fonte_id: int | None
    documento_id: int | None
    score: float
    por: str = "texto"              # de onde veio: "texto", "sentido" ou "ambos" (modo híbrido)
    pagina_fim: int | None = None   # última página do trecho (para citar a faixa certa)
    parte: str = "teoria"           # "teoria", "exercicio" ou "resposta"
    numero: int | None = None       # número do exercício ou da resposta


def montar_consulta(texto: str) -> str | None:
    """Termos do usuário viram termos entre aspas unidos por OR; operadores do FTS5 nunca passam."""
    termos = []
    for palavra in _PALAVRA.findall(sem_acento(texto or "").lower()):
        if len(palavra) < 2 or palavra in STOPWORDS:
            continue
        termo = f'"{radical(palavra)}"*' if len(palavra) >= _MIN_PREFIXO else f'"{palavra}"'
        if termo not in termos:
            termos.append(termo)
    return " OR ".join(termos) or None


_FILTRO_UNIDADE = """
    (t.secao_id IN (
        SELECT ts.secao_id FROM m.topico_secao ts JOIN m.topico tp ON tp.id = ts.topico_id
        JOIN m.unidade u ON u.id = tp.unidade_id WHERE u.numero = :unidade)
     OR t.fonte_id IN (
        SELECT l.fonte_id FROM m.lista l JOIN m.unidade u ON u.id = l.unidade_id
        WHERE u.numero = :unidade AND l.fonte_id IS NOT NULL)
     OR t.documento_id IN (
        SELECT d.id FROM m.documento d LEFT JOIN m.unidade u ON u.id = d.unidade_id
        WHERE u.numero = :unidade OR d.unidade_id IS NULL
        UNION SELECT e.documento_id FROM m.documento_unidade_extra e JOIN m.unidade u ON u.id = e.unidade_id
        WHERE u.numero = :unidade))
"""


def _filtros(unidade: int | None, secao_id: int | None, tipos: list[str] | None, params: dict,
             partes: list[str] | None = None) -> list[str]:
    filtros = []
    if unidade is not None:
        filtros.append(_FILTRO_UNIDADE)
        params["unidade"] = unidade
    if secao_id is not None:
        filtros.append("t.secao_id = :secao")
        params["secao"] = secao_id
    if tipos:
        nomes = [f"tipo{i}" for i in range(len(tipos))]
        filtros.append(f"t.tipo IN ({', '.join(':' + n for n in nomes)})")
        params.update(zip(nomes, tipos))
    if partes:
        nomes = [f"parte{i}" for i in range(len(partes))]
        filtros.append(f"t.parte IN ({', '.join(':' + n for n in nomes)})")
        params.update(zip(nomes, partes))
    return filtros


def _resultado(l: sqlite3.Row, trecho: str, score: float, por: str = "texto") -> Resultado:
    return Resultado(
        trecho_id=l["id"], origem=l["origem"], tipo=l["tipo"], titulo=l["titulo"], trecho=trecho, pagina=l["pagina"],
        secao_id=l["secao_id"], secao_codigo=l["secao_codigo"], fonte_id=l["fonte_id"], documento_id=l["documento_id"],
        score=round(score, 4), por=por, pagina_fim=l["pagina_fim"], parte=l["parte"], numero=l["numero"],
    )


def buscar(
    indice: sqlite3.Connection,
    consulta: str = "",
    unidade: int | None = None,
    secao_id: int | None = None,
    tipos: list[str] | None = None,
    limite: int = 8,
    partes: list[str] | None = None,
) -> list[Resultado]:
    fts = montar_consulta(consulta)
    params: dict = {"limite": max(1, min(int(limite), 50))}
    filtros = _filtros(unidade, secao_id, tipos, params, partes)
    if fts:
        params["fts"] = fts
        sql = (
            f"SELECT t.*, s.codigo AS secao_codigo, bm25(trecho_fts, {_PESO_TITULO}, {_PESO_TEXTO}) AS score, "
            f"snippet(trecho_fts, 1, '[', ']', '…', {_TAMANHO_SNIPPET}) AS resumo "
            "FROM trecho_fts JOIN trecho t ON t.id = trecho_fts.rowid LEFT JOIN m.secao_livro s ON s.id = t.secao_id "
            "WHERE trecho_fts MATCH :fts"
        )
        ordem = " ORDER BY score"
    elif filtros:
        sql = (
            "SELECT t.*, s.codigo AS secao_codigo, 0.0 AS score, substr(t.texto, 1, 240) AS resumo "
            "FROM trecho t LEFT JOIN m.secao_livro s ON s.id = t.secao_id WHERE 1 = 1"
        )
        ordem = " ORDER BY t.id"
    else:
        return []
    for filtro in filtros:
        sql += f" AND {filtro}"
    linhas = indice.execute(sql + ordem + " LIMIT :limite", params).fetchall()
    return [_resultado(l, l["resumo"], l["score"]) for l in linhas]


def secao_completa(indice: sqlite3.Connection, secao_id: int) -> str:
    """Texto inteiro da seção do livro, na ordem das páginas."""
    linhas = indice.execute(
        "SELECT texto FROM trecho WHERE secao_id = ? AND fonte_id IS NOT NULL AND parte != 'resposta' ORDER BY id", (secao_id,)
    ).fetchall()
    return "\n\n".join(l["texto"] for l in linhas)


# ---- modos "vetor" e "hibrida" (peça B da Fase 6) ------------------------------------------------------------------

_K_RRF = 60          # constante padrão da Reciprocal Rank Fusion (fixa: não é ajustada no gabarito)
_TOPO_FUSAO = 50     # quantos de cada ranking entram na fusão
_RESUMO_VETOR = 240  # caracteres do trecho mostrados quando o resultado veio só pelo sentido


def fundir_rrf(rankings: list[list[int]], k: int = _K_RRF) -> list[tuple[int, float]]:
    """Ids ordenados pela soma de 1/(k + posição) em cada ranking (posição 1-based); empate fica na ordem de chegada."""
    notas: dict[int, float] = {}
    for ranking in rankings:
        for posicao, i in enumerate(ranking, start=1):
            notas[i] = notas.get(i, 0.0) + 1 / (k + posicao)
    return sorted(notas.items(), key=lambda par: par[1], reverse=True)


def _por_sentido(indice, consulta, unidade, secao_id, tipos, limite, embeddings, partes=None) -> list[Resultado]:
    from estudos.ia.embeddings import vetores_do_indice

    matriz, ids = vetores_do_indice(indice)
    if not ids:
        return []
    params: dict = {}
    filtros = _filtros(unidade, secao_id, tipos, params, partes)
    sql = "SELECT t.id FROM trecho t WHERE t.vetor IS NOT NULL" + "".join(f" AND {f}" for f in filtros)
    permitidos = {r[0] for r in indice.execute(sql, params)}
    notas = matriz @ embeddings.de_consulta(consulta)
    ordem = [ids[i] for i in notas.argsort()[::-1] if ids[i] in permitidos][:limite]
    if not ordem:
        return []
    nota = dict(zip(ids, notas.tolist()))
    marcas = ", ".join("?" * len(ordem))
    linhas = {l["id"]: l for l in indice.execute(
        f"SELECT t.*, s.codigo AS secao_codigo FROM trecho t LEFT JOIN m.secao_livro s ON s.id = t.secao_id "
        f"WHERE t.id IN ({marcas})", ordem)}
    return [_resultado(linhas[i], linhas[i]["texto"][:_RESUMO_VETOR], nota[i], "sentido") for i in ordem]


def buscar_modo(
    indice: sqlite3.Connection,
    consulta: str = "",
    unidade: int | None = None,
    secao_id: int | None = None,
    tipos: list[str] | None = None,
    limite: int = 8,
    modo: str = "texto",
    embeddings=None,
    partes: list[str] | None = None,
) -> tuple[str, list[Resultado]]:
    """Busca no modo pedido e devolve (modo efetivo, resultados). Sem embeddings ou sem vetores no índice, cai para
    "texto". Pergunta sem nenhuma palavra que conte (vazia, só pontuação ou só palavras vazias) não traz nada."""
    limite = max(1, min(int(limite), 50))
    if modo not in ("vetor", "hibrida") or embeddings is None:
        modo = "texto"
    if montar_consulta(consulta) is None:
        return modo, []
    if modo == "texto":
        return "texto", buscar(indice, consulta, unidade, secao_id, tipos, limite, partes)
    sentido = _por_sentido(indice, consulta, unidade, secao_id, tipos, _TOPO_FUSAO, embeddings, partes)
    if not sentido:
        return "texto", buscar(indice, consulta, unidade, secao_id, tipos, limite, partes)
    if modo == "vetor":
        return "vetor", sentido[:limite]
    texto = buscar(indice, consulta, unidade, secao_id, tipos, _TOPO_FUSAO, partes)
    por_id = {r.trecho_id: r for r in sentido} | {r.trecho_id: r for r in texto}  # texto tem o trecho destacado
    em_texto, em_sentido = {r.trecho_id for r in texto}, {r.trecho_id for r in sentido}
    fundido = fundir_rrf([[r.trecho_id for r in texto], [r.trecho_id for r in sentido]])[:limite]
    return "hibrida", [
        dataclasses.replace(por_id[i], score=round(nota, 5),
                            por="ambos" if i in em_texto and i in em_sentido else ("texto" if i in em_texto else "sentido"))
        for i, nota in fundido
    ]


def _linha_completa(indice: sqlite3.Connection, where: str, params: tuple) -> list[sqlite3.Row]:
    return indice.execute(
        "SELECT t.*, s.codigo AS secao_codigo FROM trecho t LEFT JOIN m.secao_livro s ON s.id = t.secao_id "
        f"WHERE {where} ORDER BY t.ordem", params).fetchall()


_ITEM_NO_TEXTO = r"(^|\n)\s*{}\.\s"


def exercicio_de(indice: sqlite3.Connection, secao_id: int, numero: int) -> Resultado | None:
    """Exercício `numero` da seção, com o texto inteiro do trecho. Exercícios curtos foram juntados ao seguinte e a
    leitura às vezes troca a ordem, então vale o trecho com esse número; senão, o trecho em que ele aparece como item."""
    linhas = _linha_completa(indice, "t.secao_id = ? AND t.parte = 'exercicio' AND t.numero IS NOT NULL", (secao_id,))
    por_numero: dict[int, list[sqlite3.Row]] = {}
    for l in linhas:
        por_numero.setdefault(l["numero"], []).append(l)
    item = re.compile(_ITEM_NO_TEXTO.format(numero))
    partes = por_numero.get(numero) or next(
        (ps for _, ps in sorted(por_numero.items(), reverse=True) if item.search("\n".join(p["texto"] for p in ps))), None)
    if not partes:
        return None
    texto = "\n".join(l["texto"] for l in partes)
    return dataclasses.replace(_resultado(partes[0], texto, 0.0), pagina_fim=partes[-1]["pagina_fim"])


def resposta_de(indice: sqlite3.Connection, secao_id: int, numero: int) -> Resultado | None:
    """Resposta do gabarito para o exercício `numero` da seção (texto inteiro), ou None."""
    linhas = _linha_completa(indice, "t.secao_id = ? AND t.parte = 'resposta' AND t.numero = ?", (secao_id, numero))
    if not linhas:
        return None
    return _resultado(linhas[0], "\n".join(l["texto"] for l in linhas), 0.0)
