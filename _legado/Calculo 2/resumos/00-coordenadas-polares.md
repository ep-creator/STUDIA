# Coordenadas polares

> Stewart 10.3 e 10.4 · pré-requisito da 1ª unidade

Está no programa da 1ª unidade e é a ferramenta que salva metade dos limites de duas variáveis. Vale a hora gasta.

## 1. Definição

Um ponto do plano é localizado por `(r, θ)`: `r` = distância orientada até o polo (origem), `θ` = ângulo do eixo polar (semi-eixo x positivo) até o segmento, positivo no sentido anti-horário.

**Conversão polar → cartesiana** (sempre vale):

```
x = r cos θ        y = r sen θ
```

**Conversão cartesiana → polar:**

```
r² = x² + y²       tg θ = y/x   (x ≠ 0)
```

> **Cuidado (erro de prova):** `tg θ = y/x` não determina θ sozinho — a tangente tem período π. É preciso olhar em que **quadrante** está `(x, y)` e escolher θ de acordo. Ex.: `(1, 1)` e `(−1, −1)` têm a mesma razão `y/x = 1`, mas `θ = π/4` e `θ = 5π/4`.

## 2. Não-unicidade

`(r, θ)`, `(r, θ + 2kπ)` e `(−r, θ + π)` representam **o mesmo ponto**. A origem é `(0, θ)` para qualquer θ. Por isso questões do tipo "dê três outras representações" são comuns.

## 3. Curvas polares que caem

| Equação | Curva |
|---|---|
| `r = a` | circunferência de raio \|a\| centrada na origem |
| `θ = θ₀` | reta pela origem |
| `r = 2a cos θ` | circunferência de raio \|a\| centrada em `(a, 0)` |
| `r = 2a sen θ` | circunferência de raio \|a\| centrada em `(0, a)` |
| `r = a(1 ± cos θ)`, `r = a(1 ± sen θ)` | cardioide |
| `r = a ± b cos θ` com `a < b` | limaçon com laço interno |
| `r = a cos(nθ)`, `r = a sen(nθ)` | rosácea: **n pétalas se n é ímpar, 2n pétalas se n é par** |
| `r² = a² cos(2θ)` | lemniscata |

**Simetrias** (economizam metade do esboço):
- troca `θ → −θ` deixa a equação igual ⇒ simétrica em relação ao **eixo polar** (eixo x);
- troca `θ → π − θ` ⇒ simétrica em relação ao **eixo θ = π/2** (eixo y);
- troca `r → −r` (ou `θ → θ + π`) ⇒ simétrica em relação ao **polo**.

## 4. Área e comprimento (10.4)

```
A = ∫[α→β] ½ r(θ)² dθ

L = ∫[α→β] √( r² + (dr/dθ)² ) dθ
```

Área entre duas curvas: `A = ∫ ½ (r_ext² − r_int²) dθ`, achando os limites pelas **interseções** — e lembrando de checar se a origem é interseção "invisível" (as curvas passam pelo polo com valores diferentes de θ).

## 5. Por que isso importa em Cálculo 2

Três usos, em ordem de importância para esta unidade:

1. **Limites em (0,0)** — substituindo `x = r cos θ`, `y = r sen θ`, o limite `(x,y) → (0,0)` vira `r → 0⁺`. Se a expressão resultante for limitada por algo que tende a 0 **independentemente de θ**, o limite existe e vale isso. (Ver `resumos/02-limites-continuidade.md`.)
2. **Curvas de nível** de funções com simetria radial (`f` que só depende de `x² + y²`) ficam triviais.
3. **Integrais duplas** — 2ª e 3ª unidades.

## Exercícios sugeridos (S0, ~1 h)

Stewart 10.3 (livro p. 592 · PDF p. 103): **1, 3, 5, 15, 17, 29, 31**.
