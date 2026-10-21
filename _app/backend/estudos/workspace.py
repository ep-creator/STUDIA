"""Workspace multi-matéria: cada subpasta com materia.db é uma matéria, identificada pelo uid gravado no banco."""

import datetime
import re
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from estudos.db.conexao import aplicar_migracoes, conectar, transacao
from estudos.erros import DadoInvalido, NaoEncontrado

ARQUIVO_DB = "materia.db"
SUBPASTAS = (
    "fontes/documentos",
    "fontes/livros",
    "fontes/listas",
    "fontes/slides",
    "fontes/provas",
    "fontes/anotacoes",
    "conteudo/resumos",
    "conteudo/resolucoes",
    "conteudo/planos",
    "conteudo/anotacoes",
    "figuras",
    ".versoes",
)
_PROIBIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVADOS_WINDOWS = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


@dataclass(frozen=True)
class MateriaRef:
    uid: str
    nome: str
    pasta: Path

    @property
    def db(self) -> Path:
        return self.pasta / ARQUIVO_DB


def nome_pasta_valido(nome: str) -> str:
    limpo = nome.strip()
    if not limpo:
        raise DadoInvalido("Informe o nome da matéria.")
    if _PROIBIDOS.search(limpo):
        raise DadoInvalido('O nome não pode conter < > : " / \\ | ? *')
    if limpo.split(".")[0].upper() in _RESERVADOS_WINDOWS:
        raise DadoInvalido(f"'{limpo}' é um nome reservado do Windows.")
    if limpo.endswith("."):
        raise DadoInvalido("O nome não pode terminar com ponto.")
    if limpo[0] in "_.":
        raise DadoInvalido("O nome não pode começar com '_' ou '.' (pastas assim são ignoradas).")
    return limpo


def _ler_ref(pasta: Path) -> MateriaRef:
    with closing(conectar(pasta / ARQUIVO_DB)) as con:
        aplicar_migracoes(con)
        linha = con.execute("SELECT uid, nome FROM materia").fetchone()
    if linha is None:
        raise NaoEncontrado(f"Banco sem registro de matéria em {pasta.name}")
    return MateriaRef(uid=linha["uid"], nome=linha["nome"], pasta=pasta)


def descobrir_materias(workspace: Path) -> list[MateriaRef]:
    refs = []
    for pasta in workspace.iterdir():
        if pasta.is_dir() and pasta.name[0] not in "_." and (pasta / ARQUIVO_DB).is_file():
            try:
                refs.append(_ler_ref(pasta))
            except (NaoEncontrado, sqlite3.DatabaseError):
                continue  # banco vazio, corrompido ou de outro programa: não derruba as outras matérias
    return sorted(refs, key=lambda r: r.nome.casefold())


def criar_materia(workspace: Path, nome: str, periodo: str | None = None) -> MateriaRef:
    nome = nome_pasta_valido(nome)
    pasta = workspace / nome
    if pasta.exists():
        raise DadoInvalido(f"A pasta '{nome}' já existe.")
    for sub in SUBPASTAS:
        (pasta / sub).mkdir(parents=True)
    uid = uuid.uuid4().hex
    with closing(conectar(pasta / ARQUIVO_DB)) as con:
        aplicar_migracoes(con)
        with transacao(con):
            con.execute(
                "INSERT INTO materia (uid, nome, periodo, criada_em) VALUES (?, ?, ?, ?)",
                (uid, nome, periodo, datetime.datetime.now().isoformat(timespec="seconds")),
            )
    return MateriaRef(uid=uid, nome=nome, pasta=pasta)


def abrir_materia(workspace: Path, uid: str) -> MateriaRef:
    for ref in descobrir_materias(workspace):
        if ref.uid == uid:
            return ref
    raise NaoEncontrado(f"Matéria não encontrada: {uid}")
