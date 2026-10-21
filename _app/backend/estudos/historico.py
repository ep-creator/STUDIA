"""Histórico transacional: cada ação do usuário é um grupo de mudanças que pode ser desfeito por inteiro."""

import datetime
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from estudos.db.conexao import transacao
from estudos.repos._base import aplicar_estado


@dataclass(frozen=True)
class GrupoHistorico:
    id: int
    momento: str
    descricao: str
    desfaz_grupo: int | None
    desfeito_em: str | None


def _agora() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


class Operacao:
    def __init__(self, con: sqlite3.Connection, grupo_id: int, raiz: Path | None) -> None:
        self.con = con
        self.grupo_id = grupo_id
        self.raiz = raiz
        self._ordem = 0

    @property
    def total_mudancas(self) -> int:
        return self._ordem

    def _inserir(self, **campos) -> None:
        self._ordem += 1
        self.con.execute(
            "INSERT INTO historico_mudanca (grupo_id, ordem, tabela, chave_json, antes_json, depois_json, arquivo, versao_arquivo)"
            " VALUES (:grupo_id, :ordem, :tabela, :chave_json, :antes_json, :depois_json, :arquivo, :versao_arquivo)",
            {"grupo_id": self.grupo_id, "ordem": self._ordem, "tabela": None, "chave_json": None,
             "antes_json": None, "depois_json": None, "arquivo": None, "versao_arquivo": None, **campos},
        )

    def registrar(self, tabela: str, chave: dict, antes: dict | None, depois: dict | None) -> None:
        self._inserir(
            tabela=tabela,
            chave_json=json.dumps(chave, ensure_ascii=False),
            antes_json=None if antes is None else json.dumps(antes, ensure_ascii=False),
            depois_json=None if depois is None else json.dumps(depois, ensure_ascii=False),
        )

    def registrar_arquivo(self, caminho_rel: str, versao_rel: str | None) -> None:
        self._inserir(arquivo=caminho_rel, versao_arquivo=versao_rel)


@contextmanager
def operacao(con: sqlite3.Connection, descricao: str, raiz: Path | None = None) -> Iterator[Operacao]:
    with transacao(con):
        cursor = con.execute(
            "INSERT INTO historico_grupo (momento, descricao) VALUES (?, ?)", (_agora(), descricao)
        )
        op = Operacao(con, cursor.lastrowid, raiz)
        yield op
        if op.total_mudancas == 0:
            con.execute("DELETE FROM historico_grupo WHERE id = ?", (op.grupo_id,))


def _grupo(linha: sqlite3.Row) -> GrupoHistorico:
    return GrupoHistorico(
        id=linha["id"], momento=linha["momento"], descricao=linha["descricao"],
        desfaz_grupo=linha["desfaz_grupo"], desfeito_em=linha["desfeito_em"],
    )


def listar(con: sqlite3.Connection, limite: int = 50) -> list[GrupoHistorico]:
    linhas = con.execute("SELECT * FROM historico_grupo ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
    return [_grupo(linha) for linha in linhas]


def _desfazer_mudanca(op: Operacao, mudanca: sqlite3.Row) -> None:
    alvo = None if mudanca["antes_json"] is None else json.loads(mudanca["antes_json"])
    aplicar_estado(op, mudanca["tabela"], json.loads(mudanca["chave_json"]), alvo)


def desfazer_ultimo(con: sqlite3.Connection, raiz: Path | None = None) -> GrupoHistorico | None:
    with transacao(con):
        original = con.execute(
            "SELECT * FROM historico_grupo WHERE desfeito_em IS NULL AND desfaz_grupo IS NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if original is None:
            return None
        mudancas = con.execute(
            "SELECT * FROM historico_mudanca WHERE grupo_id = ? ORDER BY ordem DESC", (original["id"],)
        ).fetchall()
        with operacao(con, f"Desfazer: {original['descricao']}", raiz) as op:
            con.execute("UPDATE historico_grupo SET desfaz_grupo = ? WHERE id = ?", (original["id"], op.grupo_id))
            for mudanca in mudancas:
                _desfazer_mudanca(op, mudanca)
        con.execute("UPDATE historico_grupo SET desfeito_em = ? WHERE id = ?", (_agora(), original["id"]))
        return _grupo(con.execute("SELECT * FROM historico_grupo WHERE id = ?", (original["id"],)).fetchone())


def podar(con: sqlite3.Connection, max_grupos: int) -> int:
    with transacao(con):
        cursor = con.execute(
            "DELETE FROM historico_grupo WHERE id NOT IN (SELECT id FROM historico_grupo ORDER BY id DESC LIMIT ?)",
            (max_grupos,),
        )
        return cursor.rowcount
