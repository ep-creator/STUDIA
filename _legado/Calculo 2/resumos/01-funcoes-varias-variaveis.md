# 14.1 Funções de várias variáveis

> Funções de várias variáveis reais a valores reais · Stewart 14.1 · Guidorizzi cap. 8

## 1. Definição

Uma **função de duas variáveis reais a valores reais** é uma função `f : A → ℝ` com `A ⊂ ℝ²`, que associa a cada par `(x, y) ∈ A` um único número `f(x, y) ∈ ℝ`.

- **Domínio** `D_f = A`. Quando não é especificado, convenciona-se o **maior** subconjunto de ℝ² para o qual a regra faz sentido.
- **Imagem** `Im f = { f(x,y) : (x,y) ∈ D_f } ⊂ ℝ`.
- **Gráfico**: `G_f = { (x, y, z) ∈ ℝ³ : z = f(x,y), (x,y) ∈ D_f }` — uma **superfície** em ℝ³.

Para três variáveis, tudo se repete com `A ⊂ ℝ³`; o gráfico viveria em ℝ⁴ e por isso não se desenha.

## 2. Determinar o domínio — receita

O domínio é a interseção das restrições impostas por cada operação:

| Operação | Restrição |
|---|---|
| `√(g)` (raiz de índice par) | `g ≥ 0` |
| `1/g` | `g ≠ 0` |
| `ln(g)` | `g > 0` |
| `arcsen(g)`, `arccos(g)` | `−1 ≤ g ≤ 1` |
| `tg(g)` | `g ≠ π/2 + kπ` |

**Depois de achar as inequações, desenhe.** A resposta esperada na prova é (i) o conjunto em notação de conjunto e (ii) o esboço hachurado, indicando se a fronteira entra (linha cheia) ou não (tracejada).

## 3. Curvas de nível

> **Definição.** Sejam `z = f(x,y)` e `c ∈ Im f`. A **curva de nível de f correspondente ao nível c** é o conjunto `{ (x,y) ∈ D_f : f(x,y) = c }`.

Três fatos que caem:

1. A curva de nível é subconjunto do **domínio** (mora em ℝ²), o gráfico mora em ℝ³. Não confunda.
2. A curva de nível de nível `c` é a **projeção no plano xy** da interseção do gráfico com o plano horizontal `z = c`.
3. **Duas curvas de nível distintas nunca se cruzam** — se `(x₀,y₀)` estivesse em ambas, `f(x₀,y₀)` teria dois valores. (Guidorizzi 8.3 ex. 3 pergunta o análogo para superfícies de nível: mesma resposta, mesmo argumento.)

**Receita de esboço:** escolha `c = ..., −2, −1, 0, 1, 2, ...`, escreva `f(x,y) = c`, identifique a cônica/curva resultante, e **anote o valor de c em cada curva**. Curvas muito juntas ⇒ superfície íngreme.

Padrões que se repetem:

| `f(x,y)` | Curvas de nível | Superfície |
|---|---|---|
| `ax + by + c` | retas paralelas | plano |
| `x² + y²` | circunferências concêntricas | paraboloide circular |
| `√(x² + y²)` | circunferências concêntricas (**espaçamento uniforme**) | cone |
| `x² − y²` | hipérboles + o par de retas `y = ±x` (nível 0) | paraboloide hiperbólico (sela) |
| `y − x²` | parábolas transladadas | cilindro parabólico deformado |
| `e^{−(x²+y²)}` | circunferências | "sino" |

## 4. Superfícies de nível (três variáveis)

Para `w = f(x,y,z)`, a **superfície de nível** de nível `c` é `{ (x,y,z) : f(x,y,z) = c }` — um subconjunto de ℝ³. É a única forma prática de "ver" uma função de três variáveis.

Exemplo do tipo do exercício 68 do Stewart: `f(x,y,z) = x² − y² − z²`.
- `c > 0`: hiperboloide de **duas** folhas ao longo do eixo x;
- `c = 0`: cone `x² = y² + z²`;
- `c < 0`: hiperboloide de **uma** folha em torno do eixo x.

## 5. Superfícies quádricas — tabela de reconhecimento

Com a equação na forma reduzida, o padrão de sinais decide:

| Equação | Superfície |
|---|---|
| `x²/a² + y²/b² + z²/c² = 1` | elipsoide |
| `z = x²/a² + y²/b²` | paraboloide elíptico |
| `z = x²/a² − y²/b²` | paraboloide hiperbólico (sela) |
| `x²/a² + y²/b² − z²/c² = 1` | hiperboloide de uma folha |
| `x²/a² + y²/b² − z²/c² = −1` | hiperboloide de duas folhas |
| `z² = x²/a² + y²/b²` | cone |
| falta uma variável | cilindro (gera-se transladando a curva ao longo do eixo ausente) |

**Método dos traços:** corte com `x = k`, `y = k`, `z = k` e identifique as curvas planas. É o que o Stewart pede em "esboce o gráfico" e é o que dá pontos na prova.

## 6. Operações e classes especiais (Guidorizzi)

- **Função polinomial**: soma finita de `a_{mn} xᵐ yⁿ`. Domínio ℝ².
- **Função racional**: `p/q` com p, q polinomiais. Domínio `{ q ≠ 0 }`.
- **Função afim**: `ax + by + c`; **linear** se `c = 0`. Gráfico é um plano de vetor normal `(a, b, −1)`.
- **Função homogênea de grau λ**: `f(tx, ty) = t^λ f(x,y)` para todo `t > 0`. Truque de prova: para `(x,y) ≠ (0,0)`, escreva `(x,y) = r·(cos α, sen α)` com `r = ‖(x,y)‖`; então `f(x,y) = r^λ f(cos α, sen α)` — a função fica determinada pelos valores no círculo unitário. É exatamente o que os exercícios 6, 7 e 8 da seção 8.1 exploram.

## 7. Erros que custam ponto

1. Dar o domínio sem desenhar, ou desenhar sem dizer se a fronteira pertence.
2. Chamar de "curva de nível" a curva desenhada em ℝ³ sobre a superfície. A curva de nível está no plano xy.
3. Esquecer `Im f` quando o enunciado pede — em `f(x,y) = √(x²+y²)`, a imagem é `[0, +∞)`, não ℝ.
4. Esboçar curvas de nível sem rotular os níveis.
