"""Arquivo do índice de busca, separado do banco da matéria (é 100% derivável e fica fora do Git).

O banco da matéria é anexado como "m" em modo somente leitura: a busca consulta vínculos atuais (unidade de uma seção,
lista de uma fonte…) na hora, então o índice nunca guarda informação que possa ficar desatualizada.
"""

import sqlite3
from pathlib import Path

from estudos.workspace import ARQUIVO_DB

VERSAO_INDICE = 2   # 2: trecho.vetor e tabela meta (modelo e dimensão dos vetores)
PASTA_INDICE = ".indice"
_ARQUIVO = "indice.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS estado (
    origem TEXT PRIMARY KEY,
    assinatura TEXT NOT NULL,
    indexado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trecho (
    id INTEGER PRIMARY KEY,
    origem TEXT NOT NULL,
    fonte_id INTEGER,
    documento_id INTEGER,
    secao_id INTEGER,
    tipo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    texto TEXT NOT NULL,
    pagina INTEGER,
    ordem INTEGER NOT NULL,
    vetor BLOB                 -- embedding normalizado (float32); NULL sem embeddings
);
CREATE TABLE IF NOT EXISTS meta (
    chave TEXT PRIMARY KEY,    -- "modelo" e "dimensao" dos vetores gravados
    valor TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trecho_origem ON trecho (origem);
CREATE INDEX IF NOT EXISTS idx_trecho_secao ON trecho (secao_id);
CREATE VIRTUAL TABLE IF NOT EXISTS trecho_fts USING fts5(
    titulo, texto, content='trecho', content_rowid='id', tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS trecho_ai AFTER INSERT ON trecho BEGIN
    INSERT INTO trecho_fts (rowid, titulo, texto) VALUES (new.id, new.titulo, new.texto);
END;
CREATE TRIGGER IF NOT EXISTS trecho_ad AFTER DELETE ON trecho BEGIN
    INSERT INTO trecho_fts (trecho_fts, rowid, titulo, texto) VALUES ('delete', old.id, old.titulo, old.texto);
END;
CREATE TRIGGER IF NOT EXISTS trecho_au AFTER UPDATE ON trecho BEGIN
    INSERT INTO trecho_fts (trecho_fts, rowid, titulo, texto) VALUES ('delete', old.id, old.titulo, old.texto);
    INSERT INTO trecho_fts (rowid, titulo, texto) VALUES (new.id, new.titulo, new.texto);
END;
"""


class IndiceDesatualizado(sqlite3.DatabaseError):
    """Arquivo de índice de outra versão: é descartado e refeito."""


def eh_corrupcao(erro: BaseException) -> bool:
    """Só arquivo inválido/corrompido (ou de outra versão) justifica apagar o índice; banco ocupado não."""
    return isinstance(erro, IndiceDesatualizado) or getattr(erro, "sqlite_errorname", "") in ("SQLITE_NOTADB", "SQLITE_CORRUPT")


def caminho_indice(raiz: Path) -> Path:
    return raiz / PASTA_INDICE / _ARQUIVO


def _apagar(caminho: Path) -> None:
    for sufixo in ("", "-wal", "-shm", "-journal"):
        Path(f"{caminho}{sufixo}").unlink(missing_ok=True)


def _conectar(caminho: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"{caminho.resolve().as_uri()}?mode=rwc", uri=True, isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=5000")
    return con


def _preparar(con: sqlite3.Connection) -> None:
    """Cria o schema só quando o arquivo é novo; abrir um índice existente não precisa de escrita."""
    versao = con.execute("PRAGMA user_version").fetchone()[0]
    existe = con.execute("SELECT count(*) FROM sqlite_master").fetchone()[0] > 0
    if existe and versao == VERSAO_INDICE:
        return
    if existe:
        raise IndiceDesatualizado(f"índice na versão {versao}, esperada {VERSAO_INDICE}")
    con.execute("PRAGMA journal_mode=WAL")  # leitores não esperam enquanto a indexação escreve
    con.executescript(_SCHEMA)
    con.execute(f"PRAGMA user_version = {VERSAO_INDICE}")


def descartar_indice(raiz: Path, caminho: Path | None = None) -> None:
    _apagar(caminho or caminho_indice(raiz))


def abrir_indice(raiz: Path, caminho: Path | None = None) -> sqlite3.Connection:
    caminho = caminho or caminho_indice(raiz)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    try:
        con = _conectar(caminho)
        _preparar(con)
    except sqlite3.DatabaseError as erro:
        if not eh_corrupcao(erro):
            raise  # ocupado ou outro problema transitório: o índice continua lá
        try:
            con.close()
        except Exception:  # conexão pode nem ter sido criada
            pass
        _apagar(caminho)
        con = _conectar(caminho)
        _preparar(con)
    banco = (raiz / ARQUIVO_DB).resolve().as_uri()
    con.execute("ATTACH DATABASE ? AS m", (f"{banco}?mode=ro",))
    return con
