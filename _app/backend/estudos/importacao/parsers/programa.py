"""Programa da disciplina → unidades e tópicos.

O nível do item vem da ordem em que os marcadores aparecem: o primeiro tipo de marcador visto é o nível 1 (tópico),
o segundo é o nível 2 (subtópico). Assim um programa só com "•" fica todo no nível 1.

Também entende o formato em frases ("1ª unidade. Tópico. Tópico.", que pode continuar nas linhas seguintes) e o
cronograma de aulas ("— Aula 3: Retas e planos…"). Quando a mesma unidade aparece de novo, os itens só entram se ela
ainda não tem tópicos (a primeira descrição vale; o cronograma não duplica o conteúdo programático).
"""

import re
from dataclasses import dataclass, field

from estudos.importacao.idioma import numero_de_unidade

_MARCADORES = "○◦▪•‣–—-"
# "1ª unidade. Vetores no plano…" → título "1ª unidade" e o resto é o conteúdo em frases
_UNIDADE_EM_FRASES = re.compile(r"^(?P<cab>\S+\s+unidade|unidade\s+\S+?)\s*\.\s+(?P<resto>\S.*)$", re.I)
_FIM_DE_FRASE = re.compile(r"\.\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9])")
_AULA = re.compile(r"^aula\s+\d+\s*:\s*", re.I)
_ATIVIDADE = re.compile(r"^aula de atividade\b", re.I)
_PARENTESES_FINAL = re.compile(r"\s*\([^()]*\)\s*\.?$")


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


def _frases(texto: str) -> list[str]:
    return [f.strip().rstrip(".").strip() for f in _FIM_DE_FRASE.split(texto) if f.strip().rstrip(".").strip()]


def _titulo_do_item(texto: str) -> str | None:
    """Item de cronograma de aulas: tira "Aula N:", a observação entre parênteses e fica com a primeira frase;
    aula só de atividade não é tópico."""
    if _ATIVIDADE.match(texto):
        return None
    if _AULA.match(texto):
        texto = _PARENTESES_FINAL.sub("", _AULA.sub("", texto))
        frases = _frases(texto)
        return frases[0] if frases else None
    return texto


def extrair_programa(texto: str) -> list[UnidadeExtraida]:
    unidades: list[UnidadeExtraida] = []
    ordem_marcadores: list[str] = []
    marcador_pendente: str | None = None   # marcador sozinho na linha: o item é a próxima linha
    ultimo: TopicoExtraido | None = None
    paragrafo: list[str] | None = None      # conteúdo em frases da unidade atual, até a próxima linha em branco
    ignorando = False                       # unidade repetida que já tem tópicos: os itens desta vez não entram
    atual: UnidadeExtraida | None = None

    def fechar_paragrafo() -> None:
        nonlocal paragrafo
        if paragrafo and atual is not None:
            atual.topicos.extend(TopicoExtraido(f) for f in _frases(" ".join(paragrafo)))
        paragrafo = None

    for bruta in texto.split("\n"):
        linha = bruta.strip()
        if not linha:
            fechar_paragrafo()
            continue
        em_frases = _UNIDADE_EM_FRASES.match(linha)
        numero = numero_de_unidade(em_frases.group("cab") if em_frases else linha)
        if numero is not None:
            fechar_paragrafo()
            marcador_pendente, ultimo = None, None
            atual = next((u for u in unidades if u.numero == numero), None)
            if atual is None:
                atual = UnidadeExtraida(numero, em_frases.group("cab") if em_frases else linha)
                unidades.append(atual)
            ignorando = bool(atual.topicos)
            if em_frases and not ignorando:
                paragrafo = [em_frases.group("resto")]
            continue
        if atual is None:
            continue  # cabeçalho do documento
        marcador = linha[0] if linha[0] in _MARCADORES else None
        if paragrafo is not None and marcador is None:
            paragrafo.append(linha)
            continue
        fechar_paragrafo()
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
        if ignorando:
            continue
        titulo = _titulo_do_item(resto)
        if titulo is None:
            ultimo = None
            continue
        if marcador not in ordem_marcadores:
            ordem_marcadores.append(marcador)
        nivel = min(ordem_marcadores.index(marcador) + 1, 2)
        ultimo = TopicoExtraido(titulo)
        if nivel == 2 and atual.topicos:
            atual.topicos[-1].filhos.append(ultimo)
        else:
            atual.topicos.append(ultimo)
    fechar_paragrafo()
    return unidades
