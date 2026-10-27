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


---

## Versão 2 do gabarito (uso real: questões, slides/listas, trecho e links)


Gabarito: `calculo2_busca.toml` (161 perguntas)

| configuração | acerto@5 | exata | parafrase | questao | de claude | de gerada | trecho | links | MRR@10 | indexação (s) | busca p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| texto | 91% | 100% | 65% | 94% | 82% | 94% | — | 56% (n=12) | 0.81 | 27.89 | 13.0 |
| vetor:small | 63% | 95% | 70% | 57% | 82% | 57% | — | 55% (n=12) | 0.47 | 248.49 | 71.0 |
| hibrida:small | 84% | 100% | 75% | 83% | 88% | 83% | — | 68% (n=12) | 0.68 | 248.49 | 97.6 |
| vetor:base | 78% | 100% | 75% | 75% | 88% | 75% | — | 60% (n=12) | 0.59 | 863.24 | 66.9 |
| hibrida:base | 89% | 100% | 80% | 89% | 90% | 89% | — | 68% (n=12) | 0.75 | 863.24 | 84.3 |


---

## Versão 3: perguntas de questão sem a página da própria questão

Um resultado que contém o enunciado (a página da lista ou dos exercícios do livro) não conta: só vale a explicação.

| configuração | acerto@5 | exata | parafrase | questao | de claude | de gerada | trecho | links | MRR@10 | indexação (s) | busca p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| texto | 78% | 100% | 65% | 77% | 82% | 77% | — | 56% (n=12) | 0.61 | 28.17 | 21.7 |
| vetor:small | 56% | 95% | 70% | 47% | 82% | 47% | — | 55% (n=12) | 0.41 | 336.09 | 109.0 |
| hibrida:small | 73% | 100% | 75% | 69% | 88% | 69% | — | 68% (n=12) | 0.55 | 336.09 | 111.8 |
| vetor:base | 71% | 100% | 75% | 65% | 88% | 65% | — | 60% (n=12) | 0.52 | 881.41 | 118.2 |
| hibrida:base | 80% | 100% | 80% | 76% | 90% | 76% | — | 68% (n=12) | 0.65 | 881.41 | 288.2 |

## B2 · passo 1: teoria separada dos exercícios (2026-10-26)

Índice com o livro cortado em teoria, exercícios e respostas; a busca e a avaliação olham só a teoria (os exercícios
do livro aparecem num grupo à parte). Mesmo gabarito da versão 3, com `--geradas` (161 perguntas), modo texto.
"acerto@20" mostra se o erro é de ordem (resposta certa entre os 20 primeiros) ou de recuperação.

| limite da teoria | acerto@5 | acerto@20 | exata | parafrase | questao | de claude | de gerada | links | MRR@10 |
|---|---|---|---|---|---|---|---|---|---|
| base (versão 3) | 78% | — | 100% | 65% | 77% | 82% | 77% | 56% (n=12) | 0.61 |
| 800 | 78% | 93% | 100% | 65% | 77% | 82% | 77% | 64% (n=12) | 0.65 |
| **1.200 (escolhido)** | **80%** | **91%** | 100% | 70% | **78%** | 85% | 78% | 56% (n=12) | 0.62 |
| 1.600 | 76% | 92% | 100% | 60% | 75% | 80% | 75% | 56% (n=12) | 0.60 |

Decisão: 1.200 caracteres — maior acerto de questão somado nas duas matérias, sem piorar os links.

## B2 · passo 2: leitura limpa dos PDFs (2026-10-27)

Mesmo gabarito e configuração do passo 1 (limite 1.200), índice com a leitura por fonte e posição.

| configuração | acerto@5 | acerto@20 | exata | parafrase | questao | de claude | de gerada | links | MRR@10 | indexação (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| passo 1 | 80% | 91% | 100% | 70% | 78% | 85% | 78% | 56% (n=12) | 0.62 | 29 |
| passo 2 | 78% | 93% | 100% | 65% | 77% | 82% | 77% | 56% (n=12) | 0.58 | 90–250 |

Decisão e motivo: spec da peça B2, §9.
