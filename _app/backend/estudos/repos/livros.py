import sqlite3

from estudos.erros import DadoInvalido
from estudos.historico import Operacao
from estudos.modelos import ORIGENS, PAPEIS_LIVRO, Livro, SecaoLivro, exigir_opcao
from estudos.repos import _base


def criar(
    op: Operacao,
    fonte_id: int,
    papel: str,
    autor: str = "",
    titulo_obra: str = "",
    edicao: str = "",
    offset_pagina: int = 0,
    gabarito_pdf_ini: int | None = None,
    gabarito_pdf_fim: int | None = None,
) -> None:
    exigir_opcao(papel, PAPEIS_LIVRO, "papel do livro")
    _base.inserir(op, "livro", {
        "fonte_id": fonte_id, "papel": papel, "autor": autor, "titulo_obra": titulo_obra, "edicao": edicao,
        "offset_pagina": offset_pagina, "gabarito_pdf_ini": gabarito_pdf_ini, "gabarito_pdf_fim": gabarito_pdf_fim,
    })


def principal(con: sqlite3.Connection) -> Livro | None:
    linha = con.execute("SELECT * FROM livro WHERE papel = 'principal' ORDER BY fonte_id LIMIT 1").fetchone()
    return Livro(**dict(linha)) if linha else None


def criar_secao(
    op: Operacao,
    livro_id: int,
    codigo: str,
    titulo: str,
    pagina_pdf_ini: int,
    pagina_pdf_fim: int,
    nivel: int | None = None,
    origem: str = "manual",
    confianca: float | None = None,
) -> int:
    exigir_opcao(origem, ORIGENS, "origem")
    if pagina_pdf_fim < pagina_pdf_ini:
        raise DadoInvalido(f"Seção {codigo}: página final {pagina_pdf_fim} antes da inicial {pagina_pdf_ini}.")
    return _base.inserir(op, "secao_livro", {
        "livro_id": livro_id, "codigo": codigo, "titulo": titulo,
        "nivel": nivel if nivel is not None else codigo.count(".") + 1,
        "pagina_pdf_ini": pagina_pdf_ini, "pagina_pdf_fim": pagina_pdf_fim, "origem": origem, "confianca": confianca,
    })


def secao_por_codigo(con: sqlite3.Connection, livro_id: int, codigo: str) -> SecaoLivro | None:
    linha = con.execute(
        "SELECT * FROM secao_livro WHERE livro_id = ? AND codigo = ?", (livro_id, codigo)
    ).fetchone()
    return SecaoLivro(**dict(linha)) if linha else None


def listar_secoes(con: sqlite3.Connection, livro_id: int) -> list[SecaoLivro]:
    return [SecaoLivro(**dict(l)) for l in con.execute(
        "SELECT * FROM secao_livro WHERE livro_id = ? ORDER BY pagina_pdf_ini, id", (livro_id,)
    )]


def vincular_equivalente(op: Operacao, secao_id: int, equivalente_id: int) -> None:
    for a, b in ((secao_id, equivalente_id), (equivalente_id, secao_id)):
        chave = {"secao_id": a, "equivalente_id": b}
        if _base.obter(op.con, "secao_equivalente", chave) is None:
            _base.inserir(op, "secao_equivalente", chave)


def vincular_topico(
    op: Operacao, topico_id: int, secao_id: int, confianca: float | None = None, confirmado: bool = False
) -> None:
    chave = {"topico_id": topico_id, "secao_id": secao_id}
    valores = {"confianca": confianca, "confirmado": int(confirmado)}
    if _base.obter(op.con, "topico_secao", chave) is None:
        _base.inserir(op, "topico_secao", {**chave, **valores})
    else:
        _base.atualizar(op, "topico_secao", chave, valores)
