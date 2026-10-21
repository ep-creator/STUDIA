"""Dados da turma: horários de aula e critérios de correção do professor."""

import sqlite3

from estudos.erros import DadoInvalido
from estudos.historico import Operacao
from estudos.modelos import ORIGENS, Criterio, HorarioAula, exigir_opcao
from estudos.repos import _base


def definir_horarios(op: Operacao, horarios: list[tuple[int, str, str]]) -> None:
    """Substitui o conjunto de horários (dia_semana 0 = segunda … 6 = domingo)."""
    for dia, _, _ in horarios:
        if not 0 <= dia <= 6:
            raise DadoInvalido(f"Dia da semana inválido: {dia} (use 0 = segunda … 6 = domingo)")
    for h in listar_horarios(op.con):
        _base.remover(op, "horario_aula", {"id": h.id})
    for dia, ini, fim in horarios:
        _base.inserir(op, "horario_aula", {"dia_semana": dia, "hora_inicio": ini, "hora_fim": fim})


def listar_horarios(con: sqlite3.Connection) -> list[HorarioAula]:
    return [HorarioAula(**dict(l)) for l in con.execute("SELECT * FROM horario_aula ORDER BY dia_semana, hora_inicio")]


def definir_criterios(op: Operacao, textos: list[str], origem: str = "manual") -> None:
    exigir_opcao(origem, ORIGENS, "origem")
    for c in listar_criterios(op.con):
        _base.remover(op, "criterio_correcao", {"id": c.id})
    for ordem, texto in enumerate(textos, start=1):
        _base.inserir(op, "criterio_correcao", {"ordem": ordem, "texto": texto, "origem": origem})


def listar_criterios(con: sqlite3.Connection) -> list[Criterio]:
    return [Criterio(**dict(l)) for l in con.execute("SELECT * FROM criterio_correcao ORDER BY ordem")]
