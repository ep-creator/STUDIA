import sqlite3
from datetime import date

from estudos.erros import NaoEncontrado
from estudos.historico import Operacao
from estudos.modelos import ORIGENS, Unidade, exigir_opcao
from estudos.repos import _base

_SELECT = """
    SELECT u.id, u.numero, u.titulo, u.origem, u.confianca,
           (SELECT min(e.data) FROM evento e WHERE e.unidade_id = u.id AND e.tipo = 'prova') AS data_prova
    FROM unidade u
"""


def criar(op: Operacao, numero: int, titulo: str = "", origem: str = "manual", confianca: float | None = None) -> int:
    exigir_opcao(origem, ORIGENS, "origem")
    return _base.inserir(op, "unidade", {"numero": numero, "titulo": titulo, "origem": origem, "confianca": confianca})


def listar(con: sqlite3.Connection) -> list[Unidade]:
    return [Unidade(**dict(linha)) for linha in con.execute(_SELECT + " ORDER BY u.numero")]


def obter(con: sqlite3.Connection, unidade_id: int) -> Unidade:
    linha = con.execute(_SELECT + " WHERE u.id = ?", (unidade_id,)).fetchone()
    if linha is None:
        raise NaoEncontrado(f"Unidade {unidade_id} não encontrada")
    return Unidade(**dict(linha))


def atualizar(op: Operacao, unidade_id: int, **campos) -> None:
    if "origem" in campos:
        exigir_opcao(campos["origem"], ORIGENS, "origem")
    _base.atualizar(op, "unidade", {"id": unidade_id}, campos)


def remover(op: Operacao, unidade_id: int) -> None:
    _base.remover(op, "unidade", {"id": unidade_id})


def unidade_atual(con: sqlite3.Connection, hoje: date) -> Unidade | None:
    """Menor unidade cuja prova ainda não passou; se todas passaram (ou nenhuma tem prova), a última."""
    todas = listar(con)
    hoje_iso = hoje.isoformat()
    futuras = [u for u in todas if u.data_prova and u.data_prova >= hoje_iso]
    if futuras:
        return futuras[0]
    return todas[-1] if todas else None
