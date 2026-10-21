"""Programa da disciplina → unidades e tópicos (○ tópico, • subtópico)."""

from dataclasses import dataclass, field

from estudos.importacao.idioma import numero_de_unidade

_NIVEL_1 = "○◦▪"
_NIVEL_2 = "•‣–-"


@dataclass
class TopicoExtraido:
    titulo: str
    filhos: list["TopicoExtraido"] = field(default_factory=list)


@dataclass
class UnidadeExtraida:
    numero: int
    titulo: str
    topicos: list[TopicoExtraido] = field(default_factory=list)


def _marcador(linha: str) -> tuple[int | None, str]:
    """(nível, resto da linha). Nível None quando a linha não começa com marcador."""
    if linha[:1] in _NIVEL_1:
        return 1, linha[1:].strip()
    if linha[:1] in _NIVEL_2:
        return 2, linha[1:].strip()
    return None, linha


def extrair_programa(texto: str) -> list[UnidadeExtraida]:
    unidades: list[UnidadeExtraida] = []
    nivel_pendente: int | None = None   # marcador sozinho na linha: o item é a próxima linha
    ultimo: TopicoExtraido | None = None
    for bruta in texto.split("\n"):
        linha = bruta.strip()
        if not linha:
            continue
        numero = numero_de_unidade(linha)
        if numero is not None:
            unidades.append(UnidadeExtraida(numero, linha))
            nivel_pendente, ultimo = None, None
            continue
        if not unidades:
            continue  # cabeçalho do documento
        nivel, resto = _marcador(linha)
        if nivel is not None and not resto:
            nivel_pendente = nivel
            continue
        if nivel is None and nivel_pendente is not None:
            nivel, nivel_pendente = nivel_pendente, None
        if nivel is None:
            if ultimo is not None:
                ultimo.titulo = f"{ultimo.titulo} {linha}"
            continue
        unidade = unidades[-1]
        ultimo = TopicoExtraido(resto)
        if nivel == 2 and unidade.topicos:
            unidade.topicos[-1].filhos.append(ultimo)
        else:
            unidade.topicos.append(ultimo)
    return unidades
