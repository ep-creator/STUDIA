import sqlite3

from estudos.historico import Operacao
from estudos.modelos import ORIGENS, TIPOS_EVENTO, Evento, exigir_opcao
from estudos.repos import _base


def criar(
    op: Operacao,
    tipo: str,
    data: str,
    unidade_id: int | None = None,
    hora_inicio: str | None = None,
    hora_fim: str | None = None,
    descricao: str = "",
    origem: str = "manual",
) -> int:
    exigir_opcao(tipo, TIPOS_EVENTO, "tipo de evento")
    exigir_opcao(origem, ORIGENS, "origem")
    return _base.inserir(op, "evento", {
        "tipo": tipo, "data": data, "unidade_id": unidade_id, "hora_inicio": hora_inicio,
        "hora_fim": hora_fim, "descricao": descricao, "origem": origem,
    })


def listar(con: sqlite3.Connection, unidade_id: int | None = None) -> list[Evento]:
    sql = "SELECT * FROM evento"
    params: tuple = ()
    if unidade_id is not None:
        sql += " WHERE unidade_id = ?"
        params = (unidade_id,)
    sql += " ORDER BY data, coalesce(hora_inicio, ''), id"
    return [Evento(**dict(linha)) for linha in con.execute(sql, params)]


def remover(op: Operacao, evento_id: int) -> None:
    _base.remover(op, "evento", {"id": evento_id})
