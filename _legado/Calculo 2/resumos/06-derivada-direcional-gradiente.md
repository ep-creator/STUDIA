# 14.6 Derivada direcional e vetor gradiente

> Derivada direcional, gradiente, direção de crescimento máximo, planos tangentes a superfícies de nível · Stewart 14.6 · Guidorizzi 11.5 e 13.1–13.4

## 1. A pergunta que motiva a seção

As parciais `f_x` e `f_y` medem a taxa de variação em **duas** direções: a do eixo x e a do eixo y. E nas outras infinitas direções?

A derivada direcional responde. Ela é a mesma ideia — quanto f varia por unidade de deslocamento — só que ao longo de uma direção `u` qualquer.

## 2. Definição

Seja `u = ⟨a, b⟩` um vetor **unitário** (`|u| = 1`). A derivada direcional de f em `(x₀,y₀)` na direção de u é

```
D_u f(x₀,y₀) = lim_{h→0}  [ f(x₀ + ha, y₀ + hb) − f(x₀,y₀) ] / h
```

quando o limite existe.

> **O vetor tem que ser unitário.** Se o enunciado der `v` não unitário, normalize primeiro: `u = v/|v|`. Pular esse passo é o erro nº 1 desta seção, e ele muda o valor numérico da resposta.

Casos particulares: `u = ⟨1,0⟩` dá `D_u f = f_x`; `u = ⟨0,1⟩` dá `D_u f = f_y`. A derivada direcional generaliza as parciais.

## 3. O teorema de cálculo

> **Teorema.** Se f é **diferenciável** em `(x₀,y₀)`, então `D_u f` existe em toda direção `u = ⟨a,b⟩` e
> ```
> D_u f(x₀,y₀) = f_x(x₀,y₀)·a + f_y(x₀,y₀)·b
> ```

É esse teorema que transforma um limite num produto escalar. **A hipótese é diferenciabilidade, não "as parciais existem"** — e essa distinção é cobrada: existe função com derivada direcional em toda direção que nem contínua é.

Em ângulo: se `u = ⟨cos θ, sen θ⟩`, então `D_u f = f_x cos θ + f_y sen θ`.

## 4. O gradiente

```
∇f(x,y) = ⟨ f_x(x,y) , f_y(x,y) ⟩          (em ℝ³:  ⟨f_x, f_y, f_z⟩)
```

Lê-se "gradiente de f" ou "del f". É um **vetor**, não um número — escrever `∇f = 3` custa ponto.

Com ele o teorema da §3 vira

```
D_u f = ∇f · u = |∇f| · |u| · cos φ = |∇f| cos φ
```

onde φ é o ângulo entre `∇f` e `u` (a última igualdade usa `|u| = 1`).

## 5. A consequência que vale metade dos exercícios

Como `cos φ` varia entre −1 e 1:

| Direção | Valor de `D_u f` | Interpretação |
|---|---|---|
| `u` na direção de `∇f` (φ = 0) | **`+|∇f|`** | crescimento **mais rápido** |
| `u` na direção de `−∇f` (φ = π) | **`−|∇f|`** | decrescimento mais rápido |
| `u` perpendicular a `∇f` (φ = π/2) | **0** | f não varia |

> **Enunciado do teorema, para citar na prova.** Seja f diferenciável. O valor máximo de `D_u f(x)` é `|∇f(x)|`, atingido quando u tem a mesma direção e sentido de `∇f(x)`.

Traduções de enunciado que você vai encontrar:

- *"em que direção a temperatura cresce mais rápido?"* → `∇T`
- *"qual a taxa máxima de variação?"* → `|∇T|` (um número)
- *"em que direções f não varia?"* → as perpendiculares a `∇f`
- *"a formiga foge do calor"* → `−∇T`

## 6. Gradiente ⟂ curva de nível

> **Teorema.** `∇f(x₀,y₀)` é **perpendicular** à curva de nível de f que passa por `(x₀,y₀)`. Em ℝ³, `∇F(x₀,y₀,z₀)` é perpendicular à superfície de nível `F = k`.

Por quê: ao andar sobre a curva de nível, f não muda, logo `D_u f = 0` nessa direção, logo `∇f · u = 0`.

Daí sai o **plano tangente a uma superfície de nível** `F(x,y,z) = k`:

```
F_x(P)(x−x₀) + F_y(P)(y−y₀) + F_z(P)(z−z₀) = 0
```

e a **reta normal**, que tem `∇F(P)` como vetor diretor:

```
(x, y, z) = (x₀, y₀, z₀) + t·∇F(x₀,y₀,z₀)
```

> **Isto unifica o 14.4 com o 14.6.** O plano tangente ao gráfico `z = f(x,y)` é caso particular: tome `F(x,y,z) = f(x,y) − z`, cuja superfície de nível `F = 0` é o próprio gráfico. Fazendo as contas cai na fórmula do 14.4. Se a prova pedir plano tangente a algo que **não** está na forma `z = f(x,y)` (um elipsoide, um cone), use a fórmula desta seção.

## 7. Três variáveis

Tudo vale igual, com `u = ⟨a,b,c⟩` unitário:

```
D_u f = ∇f · u = f_x a + f_y b + f_z c
```

## 8. O tipo de exercício que exige montar sistema

*"A derivada direcional na direção de u vale 5 e na direção de v vale 3. Determine ∇f."*

Não há truque: cada informação vira uma equação linear `∇f · u = 5`, `∇f · v = 3` nas incógnitas `f_x` e `f_y`. Duas direções não paralelas ⇒ sistema 2×2 determinado. É a lista 3 #4 de 2026.1.

## 9. Erros que custam ponto

1. **Não normalizar o vetor direção.** Se `v = ⟨2, −1/3⟩`, então `|v| = √(4 + 1/9)` e é `v/|v|` que entra na conta.
2. **Tratar `∇f` como número** — ou responder "a taxa máxima é `∇f`" quando o certo é `|∇f|`.
3. **Usar o teorema da §3 sem diferenciabilidade.** Se a função é definida por partes na origem, o teorema não se aplica: volte à definição por limite da §2.
4. **Confundir *direção de maior crescimento* (um vetor) com *taxa de maior crescimento* (um número).** Leia o que o enunciado pede.
5. **Esquecer que o ponto tem que satisfazer a equação da superfície** nos exercícios de plano tangente a superfície de nível.
6. Dar a resposta da reta normal como equação de plano, ou vice-versa.
