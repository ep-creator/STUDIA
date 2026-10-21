---
tipo: resumo
titulo: 14.2 Limite e continuidade
unidade: 1
secao: null
questao: null
origem: migrado
---
# 14.2 Limite e continuidade

> Stewart 14.2 · Guidorizzi cap. 9

## 1. Definição (ε–δ)

> Sejam `f : A ⊂ ℝ² → ℝ`, `(x₀,y₀)` ponto de acumulação de `A` e `L ∈ ℝ`. Diz-se que
> ```
> lim f(x,y) = L        quando (x,y) → (x₀,y₀)
> ```
> se, **para todo ε > 0, existe δ > 0** tal que, para todo `(x,y) ∈ D_f`,
> ```
> 0 < ‖(x,y) − (x₀,y₀)‖ < δ   ⟹   |f(x,y) − L| < ε.
> ```

Em palavras: `f(x,y)` fica em `]L−ε, L+ε[` sempre que `(x,y)`, diferente de `(x₀,y₀)`, está na **bola aberta** de centro `(x₀,y₀)` e raio δ.

**A diferença crucial em relação a uma variável:** em ℝ há dois lados; em ℝ² há **infinitos caminhos** de aproximação. O limite só existe se todos derem o mesmo valor — e "todos" inclui caminhos curvos.

## 2. Como PROVAR que o limite NÃO existe

Este é o lado fácil e é o que mais cai.

> **Teorema (critério dos caminhos).** Se `γ₁` e `γ₂` são curvas contínuas com `γᵢ(t₀) = (x₀,y₀)` e `γᵢ(t) ≠ (x₀,y₀)` para `t ≠ t₀`, e se
> `lim_{t→t₀} f(γ₁(t)) ≠ lim_{t→t₀} f(γ₂(t))`,
> então `lim_{(x,y)→(x₀,y₀)} f(x,y)` **não existe**.
> (O limite também não existe se um dos dois limites em t não existir.)

**Arsenal de caminhos, na ordem em que se tenta:**

| Caminho | Substituição | Serve para |
|---|---|---|
| eixo x | `y = 0` | quase sempre o primeiro teste |
| eixo y | `x = 0` | idem |
| retas | `y = mx` | se o resultado **depende de m**, acabou: não existe |
| parábolas | `y = mx²` | quando as retas todas dão o mesmo valor mas o grau sugere |
| curva ad hoc | `y = x³`, `y = x^{3/2}`, … | casos como `x³y/(x⁶+y²)` |

> **Erro clássico:** concluir que o limite **existe** porque todas as retas deram o mesmo valor. Isso não prova nada. `f(x,y) = x²y/(x⁴+y²)` vale 0 em toda reta pela origem e vale 1/2 sobre `y = x²`.

## 3. Como PROVAR que o limite EXISTE

Três ferramentas, nesta ordem de preferência:

### (a) Teorema do confronto / produto de limitada por infinitésimo

Se `|f(x,y) − L| ≤ g(x,y)` e `g(x,y) → 0`, então `f(x,y) → L`.

Desigualdades que resolvem quase tudo:

```
|x| ≤ √(x² + y²)        |y| ≤ √(x² + y²)
|xy| ≤ ½ (x² + y²)      x² ≤ x² + y²      y² ≤ x² + y²
```

Exemplo modelo (`x³/(x²+y²) → 0`):
```
| x³/(x²+y²) − 0 | = |x| · x²/(x²+y²) ≤ |x| · 1 = |x| → 0.
```
Escreva assim na prova: identifique o fator limitado, o fator que tende a zero, cite o teorema.

### (b) Coordenadas polares (só para `(x,y) → (0,0)`)

Ponha `x = r cos θ`, `y = r sen θ`; então `(x,y) → (0,0)` ⟺ `r → 0⁺`.

> **Condição para valer:** só se pode concluir `lim = L` se `|f(r cos θ, r sen θ) − L| ≤ h(r)` com `h(r) → 0` e **h independente de θ**. Se o resultado depende de θ, o limite não existe.

### (c) Definição ε–δ

Quando o enunciado pede explicitamente. Estrutura: partindo de `|f − L|`, majore por uma expressão em `‖(x,y) − (x₀,y₀)‖`; daí saia com δ em função de ε.

## 4. Propriedades operacionais

Se `lim f = L₁` e `lim g = L₂` em `(x₀,y₀)`, então valem soma, múltiplo escalar, produto, e quociente com `L₂ ≠ 0`. Também:

- `lim f = L  ⟺  lim (f − L) = 0`;
- `lim_{(x,y)→(x₀,y₀)} f(x,y) = lim_{(h,k)→(0,0)} f(x₀+h, y₀+k)` — **translada para a origem**, muito útil;
- **Conservação do sinal:** se `lim f = L > 0`, existe δ > 0 com `f(x,y) > 0` na bola furada de raio δ.

## 5. Continuidade

> **Definição.** `f` é **contínua em `(x₀,y₀) ∈ D_f`** se `lim_{(x,y)→(x₀,y₀)} f(x,y) = f(x₀,y₀)`.
> `f` é contínua em `A` se for contínua em todo ponto de A.

Três coisas precisam valer ao mesmo tempo: `f(x₀,y₀)` existe, o limite existe, e os dois coincidem.

**Teoremas que dispensam contas:**

- Polinômios são contínuos em ℝ². Funções racionais são contínuas em todo o seu domínio.
- Soma, produto, múltiplo e quociente (denominador não nulo) de contínuas são contínuas.
- **Composição:** se `f : A ⊂ ℝ² → ℝ` é contínua em `(x₀,y₀)` e `g : B ⊂ ℝ → ℝ` é contínua em `f(x₀,y₀)`, então `h = g ∘ f` é contínua em `(x₀,y₀)`. É o que resolve os exercícios "determine `h = g(f(x,y))` e o conjunto onde h é contínua".

**Estratégia padrão para "determine o conjunto dos pontos de continuidade":**

1. Fora do ponto suspeito (geralmente a origem), invoque os teoremas: quociente de contínuas com denominador não nulo ⇒ contínua. **Uma linha.**
2. No ponto suspeito, calcule o limite. Se existir e for igual ao valor, contínua; senão, não.

## 6. Erros que custam ponto

1. Testar dois caminhos, obter o mesmo valor e escrever "logo o limite existe e vale L". **Não prova.**
2. Usar polares e concluir sem verificar que a majoração independe de θ.
3. Trocar `|x| ≤ √(x²+y²)` por `x ≤ x² + y²` (falso perto da origem).
4. Esquecer de verificar se o ponto pertence ao domínio antes de falar em continuidade.
5. Escrever `x/(x²+y²)` como "limitada". Não é — o Guidorizzi grifa isso.
