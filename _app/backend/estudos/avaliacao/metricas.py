"""Métricas sobre a posição (1-based) da primeira resposta aceita em cada pergunta; None = não apareceu."""


def acerto_em(posicoes: list[int | None], k: int) -> float:
    if not posicoes:
        return 0.0
    return sum(1 for p in posicoes if p is not None and p <= k) / len(posicoes)


def mrr(posicoes: list[int | None], k: int = 10) -> float:
    if not posicoes:
        return 0.0
    return sum(1 / p for p in posicoes if p is not None and p <= k) / len(posicoes)
