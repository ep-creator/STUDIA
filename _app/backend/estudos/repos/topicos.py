import sqlite3

from estudos.historico import Operacao
from estudos.modelos import ORIGENS, STATUS_TOPICO, Topico, exigir_opcao
from estudos.repos import _base


def criar(
    op: Operacao,
    unidade_id: int,
    titulo: str,
    pai_id: int | None = None,
    ordem: int | None = None,
    origem: str = "manual",
) -> int:
    exigir_opcao(origem, ORIGENS, "origem")
    if ordem is None:
        ordem = op.con.execute(
            "SELECT coalesce(max(ordem), 0) + 1 FROM topico WHERE unidade_id = ? AND pai_id IS ?",
            (unidade_id, pai_id),
        ).fetchone()[0]
    return _base.inserir(op, "topico", {
        "unidade_id": unidade_id, "pai_id": pai_id, "ordem": ordem, "titulo": titulo, "origem": origem,
    })


def listar(con: sqlite3.Connection, unidade_id: int) -> list[Topico]:
    """Tópicos da unidade em ordem de leitura: cada pai seguido dos seus filhos."""
    todos = [Topico(**dict(l)) for l in con.execute(
        "SELECT * FROM topico WHERE unidade_id = ? ORDER BY ordem, id", (unidade_id,)
    )]
    filhos: dict[int | None, list[Topico]] = {}
    for t in todos:
        filhos.setdefault(t.pai_id, []).append(t)
    ordenados: list[Topico] = []

    def visitar(pai_id: int | None) -> None:
        for t in filhos.get(pai_id, []):
            ordenados.append(t)
            visitar(t.id)

    visitar(None)
    return ordenados


def definir_status(op: Operacao, topico_id: int, status: str) -> None:
    exigir_opcao(status, STATUS_TOPICO, "status")
    _base.atualizar(op, "topico", {"id": topico_id}, {"status": status})


def atualizar(op: Operacao, topico_id: int, **campos) -> None:
    if "status" in campos:
        exigir_opcao(campos["status"], STATUS_TOPICO, "status")
    _base.atualizar(op, "topico", {"id": topico_id}, campos)


def remover(op: Operacao, topico_id: int) -> None:
    _base.remover(op, "topico", {"id": topico_id})
