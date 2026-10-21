"""Programa da disciplina → unidades e tópicos.

O nível do item vem da ordem em que os marcadores aparecem: o primeiro tipo de marcador visto é o nível 1 (tópico),
o segundo é o nível 2 (subtópico). Assim um programa só com "•" fica todo no nível 1.
"""

from dataclasses import dataclass, field

from estudos.importacao.idioma import numero_de_unidade

_MARCADORES = "○◦▪•‣–-"


@dataclass
class TopicoExtraido:
    titulo: str
    filhos: list["TopicoExtraido"] = field(default_factory=list)


@dataclass
class UnidadeExtraida:
    numero: int
    titulo: str
    topicos: list[TopicoExtraido] = field(default_factory=list)


def _continua(anterior: str, linha: str) -> bool:
    """Linha sem marcador só continua o item anterior se claramente for o resto da frase."""
    return linha[0].islower() or anterior.endswith((",", "-", " e", " de", " em", " da", " do"))


def extrair_programa(texto: str) -> list[UnidadeExtraida]:
    unidades: list[UnidadeExtraida] = []
    ordem_marcadores: list[str] = []
    marcador_pendente: str | None = None   # marcador sozinho na linha: o item é a próxima linha
    ultimo: TopicoExtraido | None = None
    for bruta in texto.split("\n"):
        linha = bruta.strip()
        if not linha:
            continue
        numero = numero_de_unidade(linha)
        if numero is not None:
            unidades.append(UnidadeExtraida(numero, linha))
            marcador_pendente, ultimo = None, None
            continue
        if not unidades:
            continue  # cabeçalho do documento
        marcador = linha[0] if linha[0] in _MARCADORES else None
        resto = linha[1:].strip() if marcador else linha
        if marcador and not resto:
            marcador_pendente = marcador
            continue
        if marcador is None and marcador_pendente is not None:
            marcador, marcador_pendente = marcador_pendente, None
        if marcador is None:
            if ultimo is not None and _continua(ultimo.titulo, linha):
                ultimo.titulo = f"{ultimo.titulo} {linha}"
            else:
                ultimo = None  # texto fora da lista de tópicos (bibliografia, avaliação…): não gruda em nada
            continue
        if marcador not in ordem_marcadores:
            ordem_marcadores.append(marcador)
        nivel = min(ordem_marcadores.index(marcador) + 1, 2)
        unidade = unidades[-1]
        ultimo = TopicoExtraido(resto)
        if nivel == 2 and unidade.topicos:
            unidade.topicos[-1].filhos.append(ultimo)
        else:
            unidade.topicos.append(ultimo)
    return unidades
