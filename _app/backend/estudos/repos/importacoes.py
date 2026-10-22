"""Rascunhos de importação. Não passam pelo histórico: só a confirmação (que grava o domínio) é desfazível."""

import datetime
import json
import sqlite3

from estudos.erros import Conflito, NaoEncontrado
from estudos.modelos import ESTADOS_IMPORTACAO, Importacao, exigir_opcao


def _agora() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _importacao(linha: sqlite3.Row) -> Importacao:
    dados = dict(linha)
    dados["proposta"] = json.loads(dados.pop("proposta_json"))
    return Importacao(**dados)


def criar(con: sqlite3.Connection, fonte_id: int, tipo: str, proposta: dict) -> int:
    return con.execute(
        "INSERT INTO importacao (fonte_id, tipo, proposta_json, criada_em) VALUES (?, ?, ?, ?)",
        (fonte_id, tipo, json.dumps(proposta, ensure_ascii=False), _agora()),
    ).lastrowid


def obter(con: sqlite3.Connection, importacao_id: int) -> Importacao:
    linha = con.execute("SELECT * FROM importacao WHERE id = ?", (importacao_id,)).fetchone()
    if linha is None:
        raise NaoEncontrado(f"Importação {importacao_id} não encontrada")
    return _importacao(linha)


def por_fonte(con: sqlite3.Connection, fonte_id: int) -> Importacao | None:
    linha = con.execute(
        "SELECT * FROM importacao WHERE fonte_id = ? ORDER BY id DESC LIMIT 1", (fonte_id,)
    ).fetchone()
    return _importacao(linha) if linha else None


def listar(con: sqlite3.Connection, estado: str | None = None) -> list[Importacao]:
    if estado is None:
        linhas = con.execute("SELECT * FROM importacao ORDER BY id DESC")
    else:
        linhas = con.execute("SELECT * FROM importacao WHERE estado = ? ORDER BY id DESC", (estado,))
    return [_importacao(l) for l in linhas]


def atualizar_proposta(con: sqlite3.Connection, importacao_id: int, proposta: dict, tipo: str | None = None) -> None:
    atual = obter(con, importacao_id)
    if atual.estado != "proposta":
        raise Conflito(f"A importação {importacao_id} já está '{atual.estado}' e não pode mais ser editada.")
    con.execute(
        "UPDATE importacao SET proposta_json = ?, tipo = ? WHERE id = ?",
        (json.dumps(proposta, ensure_ascii=False), tipo or atual.tipo, importacao_id),
    )


def trocar_proposta(con: sqlite3.Connection, importacao_id: int, esperada: dict, nova: dict) -> bool:
    """Grava `nova` só se a proposta gravada ainda é `esperada` e está pendente (troca condicional, sem perder uma
    edição ou confirmação que aconteceu no meio). Devolve se gravou."""
    linha = con.execute("SELECT proposta_json, estado FROM importacao WHERE id = ?", (importacao_id,)).fetchone()
    if linha is None or linha["estado"] != "proposta" or json.loads(linha["proposta_json"]) != esperada:
        return False
    cursor = con.execute(
        "UPDATE importacao SET proposta_json = ? WHERE id = ? AND estado = 'proposta' AND proposta_json = ?",
        (json.dumps(nova, ensure_ascii=False), importacao_id, linha["proposta_json"]),
    )
    return cursor.rowcount == 1


def marcar(con: sqlite3.Connection, importacao_id: int, estado: str) -> None:
    exigir_opcao(estado, ESTADOS_IMPORTACAO, "estado da importação")
    obter(con, importacao_id)
    con.execute(
        "UPDATE importacao SET estado = ?, confirmada_em = ? WHERE id = ?",
        (estado, _agora() if estado == "confirmada" else None, importacao_id),
    )
