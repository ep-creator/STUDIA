"""Calendário de atividades → aulas, aulas extras e provas por unidade, mais segunda chamada e exame final."""

import datetime
import re
from dataclasses import dataclass, field

from estudos.importacao.idioma import DIAS_SEMANA, normalizar, numero_de_unidade
from estudos.importacao.pdf import TabelaPdf

_ANO = re.compile(r"\b(20\d\d)\b")
_DATA = re.compile(r"^(\d{1,2})/(\d{1,2})\b\s*(.*)$")
_HORARIO = re.compile(r"(\d{1,2})h(\d{2})?\s*[-–]\s*(\d{1,2})h(\d{2})?")
_PROVA = re.compile(r"^(?:\S+\s+)?(?:exame|prova)(?:\s+\d+)?\s*:\s*(.+)$", re.I)  # "Primeiro exame:", "Prova 2:"
_FERIADO = re.compile(r"\b(feriado|recesso|n[ãa]o haver[áa] aula|sem aula|suspens)", re.I)
_ANOTACAO_PROVA = re.compile(r"\b(prova|exame)\b", re.I)
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
    revisar: bool = False


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


def _data_anotada(unidade: UnidadeCalendario, data: str, anotacao: str) -> None:
    """Classifica a data pela anotação, por regras explícitas; anotação que nenhuma regra explica pede revisão."""
    inicio, fim = _horario(anotacao)
    descricao = anotacao.strip("() ")
    if not anotacao:
        unidade.aulas.append(EventoExtraido("aula", data))
    elif _FERIADO.search(anotacao):
        unidade.aulas.append(EventoExtraido("feriado", data, descricao=descricao))
    elif _ANOTACAO_PROVA.search(anotacao) and unidade.prova is None:
        unidade.prova = EventoExtraido("prova", data, inicio, fim, descricao)
    elif inicio or "extra" in anotacao.lower():
        unidade.aulas.append(EventoExtraido("extra", data, inicio, fim, descricao))
    else:
        unidade.aulas.append(EventoExtraido("aula", data, descricao=descricao, revisar=True))


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
            _data_anotada(calendario.unidades[-1], data, m.group(3).strip())
    return calendario


# ---- Calendário em tabela ---------------------------------------------------------------------------------------
#
# Dois formatos, o mesmo CalendarioExtraido do texto:
# - uma linha por aula (Data | Dia | Descrição …): "Prova N" é a prova da unidade N e fecha a unidade, "Prova final"
#   é o exame final e "2ª chamada" a segunda chamada; o resto é aula;
# - grade de provas (dias nas colunas, horários nas linhas, matérias nas células, como a de um departamento): só
#   entram as células com o nome da matéria, e a linha acima da tabela diz de qual unidade são as provas.

_MESES = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8, "set": 9, "out": 10,
          "nov": 11, "dez": 12}
# 15/09, 04/02/27 e 08.09; com ponto, só dois dígitos de cada lado ("1.5" é seção de livro)
_DIA_MES_NUMERO = re.compile(r"^(?:(\d{1,2})\s*/\s*(\d{1,2})|(\d{2})\.(\d{2}))(?:[/.]\d{2,4})?(?![\d.])")
_DIA_MES_NOME = re.compile(r"^(\d{1,2})\s*(?:-|/|\s|\s+de\s+)\s*(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)",
                           re.I)                                                         # 11-ago, 3 de dezembro
_HORAS = re.compile(r"(\d{1,2})[:h](\d{2})?\s*[-–]\s*(\d{1,2})[:h](\d{2})?")
_PROVA_NUMERADA = re.compile(r"^(?:prova|exame|avaliacao) (\d+)\b")
_PROVA_FINAL = re.compile(r"\b(?:prova|exame|avaliacao) final\b")
_CHAMADA = re.compile(r"\b(?:2 ?a|segunda) cham")
_UNIDADE_NUMERADA = re.compile(r"\b(\d+) ?a? unidade\b|\bunidade (\d+)\b")
_LISTA_DE_NUMEROS = re.compile(r"(.+?) ((?:\d+ (?:e )?)*\d+)")  # "calculo 1 2 e 3" ("Cálculo 1, 2 e 3")


def dia_mes(texto: str) -> tuple[int, int] | None:
    """Data no começo do texto, nos formatos dos calendários: 15/09, 08.09 (3ª feira), 11-ago, 3 de dezembro."""
    texto = texto.strip()
    if m := _DIA_MES_NUMERO.match(texto):
        dia, mes = int(m.group(1) or m.group(3)), int(m.group(2) or m.group(4))
    elif m := _DIA_MES_NOME.match(texto):
        dia, mes = int(m.group(1)), _MESES[m.group(2).lower()]
    else:
        return None
    return (dia, mes) if 1 <= dia <= 31 and 1 <= mes <= 12 else None


def _horas(texto: str) -> tuple[str | None, str | None]:
    m = _HORAS.search(texto.replace("\n", " "))
    if not m:
        return None, None
    return f"{int(m.group(1)):02d}:{m.group(2) or '00'}", f"{int(m.group(3)):02d}:{m.group(4) or '00'}"


def _tem_materia(texto: str, nome: str) -> bool:
    """A célula fala da matéria: uma das linhas, ou todas juntas, é o nome dela ("Geometria" + "Analítica"); uma
    lista de números ("Cálculo 1, 2 e 3") vale para cada um."""
    alvo = normalizar(nome)
    linhas = [normalizar(l) for l in texto.split("\n") if l.strip()]
    for candidato in [*linhas, " ".join(linhas)]:
        if candidato == alvo:
            return True
        m = _LISTA_DE_NUMEROS.fullmatch(candidato)
        if m and any(f"{m.group(1)} {n}" == alvo for n in re.findall(r"\d+", m.group(2))):
            return True
    return False


def _destino(titulo: str) -> tuple[str, int | None] | None:
    """De qual unidade (ou exame) é a grade, pela linha mais próxima acima dela que diga."""
    for linha in reversed([l for l in titulo.split("\n") if l.strip()]):
        n = normalizar(linha)
        if _CHAMADA.search(n):
            return "segunda_chamada", None
        if "final" in n:
            return "exame_final", None
        if (m := _UNIDADE_NUMERADA.search(n)) or (numero := numero_de_unidade(linha)) is not None:
            return "prova", int(m.group(1) or m.group(2)) if m else numero
    return None


def _unidade(calendario: CalendarioExtraido, numero: int) -> UnidadeCalendario:
    unidade = next((u for u in calendario.unidades if u.numero == numero), None)
    if unidade is None:
        unidade = UnidadeCalendario(numero)
        calendario.unidades.append(unidade)
        calendario.unidades.sort(key=lambda u: u.numero)
    return unidade


def _dia_da_semana(texto: str) -> bool:
    n = normalizar(texto).removesuffix(" feira")
    return n in DIAS_SEMANA or n in {d[:3] for d in DIAS_SEMANA}


def _ler_grade(tabela: TabelaPdf, cabecalho: int, nome: str, datas: _Datas, calendario: CalendarioExtraido) -> None:
    destino = _destino(tabela.titulo)
    if destino is None:
        return
    dias = [(c, dm) for c in tabela.linhas[cabecalho] if (dm := dia_mes(c.texto))]
    for linha in tabela.linhas[cabecalho + 1:]:
        inicio, fim = _horas(linha[0].texto)
        for celula in linha[1:]:
            if not _tem_materia(celula.texto, nome):
                continue
            # a coluna do dia é a do cabeçalho que mais se sobrepõe à célula
            coluna, (dia, mes) = max(dias, key=lambda d: min(d[0].x1, celula.x1) - max(d[0].x0, celula.x0))
            if (data := datas.iso(dia, mes)) is None:
                continue
            tipo, numero = destino
            evento = EventoExtraido(tipo, data, inicio, fim)
            if numero is None:
                calendario.eventos.append(evento)
            else:
                _unidade(calendario, numero).prova = evento


def _ler_aulas(tabela: TabelaPdf, datas: _Datas, calendario: CalendarioExtraido) -> None:
    atual = calendario.unidades[-1].numero + 1 if calendario.unidades else 1
    aulas: list[tuple[int, EventoExtraido]] = []
    for linha in tabela.linhas:
        dm = dia_mes(linha[0].texto)
        if dm is None or (data := datas.iso(*dm)) is None:
            continue
        resto = [c.texto.replace("\n", " ") for c in linha[1:]]
        # dia da semana e números soltos (carga horária) não descrevem a aula
        descricao = " ".join(t for t in resto if not t.isdigit() and not _dia_da_semana(t))
        n = normalizar(descricao)
        if _CHAMADA.search(n):
            calendario.eventos.append(EventoExtraido("segunda_chamada", data, descricao=descricao))
        elif _PROVA_FINAL.search(n):
            calendario.eventos.append(EventoExtraido("exame_final", data, descricao=descricao))
        elif m := _PROVA_NUMERADA.match(n):
            numero = int(m.group(1))
            _unidade(calendario, numero).prova = EventoExtraido("prova", data, descricao=descricao)
            atual = numero + 1
        elif _FERIADO.search(descricao):
            aulas.append((atual, EventoExtraido("feriado", data, descricao=descricao)))
        else:  # "Prova Area 2" fala de prova sem dizer qual: fica como aula, para o usuário revisar
            aulas.append((atual, EventoExtraido("aula", data, descricao=descricao,
                                                revisar=bool(_ANOTACAO_PROVA.search(descricao)))))
    ultima = max((u.numero for u in calendario.unidades), default=1)
    for numero, aula in aulas:  # o que vem depois da última prova fica na última unidade
        _unidade(calendario, min(numero, ultima)).aulas.append(aula)


def extrair_calendario_tabelas(tabelas: list[TabelaPdf], ano: int | None, nome_materia: str) -> CalendarioExtraido:
    calendario = CalendarioExtraido(ano=ano)
    datas = _Datas(ano)
    for tabela in tabelas:
        cabecalho = next((i for i, l in enumerate(tabela.linhas[:2])
                          if sum(1 for c in l if dia_mes(c.texto)) >= 2), None)
        if cabecalho is not None:
            _ler_grade(tabela, cabecalho, nome_materia, datas, calendario)
        elif sum(1 for l in tabela.linhas if dia_mes(l[0].texto)) >= 3:
            _ler_aulas(tabela, datas, calendario)
    return calendario
