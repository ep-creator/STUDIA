import sqlite3

from estudos.erros import DadoInvalido
from estudos.historico import Operacao
from estudos.modelos import Materia
from estudos.repos import _base

_CAMPOS_EDITAVEIS = {"nome", "periodo", "instituicao", "professor", "email_professor"}


def obter(con: sqlite3.Connection) -> Materia:
    linha = con.execute(
        "SELECT id, uid, nome, periodo, instituicao, professor, email_professor FROM materia"
    ).fetchone()
    return Materia(**dict(linha))


def atualizar(op: Operacao, **campos) -> None:
    _base.atualizar(op, "materia", {"id": obter(op.con).id}, _filtrar(campos))


def _filtrar(campos: dict) -> dict:
    proibidos = set(campos) - _CAMPOS_EDITAVEIS
    if proibidos:
        raise DadoInvalido(f"Campos não editáveis: {sorted(proibidos)}")
    return campos
