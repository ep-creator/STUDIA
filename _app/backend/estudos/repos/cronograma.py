import sqlite3

from estudos.historico import Operacao
from estudos.modelos import ORIGENS, Sessao, exigir_opcao
from estudos.repos import _base


def criar_sessao(
    op: Operacao,
    unidade_id: int,
    codigo: str,
    data: str | None = None,
    foco_md: str = "",
    ordem: int | None = None,
    origem: str = "manual",
) -> int:
    exigir_opcao(origem, ORIGENS, "origem")
    if ordem is None:
        ordem = op.con.execute(
            "SELECT coalesce(max(ordem), 0) + 1 FROM sessao_estudo WHERE unidade_id = ?", (unidade_id,)
        ).fetchone()[0]
    return _base.inserir(op, "sessao_estudo", {
        "unidade_id": unidade_id, "codigo": codigo, "data": data, "foco_md": foco_md, "ordem": ordem, "origem": origem,
    })


def definir_feito(op: Operacao, sessao_id: int, feito: bool) -> None:
    _base.atualizar(op, "sessao_estudo", {"id": sessao_id}, {"feito": int(feito)})


def vincular_questoes(op: Operacao, sessao_id: int, questao_ids: list[int]) -> None:
    """Substitui o conjunto de questões da sessão."""
    atuais = {l["questao_id"] for l in op.con.execute(
        "SELECT questao_id FROM sessao_questao WHERE sessao_id = ?", (sessao_id,)
    )}
    novas = set(questao_ids)
    for questao_id in sorted(atuais - novas):
        _base.remover(op, "sessao_questao", {"sessao_id": sessao_id, "questao_id": questao_id})
    for questao_id in sorted(novas - atuais):
        _base.inserir(op, "sessao_questao", {"sessao_id": sessao_id, "questao_id": questao_id})


def listar(con: sqlite3.Connection, unidade_id: int) -> list[Sessao]:
    sessoes = []
    for l in con.execute("SELECT * FROM sessao_estudo WHERE unidade_id = ? ORDER BY ordem, id", (unidade_id,)):
        questoes = tuple(r[0] for r in con.execute(
            "SELECT questao_id FROM sessao_questao WHERE sessao_id = ? ORDER BY questao_id", (l["id"],)
        ))
        sessoes.append(Sessao(**{**dict(l), "feito": bool(l["feito"]), "questao_ids": questoes}))
    return sessoes


def atualizar(op: Operacao, sessao_id: int, **campos) -> None:
    if "feito" in campos:
        campos["feito"] = int(bool(campos["feito"]))
    _base.atualizar(op, "sessao_estudo", {"id": sessao_id}, campos)


def remover(op: Operacao, sessao_id: int) -> None:
    _base.remover(op, "sessao_estudo", {"id": sessao_id})
