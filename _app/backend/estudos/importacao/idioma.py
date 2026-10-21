"""Regras do idioma (português) usadas pelos parsers: ordinais, romanos, dias da semana e normalização de texto.

Nada aqui é específico de uma disciplina.
"""

import re
import unicodedata

_ORDINAIS = (
    ("primeir", 1), ("segund", 2), ("terceir", 3), ("quart", 4), ("quint", 5), ("sext", 6),
    ("setim", 7), ("oitav", 8), ("non", 9), ("decim", 10),
)
_ORDINAL_NUMERICO = re.compile(r"^(\d{1,2})\s*[ªaº°o]$", re.I)
_ROMANO = re.compile(r"^(x{0,1})(ix|iv|v?i{0,3})$", re.I)
_VALOR_ROMANO = {"i": 1, "v": 5, "x": 10}
_NAO_ALFANUMERICO = re.compile(r"[^0-9a-z]+")
STOPWORDS = frozenset(
    "a o as os e de da do das dos em no na nos nas um uma para com por mais ou ao aos se sobre entre".split()
)
# Plural → singular, na ordem em que as terminações são testadas
_PLURAIS = (("oes", "ao"), ("aes", "ao"), ("ais", "al"), ("eis", "el"), ("res", "r"), ("zes", "z"), ("ns", "m"), ("s", ""))
DIAS_SEMANA = {"segunda": 0, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sabado": 5, "domingo": 6}


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    return _NAO_ALFANUMERICO.sub(" ", sem_acento(texto).lower()).strip()


def _romano_para_int(palavra: str) -> int | None:
    if not palavra or not _ROMANO.match(palavra):
        return None
    valores = [_VALOR_ROMANO[c] for c in palavra.lower()]
    return sum(-v if i + 1 < len(valores) and v < valores[i + 1] else v for i, v in enumerate(valores)) or None


def ordinal_para_int(palavra: str) -> int | None:
    """'Terceira' → 3, '3ª' → 3, 'IV' → 4. Qualquer outra coisa → None."""
    palavra = (palavra or "").strip()
    m = _ORDINAL_NUMERICO.match(palavra)
    if m:
        return int(m.group(1))
    base = normalizar(palavra)
    for prefixo, numero in _ORDINAIS:
        if base.startswith(prefixo) and base[len(prefixo):] in ("a", "o", "as", "os"):
            return numero
    return _romano_para_int(palavra)


def singular(palavra: str) -> str:
    if len(palavra) < 4:
        return palavra
    for plural, troca in _PLURAIS:
        if palavra.endswith(plural):
            return palavra[: -len(plural)] + troca
    return palavra


def tokens_relevantes(texto: str) -> list[str]:
    return [singular(t) for t in normalizar(texto).split() if t not in STOPWORDS and not t.isdigit()]


_CABECALHO_UNIDADE = re.compile(r"^(?:(?P<ord>\S+)\s+unidade|unidade\s+(?P<num>\S+))\s*:?$", re.I)


def numero_de_unidade(linha: str) -> int | None:
    """'Primeira Unidade', '1ª Unidade', 'Unidade II', 'Unidade 3' → número; qualquer outra linha → None."""
    m = _CABECALHO_UNIDADE.match(linha.strip())
    if not m:
        return None
    valor = m.group("ord") or m.group("num")
    return int(valor) if valor.isdigit() else ordinal_para_int(valor)
