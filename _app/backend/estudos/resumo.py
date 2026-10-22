"""Consultas de resumo para as telas: próxima prova, importações pendentes e vínculos de tópicos e listas."""

import sqlite3
from datetime import date


def proxima_prova(con: sqlite3.Connection, hoje: date) -> dict | None:
    linha = con.execute(
        "SELECT e.data, e.hora_inicio, u.numero FROM evento e LEFT JOIN unidade u ON u.id = e.unidade_id "
        "WHERE e.tipo = 'prova' AND e.data >= ? ORDER BY e.data, coalesce(e.hora_inicio, '') LIMIT 1",
        (hoje.isoformat(),),
    ).fetchone()
    if linha is None:
        return None
    return {"data": linha["data"], "hora_inicio": linha["hora_inicio"], "unidade": linha["numero"]}


def importacoes_pendentes(con: sqlite3.Connection) -> int:
    return con.execute("SELECT count(*) FROM importacao WHERE estado = 'proposta'").fetchone()[0]


def total_unidades(con: sqlite3.Connection) -> int:
    return con.execute("SELECT count(*) FROM unidade").fetchone()[0]


_SECAO_VINCULADA = (
    "s.id AS secao_id, s.codigo, s.titulo, s.livro_id AS fonte_id, f.caminho, s.pagina_pdf_ini "
    "FROM secao_livro s JOIN fonte f ON f.id = s.livro_id"
)


def _secao(linha: sqlite3.Row) -> dict:
    return {k: linha[k] for k in ("secao_id", "codigo", "titulo", "fonte_id", "caminho", "pagina_pdf_ini")}


def vinculos(con: sqlite3.Connection, unidade_id: int) -> dict:
    """Seções ligadas a cada tópico da unidade e, para cada lista, seus tópicos e sua seção."""
    por_topico: dict[str, list[dict]] = {}
    for linha in con.execute(
        f"SELECT ts.topico_id, {_SECAO_VINCULADA} JOIN topico_secao ts ON ts.secao_id = s.id "
        "JOIN topico t ON t.id = ts.topico_id WHERE t.unidade_id = ? ORDER BY ts.topico_id, s.pagina_pdf_ini",
        (unidade_id,),
    ):
        por_topico.setdefault(str(linha["topico_id"]), []).append(_secao(linha))
    por_lista: dict[str, dict] = {}
    for lista in con.execute("SELECT id FROM lista WHERE unidade_id = ? ORDER BY ordem", (unidade_id,)):
        secao = con.execute(
            f"SELECT {_SECAO_VINCULADA} JOIN lista_secao ls ON ls.secao_id = s.id WHERE ls.lista_id = ? "
            "ORDER BY s.pagina_pdf_ini LIMIT 1",
            (lista["id"],),
        ).fetchone()
        ids = [r[0] for r in con.execute(
            "SELECT topico_id FROM lista_topico WHERE lista_id = ? ORDER BY topico_id", (lista["id"],)
        )]
        por_lista[str(lista["id"])] = {"topicos": ids, "secao": _secao(secao) if secao else None}
    return {"topicos": por_topico, "listas": por_lista}
