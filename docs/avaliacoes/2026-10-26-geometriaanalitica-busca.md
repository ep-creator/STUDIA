# Avaliação da busca — Geometria Analítica

Gabarito: `geometriaanalitica_busca.toml` (36 perguntas)

| configuração | acerto@5 | exata | paráfrase | MRR@10 | indexação (s) | busca p50 (ms) | busca p95 (ms) | memória (MB) |
|---|---|---|---|---|---|---|---|---|
| texto | 86% | 100% | 69% | 0.79 | 4.11 | 2.6 | 4.9 | 16.1 |
| vetor:small | 86% | 100% | 69% | 0.75 | 98.13 | 20.3 | 27.0 | 16.0 |
| hibrida:small | 89% | 100% | 75% | 0.80 | 98.13 | 34.5 | 49.3 | 0.4 |
| vetor:base | 92% | 100% | 81% | 0.84 | 324.53 | 34.7 | 42.0 | 16.0 |
| hibrida:base | 92% | 100% | 81% | 0.85 | 324.53 | 48.0 | 61.9 | 0.5 |


---

## Versão 2 do gabarito (uso real: questões, slides/listas, trecho e links)


Gabarito: `geometriaanalitica_busca.toml` (44 perguntas)

| configuração | acerto@5 | exata | parafrase | questao | de claude | trecho | links | MRR@10 | indexação (s) | busca p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| texto | 68% | 100% | 20% | 70% | 68% | 75% (n=8) | 29% (n=12) | 0.46 | 3.87 | 9.0 |
| vetor:small | 68% | 100% | 50% | 55% | 68% | 62% (n=8) | 33% (n=12) | 0.50 | 121.08 | 55.9 |
| hibrida:small | 70% | 100% | 30% | 70% | 70% | 75% (n=8) | 42% (n=12) | 0.51 | 121.08 | 99.8 |
| vetor:base | 64% | 93% | 10% | 70% | 64% | 38% (n=8) | 21% (n=12) | 0.51 | 301.22 | 97.4 |
| hibrida:base | 68% | 93% | 20% | 75% | 68% | 50% (n=8) | 29% (n=12) | 0.48 | 301.22 | 104.7 |


---

## Versão 3: perguntas de questão sem a página da própria questão

Um resultado que contém o enunciado (a página da lista ou dos exercícios do livro) não conta: só vale a explicação.

| configuração | acerto@5 | exata | parafrase | questao | de claude | trecho | links | MRR@10 | indexação (s) | busca p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| texto | 70% | 100% | 20% | 75% | 70% | 75% (n=8) | 29% (n=12) | 0.51 | 4.2 | 20.8 |
| vetor:small | 66% | 100% | 50% | 50% | 66% | 62% (n=8) | 33% (n=12) | 0.51 | 120.75 | 61.9 |
| hibrida:small | 70% | 100% | 30% | 70% | 70% | 75% (n=8) | 42% (n=12) | 0.57 | 120.75 | 98.1 |
| vetor:base | 61% | 93% | 10% | 65% | 61% | 38% (n=8) | 21% (n=12) | 0.55 | 367.67 | 89.6 |
| hibrida:base | 68% | 93% | 20% | 75% | 68% | 50% (n=8) | 29% (n=12) | 0.55 | 367.67 | 158.0 |

## B2 · passo 1: teoria separada dos exercícios (2026-10-26)

Índice com os livros cortados em teoria, exercícios e respostas; a busca e a avaliação olham só a teoria. Mesmo
gabarito da versão 3 (44 perguntas), modo texto.

| limite da teoria | acerto@5 | acerto@20 | exata | parafrase | questao | trecho | links | MRR@10 |
|---|---|---|---|---|---|---|---|---|
| base (versão 3) | 70% | — | 100% | 20% | 75% | 75% (n=8) | 29% (n=12) | 0.51 |
| 800 | 68% | 84% | 93% | 10% | 80% | 50% (n=8) | 25% (n=12) | 0.49 |
| **1.200 (escolhido)** | 68% | 84% | 93% | 10% | **80%** | 62% (n=8) | **33%** (n=12) | 0.49 |
| 1.600 | 70% | 86% | 100% | 10% | 80% | 62% (n=8) | 33% (n=12) | 0.52 |

O que caiu: o acerto geral (70 → 68%, uma pergunta) e a página exata (75 → 62%, uma de 8) — trechos menores
espalham uma explicação por mais de um trecho. Questão (o uso principal) sobe de 75 para 80% e os links de 29 para 33%.
