# 14.7 Valores máximo e mínimo

> Pontos críticos, ponto de sela, teste da segunda derivada, extremos em regiões fechadas · Stewart 14.7 · Guidorizzi 16.1–16.4

> **Onde a aula parou (29/09):** ponto de sela — ou seja, até o fim da §5. As §§6–8 ainda vêm, mas leia mesmo assim: a §6 é metade dos exercícios da lista.

## 1. Vocabulário, com cuidado

- **Máximo local** em `(a,b)`: `f(x,y) ≤ f(a,b)` para todo `(x,y)` **numa vizinhança** de `(a,b)`.
- **Máximo absoluto** (ou global): a desigualdade vale em **todo o domínio**.

O valor `f(a,b)` é o *valor máximo*; `(a,b)` é o *ponto de máximo*. Enunciados pedem ora um, ora outro, ora os dois — e o professor conta como itens separados.

## 2. Teorema de Fermat (condição necessária)

> Se f tem máximo ou mínimo **local** em `(a,b)` e as derivadas parciais de 1ª ordem **existem** ali, então
> ```
> f_x(a,b) = 0   e   f_y(a,b) = 0,   isto é,   ∇f(a,b) = 0.
> ```

Geometricamente: se existe plano tangente num extremo local, ele é horizontal.

> **É condição necessária, não suficiente.** Ele só serve para *achar candidatos*. Quem decide o que cada candidato é são as §§4–5.

## 3. Ponto crítico

`(a,b)` é **ponto crítico** de f se `∇f(a,b) = 0` **ou** se alguma das parciais **não existe** em `(a,b)`.

> A segunda cláusula é esquecida sempre. Em `f(x,y) = √(x²+y²)` (cone) a origem é mínimo absoluto e nenhuma das parciais existe lá. Se você só resolver `∇f = 0`, perde esse ponto.

Pelo teorema de Fermat: **todo extremo local é ponto crítico**. A recíproca é falsa.

## 4. Ponto de sela

Um ponto crítico que **não** é máximo nem mínimo local chama-se **ponto de sela**.

O exemplo canônico é `f(x,y) = y² − x²` na origem:

```
∇f = ⟨−2x, 2y⟩ = ⟨0,0⟩  ⟹  (0,0) é crítico,  f(0,0) = 0

sobre o eixo x (y = 0):  f(x,0) = −x² ≤ 0   →  a origem é MÁXIMO nessa direção
sobre o eixo y (x = 0):  f(0,y) = +y² ≥ 0   →  a origem é MÍNIMO nessa direção
```

Em toda vizinhança da origem há pontos com f > 0 e pontos com f < 0, então não pode ser extremo. O gráfico é o paraboloide hiperbólico — a sela de cavalo que dá nome ao caso.

> Esse argumento — **exibir duas direções com comportamentos opostos** — é uma demonstração completa e aceita. Guarde-o: ele é o plano B quando o teste da §5 falhar.

## 5. Teste da segunda derivada

> Suponha as segundas parciais de f contínuas numa bola em torno de `(a,b)`, e `∇f(a,b) = 0`. Defina
> ```
> D = D(a,b) = f_xx(a,b)·f_yy(a,b) − [ f_xy(a,b) ]²
> ```
> Então:
>
> | Caso | Conclusão |
> |---|---|
> | `D > 0` e `f_xx(a,b) > 0` | **mínimo local** |
> | `D > 0` e `f_xx(a,b) < 0` | **máximo local** |
> | `D < 0` | **ponto de sela** |
> | `D = 0` | **nada se conclui** — o teste falha |

Jeito de memorizar D: é o determinante da matriz hessiana,

```
       | f_xx   f_xy |
D = det|             | = f_xx f_yy − f_xy²
       | f_xy   f_yy |
```

Se `D > 0`, então `f_xx` e `f_yy` têm o mesmo sinal — dá no mesmo olhar para `f_yy` em vez de `f_xx`.

### Quando D = 0

Não escreva "o teste falha" e pare — isso não é resposta. Use um dos caminhos:

1. **Restringir a retas ou curvas pelo ponto.** Se `f` restrita a duas direções der comportamentos opostos, é sela (§4). Se der o mesmo sinal em todas, é forte indício de extremo — mas aí precisa provar.
2. **Argumento algébrico direto.** Em `f(x,y) = x⁴ + y⁴` a origem tem `D = 0`, mas `f(x,y) ≥ 0 = f(0,0)` para todo `(x,y)`: mínimo absoluto, provado em uma linha.

Os exercícios da lista 3 de 2026.1 (#5b, #5d) caem exatamente aqui.

## 6. Extremos absolutos em região fechada e limitada

> **Teorema do valor extremo.** Se f é **contínua** num conjunto `D ⊂ ℝ²` **fechado e limitado**, então f assume um valor máximo absoluto e um valor mínimo absoluto em D.

*Fechado* = contém toda a sua fronteira. *Limitado* = cabe dentro de algum disco. As duas hipóteses são necessárias: em `D` aberto o supremo pode não ser atingido; em `D` ilimitado pode nem existir.

### O roteiro (decore como roteiro, é assim que se escreve na prova)

```
1. Ache os pontos críticos de f no INTERIOR de D e calcule f neles.
2. Ache os valores extremos de f na FRONTEIRA de D.
3. O maior dos valores das etapas 1 e 2 é o máximo absoluto;
   o menor é o mínimo absoluto.
```

> Na etapa 1 **não** se usa o teste da segunda derivada. Não interessa classificar: interessa só o *valor* de f nos candidatos. Aplicar o teste ali é trabalho jogado fora — e o professor percebe.

### Como tratar a fronteira

A fronteira é unidimensional, então cada pedaço vira um problema de **Cálculo 1**.

| Fronteira | O que fazer |
|---|---|
| Segmento `y = c`, `a ≤ x ≤ b` | substitua: `g(x) = f(x,c)`, ache os críticos de g em `(a,b)` **e avalie os extremos `x = a`, `x = b`** |
| Polígono | trate **cada lado separadamente** e depois **cada vértice** |
| Circunferência `x² + y² = r²` | parametrize `x = r cos t`, `y = r sen t`, `t ∈ [0, 2π]`, e derive em t |

> **Os vértices e extremos de segmento são pontos de candidatura por si só.** Esquecer os quatro cantos de um quadrado é o erro mais comum da seção inteira.

Alternativa para a fronteira dada por equação: multiplicadores de Lagrange (14.8, próxima seção). Quase sempre a parametrização é mais rápida quando a fronteira é um polígono, e Lagrange é mais rápido quando é uma curva suave.

## 7. Problemas de otimização com enunciado em palavras

Caixa de volume máximo, distância mínima a uma superfície, e afins. Roteiro:

1. Escreva a grandeza a otimizar.
2. Use o vínculo para **eliminar uma variável**, deixando função de duas.
3. Otimize com as §§3–5.
4. **Volte ao enunciado** e responda o que foi perguntado (às vezes é a dimensão, não o volume).

> **Truque de distância.** Para minimizar `d = √((x−x₀)² + …)`, minimize `d²`. O ponto de mínimo é o mesmo, porque `t ↦ √t` é crescente — mas **diga isso por escrito**, é justificativa que o professor cobra. E se a pergunta foi a distância, lembre de tirar a raiz no fim.

## 8. Erros que custam ponto

1. Resolver `∇f = 0` e esquecer os pontos onde alguma parcial **não existe**.
2. Aplicar o teste da segunda derivada em ponto que **não** é crítico.
3. Parar em "`D = 0`, o teste falha" sem investigar (§5).
4. No roteiro da §6, esquecer **vértices** e **extremos dos segmentos** da fronteira.
5. Usar o teste da segunda derivada dentro do roteiro de extremos absolutos — desnecessário e confuso.
6. Responder o **ponto** quando o enunciado pediu o **valor**, ou o contrário.
7. Minimizar `d²` e entregar `d²` como resposta de distância.
8. Concluir "máximo absoluto" sem verificar que a região é fechada e limitada — sem isso o teorema da §6 não vale.
