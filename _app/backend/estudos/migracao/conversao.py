"""Conversões de texto do legado. Funções puras, sem acesso a banco ou disco."""

import datetime
import re

# Base do subscrito: uma palavra (f<sub>xy</sub>) ou um único símbolo (∭<sub>E</sub>).
_SUBSCRITO = re.compile(r"(\w+|[^\s\w<>])<sub>([^<]*)</sub>")
_TROCAS = (
    (re.compile(r'<span\s+class="mono">([^<]*)</span>', re.I), r"`\1`"),
    (re.compile(r"</?(?:b|strong)>", re.I), "**"),
    (re.compile(r"</?(?:i|em)>", re.I), "*"),
    (re.compile(r"<br\s*/?>", re.I), "\n"),
    (re.compile(r"\s*<small>", re.I), " — "),
    (re.compile(r"</small>", re.I), ""),
)
_TAG = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)[^>]*>")
_DATA_CURTA = re.compile(r"^\s*(?:[A-Za-zÀ-ÿ]{3}\.?\s+)?(\d{1,2})/(\d{1,2})\s*$")
_REFERENCIA = re.compile(
    r"(?P<cod>\b\d+\.\d+|\bL\d+)\s*:?\s*(?P<lista>[⭐#\s]*\d+(?:\([a-z]\))*(?:\s*,\s*[⭐#\s]*\d+(?:\([a-z]\))*)*)"
)
_ROTULO = re.compile(r"\d+(?:\([a-z]\))*")
_NOTA = re.compile(r"^\s*Nota:\s*(\d+(?:[.,]\d+)?)\s*$", re.I)
_PERIODO = re.compile(r"^\d{4}\.\d$")


def html_para_md(texto: str) -> tuple[str, list[str]]:
    """Converte o HTML simples do legado em Markdown. Tags desconhecidas saem, o texto fica, e vira aviso."""
    md = _SUBSCRITO.sub(lambda m: f"${m.group(1)}_{{{m.group(2)}}}$", texto)
    for padrao, troca in _TROCAS:
        md = padrao.sub(troca, md)
    avisos = []
    for tag in dict.fromkeys(m.group(1).lower() for m in _TAG.finditer(md)):
        avisos.append(f"tag <{tag}> removida")
    return _TAG.sub("", md), avisos


def data_curta_para_iso(texto: str, ano: int) -> str | None:
    """'sáb 05/09' → '2026-09-05'. Qualquer outra forma (intervalos, rótulos) → None."""
    m = _DATA_CURTA.match(texto or "")
    if not m:
        return None
    try:
        return datetime.date(ano, int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None


def referencias_exercicios(texto: str) -> list[tuple[str, str]]:
    """Referências com código de seção explícito: '14.6: 4, 8' e 'L5 #6(a), ⭐#4'. Sem código, nada é inferido."""
    refs = []
    for m in _REFERENCIA.finditer(texto or ""):
        refs += [(m.group("cod"), rotulo) for rotulo in _ROTULO.findall(m.group("lista"))]
    return refs


def nota_de_tags(tags: list[str]) -> float | None:
    for tag in tags:
        m = _NOTA.match(tag)
        if m:
            return float(m.group(1).replace(",", "."))
    return None


def periodo_e_instituicao(subtitulo: str) -> tuple[str | None, str | None]:
    """'UFPE · 2026.2' → ('2026.2', 'UFPE'): partes separadas por '·'; período é a parte no formato AAAA.S."""
    partes = [p.strip() for p in (subtitulo or "").split("·") if p.strip()]
    periodo = next((p for p in partes if _PERIODO.match(p)), None)
    resto = [p for p in partes if p != periodo]
    return periodo, (" · ".join(resto) or None)


def tabela_markdown(colunas: list[str], linhas: list[list[str]]) -> str:
    def celula(valor: str) -> str:
        return str(valor).replace("|", "\\|").replace("\n", " ")

    cabecalho = "| " + " | ".join(map(celula, colunas)) + " |"
    separador = "|" + "|".join("---" for _ in colunas) + "|"
    corpo = ["| " + " | ".join(map(celula, linha)) + " |" for linha in linhas]
    return "\n".join([cabecalho, separador, *corpo])
