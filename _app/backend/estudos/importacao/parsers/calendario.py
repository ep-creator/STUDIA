"""Calendário de atividades → aulas, aulas extras e provas por unidade, mais segunda chamada e exame final."""

import datetime
import re
from dataclasses import dataclass, field

from estudos.importacao.idioma import numero_de_unidade

_ANO = re.compile(r"\b(20\d\d)\b")
_DATA = re.compile(r"^(\d{1,2})/(\d{1,2})\b\s*(.*)$")
_HORARIO = re.compile(r"(\d{1,2})h(\d{2})?\s*[-–]\s*(\d{1,2})h(\d{2})?")
_PROVA = re.compile(r"^\S+\s+(?:exame|prova)\s*:\s*(.+)$", re.I)
_SEGUNDA_CHAMADA = re.compile(r"^segunda\s+chamada\s*:\s*(.+)$", re.I)
_EXAME_FINAL = re.compile(r"^(?:exame|prova)\s+final\s*:\s*(.+)$", re.I)
_VIRADA_DE_ANO = 6  # mês que "volta" mais de 6 meses indica o ano seguinte (semestre que cruza dezembro)


@dataclass
class EventoExtraido:
    tipo: str
    data: str
    hora_inicio: str | None = None
    hora_fim: str | None = None
    descricao: str = ""


@dataclass
class UnidadeCalendario:
    numero: int
    aulas: list[EventoExtraido] = field(default_factory=list)
    prova: EventoExtraido | None = None


@dataclass
class CalendarioExtraido:
    ano: int | None
    unidades: list[UnidadeCalendario] = field(default_factory=list)
    eventos: list[EventoExtraido] = field(default_factory=list)


def _horario(texto: str) -> tuple[str | None, str | None]:
    m = _HORARIO.search(texto)
    if not m:
        return None, None
    return f"{int(m.group(1)):02d}:{m.group(2) or '00'}", f"{int(m.group(3)):02d}:{m.group(4) or '00'}"


class _Datas:
    """Converte dd/mm em ISO acompanhando a virada de ano."""

    def __init__(self, ano: int | None) -> None:
        self.ano = ano
        self.mes_anterior: int | None = None

    def iso(self, dia: int, mes: int) -> str | None:
        if self.ano is None:
            return None
        if self.mes_anterior is not None and self.mes_anterior - mes > _VIRADA_DE_ANO:
            self.ano += 1
        self.mes_anterior = mes
        try:
            return datetime.date(self.ano, mes, dia).isoformat()
        except ValueError:
            return None


def _evento(tipo: str, resto: str, datas: _Datas) -> EventoExtraido | None:
    m = re.match(r"(\d{1,2})/(\d{1,2})\b\s*,?\s*(.*)$", resto.strip())
    if not m:
        return None
    data = datas.iso(int(m.group(1)), int(m.group(2)))
    if data is None:
        return None
    inicio, fim = _horario(m.group(3))
    return EventoExtraido(tipo, data, inicio, fim, m.group(3).strip(" ()"))


def extrair_calendario(texto: str, ano_padrao: int | None = None) -> CalendarioExtraido:
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    cabecalho = []
    for linha in linhas:
        if numero_de_unidade(linha) is not None:
            break
        cabecalho.append(linha)
    m = _ANO.search(" ".join(cabecalho))
    ano = int(m.group(1)) if m else ano_padrao
    calendario = CalendarioExtraido(ano=ano)
    datas = _Datas(ano)
    for linha in linhas:
        numero = numero_de_unidade(linha)
        if numero is not None:
            calendario.unidades.append(UnidadeCalendario(numero))
            continue
        if (m := _SEGUNDA_CHAMADA.match(linha)) and (e := _evento("segunda_chamada", m.group(1), datas)):
            calendario.eventos.append(e)
        elif (m := _EXAME_FINAL.match(linha)) and (e := _evento("exame_final", m.group(1), datas)):
            calendario.eventos.append(e)
        elif not calendario.unidades:
            continue
        elif (m := _PROVA.match(linha)) and (e := _evento("prova", m.group(1), datas)):
            calendario.unidades[-1].prova = e
        elif (m := _DATA.match(linha)) and (data := datas.iso(int(m.group(1)), int(m.group(2)))):
            anotacao = m.group(3).strip()
            inicio, fim = _horario(anotacao)
            tipo = "extra" if anotacao else "aula"
            calendario.unidades[-1].aulas.append(EventoExtraido(tipo, data, inicio, fim, anotacao.strip("()")))
    return calendario
