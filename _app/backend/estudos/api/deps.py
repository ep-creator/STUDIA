"""Dependências das rotas: settings, matéria pelo uid, conexão por requisição e ação com histórico."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from fastapi import Depends, Request

from estudos.config import Settings
from estudos.db.conexao import conectar
from estudos.historico import Operacao, operacao, podar
from estudos.workspace import MateriaRef, abrir_materia


def obter_settings(request: Request) -> Settings:
    return request.app.state.settings


def materia_dep(materia_uid: str, settings: Settings = Depends(obter_settings)) -> MateriaRef:
    return abrir_materia(settings.workspace, materia_uid)


@dataclass
class Contexto:
    con: sqlite3.Connection
    materia: MateriaRef
    settings: Settings

    @contextmanager
    def acao(self, descricao: str) -> Iterator[Operacao]:
        """Uma ação do usuário: transação + grupo de histórico; depois poda o histórico pelo limite configurado."""
        with operacao(self.con, descricao, self.materia.pasta) as op:
            yield op
        podar(self.con, self.settings.historico_max_grupos, self.materia.pasta)


def contexto_dep(
    materia: MateriaRef = Depends(materia_dep), settings: Settings = Depends(obter_settings)
) -> Iterator[Contexto]:
    con = conectar(materia.db)
    try:
        yield Contexto(con, materia, settings)
    finally:
        con.close()
