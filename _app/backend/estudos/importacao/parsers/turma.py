"""Informações da turma → professor, horários, bibliografia e critérios de correção."""

import re
from dataclasses import dataclass, field

from estudos.importacao.idioma import DIAS_SEMANA, normalizar

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_SEPARADOR_NOME = re.compile(r"\s+[–—-]\s+")
_HORARIO = re.compile(
    r"^(?P<dia>[A-Za-zÀ-ÿ]+?)s?(?:-feiras?)?\s*:\s*(?P<h1>\d{1,2})h(?P<m1>\d{2})?\s*[-–]\s*(?P<h2>\d{1,2})h(?P<m2>\d{2})?"
)
_MARCADORES = "•▪◦‣–-"
_MAX_TITULO = 40


@dataclass
class ReferenciaExtraida:
    texto: str
    papel: str


@dataclass
class TurmaExtraida:
    professor: str | None = None
    email: str | None = None
    horarios: list[tuple[int, str, str]] = field(default_factory=list)
    referencias: list[ReferenciaExtraida] = field(default_factory=list)
    criterios: list[str] = field(default_factory=list)


def _eh_titulo(linha: str) -> bool:
    """Linha-título: curta, sem vírgula e sem pontuação final (ex.: 'Metodologia', 'Referências complementares')."""
    return len(linha) < _MAX_TITULO and "," not in linha and not linha.endswith((".", ";", ":"))


def _professor(linhas: list[str], turma: TurmaExtraida) -> None:
    for linha in linhas:
        m = _EMAIL.search(linha)
        if m:
            turma.email = m.group(0)
            nome = _SEPARADOR_NOME.split(linha[: m.start()].strip())[0].strip(" –—-")
            turma.professor = nome or None
            return


def _horarios(linhas: list[str], turma: TurmaExtraida) -> None:
    for linha in linhas:
        m = _HORARIO.match(linha)
        if not m:
            continue
        dia = DIAS_SEMANA.get(normalizar(m.group("dia")).rstrip("s"))
        if dia is not None:
            turma.horarios.append((dia, f"{int(m.group('h1')):02d}:{m.group('m1') or '00'}",
                                   f"{int(m.group('h2')):02d}:{m.group('m2') or '00'}"))


def _referencias(linhas: list[str], turma: TurmaExtraida) -> None:
    papel = None
    for linha in linhas:
        n = normalizar(linha)
        if n.startswith("referencias complementares") or n.startswith("bibliografia complementar"):
            papel = "complementar"
        elif n in ("referencia", "referencias", "bibliografia", "bibliografia basica", "referencias basicas"):
            papel = "principal"
        elif papel and _eh_titulo(linha):
            papel = None
        elif papel:
            turma.referencias.append(ReferenciaExtraida(linha, papel))


def _criterios(linhas: list[str], turma: TurmaExtraida) -> None:
    inicio = next((i for i, l in enumerate(linhas) if "criterios de avaliacao" in normalizar(l)), None)
    if inicio is None:
        return
    itens: list[str] = []
    aguardando_item = False
    for linha in linhas[inicio + 1:]:
        if linha[0] in _MARCADORES:
            resto = linha[1:].strip()
            aguardando_item = not resto
            if resto:
                itens.append(resto)
            continue
        if aguardando_item:
            itens.append(linha)
            aguardando_item = False
        elif itens and not itens[-1].endswith((";", ".")) and linha[0].islower():
            itens[-1] = f"{itens[-1]} {linha}"
        elif itens:
            break
    turma.criterios = [i.rstrip(" ;.") for i in itens]


def extrair_turma(texto: str) -> TurmaExtraida:
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    turma = TurmaExtraida()
    _professor(linhas, turma)
    _horarios(linhas, turma)
    _referencias(linhas, turma)
    _criterios(linhas, turma)
    return turma
