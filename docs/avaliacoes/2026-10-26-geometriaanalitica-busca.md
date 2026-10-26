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
