"""Vínculos por similaridade de texto: tópico do programa ↔ seção do livro ↔ conteúdo de lista.

Similaridade = Jaccard ponderado pelo IDF dos tokens (palavras raras pesam mais que "integral" ou "função").
"""

import math
from collections import Counter
from dataclasses import dataclass

from estudos.importacao.idioma import tokens_relevantes


@dataclass(frozen=True)
class Candidato:
    chave: object
    titulo: str


@dataclass(frozen=True)
class Vinculo:
    chave: object
    titulo: str
    confianca: float


def construir_idf(titulos: list[str]) -> dict[str, float]:
    documentos = [set(tokens_relevantes(t)) for t in titulos]
    frequencia = Counter(token for tokens in documentos for token in tokens)
    total = max(1, len(documentos))
    return {token: math.log(1 + total / df) for token, df in frequencia.items()}


def similaridade(a: str, b: str, idf: dict[str, float]) -> float:
    ta, tb = set(tokens_relevantes(a)), set(tokens_relevantes(b))
    if not ta or not tb:
        return 0.0
    padrao = max(idf.values(), default=1.0)  # token desconhecido conta como raro

    def peso(tokens: set[str]) -> float:
        return sum(idf.get(t, padrao) for t in tokens)

    return peso(ta & tb) / peso(ta | tb)


def melhores(texto: str, candidatos: list[Candidato], limiar: float, maximo: int = 1) -> list[Vinculo]:
    idf = construir_idf([c.titulo for c in candidatos])
    pontuados = sorted(
        ((similaridade(texto, c.titulo, idf), c) for c in candidatos), key=lambda par: par[0], reverse=True
    )
    pontuados = [(s, c) for s, c in pontuados if s >= limiar]
    vinculos = []
    for i, (score, c) in enumerate(pontuados[:maximo]):
        empate = i == 0 and len(pontuados) > 1 and math.isclose(pontuados[1][0], score)
        vinculos.append(Vinculo(c.chave, c.titulo, round(score / 2 if empate else score, 4)))
    return vinculos


def unidade_majoritaria(unidades: list[int]) -> tuple[int | None, float]:
    if not unidades:
        return None, 0.0
    unidade, votos = Counter(unidades).most_common(1)[0]
    return unidade, votos / len(unidades)
