"""Busca no índice: BM25 do FTS5 com filtros exatos de unidade, seção e tipo.

A unidade é resolvida na hora pelo banco da matéria (anexado como "m"): seção ligada a tópico da unidade, fonte de
lista da unidade, ou documento da unidade (ou global, ou com a unidade como extra).
"""

import re
import sqlite3
from dataclasses import dataclass

from estudos.importacao.idioma import STOPWORDS, sem_acento, singular

_PALAVRA = re.compile(r"[a-z0-9]+")
_MIN_PREFIXO = 5      # palavras com 5+ letras viram prefixo (casa singular/plural e flexões)
_MIN_RADICAL = 4
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


def _radical(palavra: str) -> str:
    base = singular(palavra)
    if base.endswith(("al", "el", "il")):
        base = base[:-2]
    elif base[-1] in "aeo":
        base = base[:-1]
    return base if len(base) >= _MIN_RADICAL else palavra


def montar_consulta(texto: str) -> str | None:
    """Termos do usuário viram termos entre aspas unidos por OR; operadores do FTS5 nunca passam."""
    termos = []
    for palavra in _PALAVRA.findall(sem_acento(texto or "").lower()):
        if len(palavra) < 2 or palavra in STOPWORDS:
            continue
        termo = f'"{_radical(palavra)}"*' if len(palavra) >= _MIN_PREFIXO else f'"{palavra}"'
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


def buscar(
    indice: sqlite3.Connection,
    consulta: str = "",
    unidade: int | None = None,
    secao_id: int | None = None,
    tipos: list[str] | None = None,
    limite: int = 8,
) -> list[Resultado]:
    fts = montar_consulta(consulta)
    params: dict = {"limite": max(1, min(int(limite), 50))}
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
    return [
        Resultado(
            trecho_id=l["id"], origem=l["origem"], tipo=l["tipo"], titulo=l["titulo"], trecho=l["resumo"],
            pagina=l["pagina"], secao_id=l["secao_id"], secao_codigo=l["secao_codigo"], fonte_id=l["fonte_id"],
            documento_id=l["documento_id"], score=round(l["score"], 4),
        )
        for l in linhas
    ]


def secao_completa(indice: sqlite3.Connection, secao_id: int) -> str:
    """Texto inteiro da seção do livro, na ordem das páginas."""
    linhas = indice.execute(
        "SELECT texto FROM trecho WHERE secao_id = ? AND fonte_id IS NOT NULL ORDER BY id", (secao_id,)
    ).fetchall()
    return "\n\n".join(l["texto"] for l in linhas)
