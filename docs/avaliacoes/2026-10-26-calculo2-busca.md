# Avaliação da busca — Calculo 2

Gabarito: `calculo2_busca.toml` (40 perguntas)

| configuração | acerto@5 | exata | paráfrase | MRR@10 | indexação (s) | busca p50 (ms) | busca p95 (ms) | memória (MB) |
|---|---|---|---|---|---|---|---|---|
| texto | 80% | 95% | 65% | 0.61 | 32.31 | 4.0 | 9.0 | 79.9 |
| vetor:small | 75% | 90% | 60% | 0.61 | 309.77 | 55.0 | 73.4 | 79.8 |
| hibrida:small | 85% | 95% | 75% | 0.71 | 309.77 | 71.4 | 91.5 | 0.6 |
| vetor:base | 82% | 95% | 70% | 0.69 | 915.94 | 50.6 | 68.3 | 79.8 |
| hibrida:base | 88% | 95% | 80% | 0.75 | 915.94 | 68.0 | 89.5 | 0.6 |

## Decisão pelas regras da spec (§4.4), fixadas antes dos números

Linha de base (`texto`): acerto@5 em paráfrase 65%, nas exatas 95%.

| regra | hibrida:small | hibrida:base |
|---|---|---|
| paráfrase sobe ≥ 10 pontos | ✅ 65% → 75% (+10) | ✅ 65% → 80% (+15) |
| exatas não caem mais de 2 pontos | ✅ 95% → 95% | ✅ 95% → 95% |
| busca p95 < 300 ms | ✅ 91,5 ms | ✅ 89,5 ms |
| indexação < 10 min | ✅ 5,2 min | ❌ 15,3 min |

- **hibrida:small passa em todas** → candidata a padrão (`embeddings = true`, `busca = "hibrida"`, modelo small).
- **base no lugar do small** exigiria ≥ 5 pontos a mais de acerto@5 geral: 88% × 85% = +3 ❌ (e ainda reprova no tempo de indexação).
- `vetor` sozinho fica abaixo do texto com o small (75% × 80%): só entra fundido.
- Observação: a coluna de memória das configurações que reaproveitam o índice (0,6 MB) mede só as buscas; o pico com indexação é ~80 MB.
