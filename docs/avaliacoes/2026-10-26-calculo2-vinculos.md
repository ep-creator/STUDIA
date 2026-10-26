# Avaliação dos vínculos — Calculo 2

Gabarito: `calculo2_vinculos.toml` (58 itens)

| configuração | ligação | acertos | erros confiantes | para revisão |
|---|---|---|---|---|
| regra | topicos | 16/19 (84%) | 0 | 7 |
| regra | listas | 17/20 (85%) | 0 | 11 |
| regra | documentos | 19/19 (100%) | 0 | 1 |
| regra | total | 52/58 (90%) | 0 | 19 |
| sentido:small@0.3 | topicos | 17/19 (89%) | 0 | 8 |
| sentido:small@0.3 | listas | 18/20 (90%) | 0 | 12 |
| sentido:small@0.3 | documentos | 16/19 (84%) | 0 | 3 |
| sentido:small@0.3 | total | 51/58 (88%) | 0 | 23 |
| sentido:small@0.5 | topicos | 15/19 (79%) | 0 | 8 |
| sentido:small@0.5 | listas | 19/20 (95%) | 0 | 13 |
| sentido:small@0.5 | documentos | 16/19 (84%) | 0 | 3 |
| sentido:small@0.5 | total | 50/58 (86%) | 0 | 24 |
| sentido:small@0.7 | topicos | 15/19 (79%) | 0 | 5 |
| sentido:small@0.7 | listas | 19/20 (95%) | 0 | 3 |
| sentido:small@0.7 | documentos | 16/19 (84%) | 0 | 3 |
| sentido:small@0.7 | total | 50/58 (86%) | 0 | 11 |
| sentido:base@0.3 | topicos | 17/19 (89%) | 0 | 9 |
| sentido:base@0.3 | listas | 18/20 (90%) | 0 | 13 |
| sentido:base@0.3 | documentos | 16/19 (84%) | 0 | 3 |
| sentido:base@0.3 | total | 51/58 (88%) | 0 | 25 |
| sentido:base@0.5 | topicos | 15/19 (79%) | 0 | 9 |
| sentido:base@0.5 | listas | 18/20 (90%) | 0 | 13 |
| sentido:base@0.5 | documentos | 16/19 (84%) | 0 | 3 |
| sentido:base@0.5 | total | 49/58 (84%) | 0 | 25 |
| sentido:base@0.7 | topicos | 15/19 (79%) | 0 | 5 |
| sentido:base@0.7 | listas | 18/20 (90%) | 0 | 3 |
| sentido:base@0.7 | documentos | 16/19 (84%) | 0 | 3 |
| sentido:base@0.7 | total | 49/58 (84%) | 0 | 11 |

## Decisão pelas regras da spec (§4.4), fixadas antes dos números

Regra para os embeddings entrarem nos vínculos: **aumentar os acertos** sem **nenhum** erro confiante novo.

- Nenhuma configuração aumenta os acertos (melhor: 51/58 contra 52/58 da regra) → **os vínculos continuam só por regra**
  (`vinculos_com_embeddings = false`); limiares sem recalibração.
- Por tipo, o sentido ajuda nas listas (85% → 95%) e atrapalha nos documentos (100% → 84%): o e5 dá cosseno alto para
  quase qualquer par de textos de matemática, e `(1 + cos) / 2` puxa planos e títulos genéricos para alguma seção.
- Achado para depois (não aplicado, para não ajustar a regra ao resultado): normalizar a escala do sentido pela
  distribuição dos cossenos do modelo, ou usar o sentido só nas listas, e medir de novo com o mesmo gabarito.
