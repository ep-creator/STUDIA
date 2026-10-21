"""Conexões SQLite da matéria: PRAGMAs padronizados, transações explícitas e migrações versionadas."""

import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from itertools import count
from pathlib import Path

PASTA_MIGRACOES = Path(__file__).parent / "migracoes"
_PADRAO_MIGRACAO = re.compile(r"^(\d{4})_[\w-]+\.sql$")
_savepoints = count(1)


def conectar(caminho: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(caminho), isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=5000")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    return con


@contextmanager
def transacao(con: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Transação de escrita; quando já existe uma aberta, vira SAVEPOINT (desfaz só o bloco interno)."""
    if con.in_transaction:
        nome = f"sp_{next(_savepoints)}"
        con.execute(f"SAVEPOINT {nome}")
        try:
            yield con
        except BaseException:
            con.execute(f"ROLLBACK TO {nome}")
            con.execute(f"RELEASE {nome}")
            raise
        con.execute(f"RELEASE {nome}")
        return
    con.execute("BEGIN IMMEDIATE")
    try:
        yield con
    except BaseException:
        con.execute("ROLLBACK")
        raise
    con.execute("COMMIT")


def _comandos(script: str) -> Iterator[str]:
    """Divide um script SQL em comandos completos (respeita ';' dentro de strings e triggers)."""
    buffer = ""
    for parte in script.split(";"):
        buffer += parte + ";"
        if sqlite3.complete_statement(buffer):
            if buffer.strip(" \t\r\n;"):
                yield buffer
            buffer = ""
    if buffer.strip(" \t\r\n;"):
        raise sqlite3.OperationalError(f"Comando SQL incompleto na migração: {buffer[:80]}")


def aplicar_migracoes(con: sqlite3.Connection, pasta: Path = PASTA_MIGRACOES) -> int:
    con.execute("CREATE TABLE IF NOT EXISTS schema_versao (versao INTEGER PRIMARY KEY, aplicada_em TEXT NOT NULL)")
    atual = con.execute("SELECT coalesce(max(versao), 0) FROM schema_versao").fetchone()[0]
    arquivos = sorted(
        (int(m.group(1)), p) for p in pasta.glob("*.sql") if (m := _PADRAO_MIGRACAO.match(p.name))
    )
    for versao, arquivo in arquivos:
        if versao <= atual:
            continue
        with transacao(con):
            for comando in _comandos(arquivo.read_text(encoding="utf-8")):
                con.execute(comando)
            con.execute(
                "INSERT INTO schema_versao (versao, aplicada_em) VALUES (?, datetime('now'))", (versao,)
            )
        atual = versao
    return atual
