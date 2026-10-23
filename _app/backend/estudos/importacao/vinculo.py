"""Vínculos por similaridade de texto: tópico do programa ↔ seção do livro ↔ conteúdo de lista.

Similaridade = Jaccard ponderado pelo IDF dos tokens (palavras raras pesam mais que "integral" ou "função").
"""

import math
from collections import Counter
from dataclasses import dataclass

from estudos.importacao.idioma import radicais_relevantes


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
    documentos = [set(radicais_relevantes(t)) for t in titulos]
    frequencia = Counter(token for tokens in documentos for token in tokens)
    total = max(1, len(documentos))
    return {token: math.log(1 + total / df) for token, df in frequencia.items()}


def similaridade(a: str, b: str, idf: dict[str, float]) -> float:
    ta, tb = set(radicais_relevantes(a)), set(radicais_relevantes(b))
    if not ta or not tb:
        return 0.0
    padrao = max(idf.values(), default=1.0)  # token desconhecido conta como raro

    def peso(tokens: set[str]) -> float:
        return sum(idf.get(t, padrao) for t in tokens)

    return peso(ta & tb) / peso(ta | tb)


def _profundidade(c: Candidato) -> int:
    """Nível do código da seção na chave ('14.3' → 1); chaves sem código contam 0."""
    codigo = c.chave[-1] if isinstance(c.chave, tuple) else c.chave
    return codigo.count(".") if isinstance(codigo, str) else 0


def pontuar(
    texto: str, candidatos: list[Candidato], limiar: float, idf: dict[str, float] | None = None
) -> list[tuple[float, Candidato]]:
    """Candidatos com similaridade ≥ limiar, do mais parecido para o menos. Quem compara muitos textos com os mesmos
    candidatos passa o `idf` pronto (construir_idf dos títulos) para não recalculá-lo a cada chamada."""
    if idf is None:
        idf = construir_idf([c.titulo for c in candidatos])
    # Empate de nota: fica a mais específica (seção 14.3 antes do capítulo 14 de mesmo título)
    pontuados = sorted(
        ((similaridade(texto, c.titulo, idf), c) for c in candidatos),
        key=lambda par: (par[0], _profundidade(par[1])), reverse=True,
    )
    return [(s, c) for s, c in pontuados if s >= limiar]


def melhores(
    texto: str, candidatos: list[Candidato], limiar: float, maximo: int = 1, idf: dict[str, float] | None = None
) -> list[Vinculo]:
    pontuados = pontuar(texto, candidatos, limiar, idf)
    vinculos = []
    for i, (score, c) in enumerate(pontuados[:maximo]):
        # Escolha única entre candidatos igualmente parecidos é um chute: a confiança cai pela metade
        empate = (maximo == 1 and i == 0 and len(pontuados) > 1 and math.isclose(pontuados[1][0], score)
                  and _profundidade(pontuados[1][1]) == _profundidade(c))
        vinculos.append(Vinculo(c.chave, c.titulo, round(score / 2 if empate else score, 4)))
    return vinculos


def unidade_majoritaria(votos: list[tuple[int, float]]) -> tuple[int | None, float]:
    """Votos (unidade, força do vínculo). Confiança = fatia da unidade vencedora × seu vínculo mais forte: um único
    vínculo fraco não vira certeza, e votos divididos entre unidades também baixam a confiança."""
    pesos: dict[int, float] = {}
    for unidade, forca in votos:
        pesos[unidade] = pesos.get(unidade, 0.0) + forca
    total = sum(pesos.values())
    if not total:
        return None, 0.0
    unidade = max(pesos, key=pesos.get)
    maior = max(forca for u, forca in votos if u == unidade)
    return unidade, pesos[unidade] / total * maior
