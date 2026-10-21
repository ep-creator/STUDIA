import sqlite3

from estudos.historico import Operacao
from estudos.modelos import ORIGENS, Formula, exigir_opcao
from estudos.repos import _base


def criar(
    op: Operacao,
    unidade_id: int,
    titulo: str,
    corpo_tex: str,
    notas_md: str = "",
    secao_id: int | None = None,
    origem: str = "manual",
) -> int:
    exigir_opcao(origem, ORIGENS, "origem")
    ordem = op.con.execute(
        "SELECT coalesce(max(ordem), 0) + 1 FROM formula WHERE unidade_id = ?", (unidade_id,)
    ).fetchone()[0]
    return _base.inserir(op, "formula", {
        "unidade_id": unidade_id, "secao_id": secao_id, "titulo": titulo, "corpo_tex": corpo_tex,
        "notas_md": notas_md, "ordem": ordem, "origem": origem,
    })


def listar(con: sqlite3.Connection, unidade_id: int) -> list[Formula]:
    return [Formula(**dict(l)) for l in con.execute(
        "SELECT * FROM formula WHERE unidade_id = ? ORDER BY ordem, id", (unidade_id,)
    )]


def atualizar(op: Operacao, formula_id: int, **campos) -> None:
    _base.atualizar(op, "formula", {"id": formula_id}, campos)


def remover(op: Operacao, formula_id: int) -> None:
    _base.remover(op, "formula", {"id": formula_id})
