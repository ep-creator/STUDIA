---
tipo: resumo
titulo: 14.4 Plano tangente e diferencial
unidade: 1
secao: null
questao: null
origem: migrado
---
# 14.4 Plano tangente e diferencial

> Diferenciabilidade, plano tangente, aproximação linear e diferencial · Stewart 14.4 · Guidorizzi 11.1–11.4

Este é o assunto mais recente visto em sala e o mais "teórico" da unidade. O Guidorizzi é bem mais rigoroso que o Stewart aqui — e o critério de correção do prof. Henrique é o do Guidorizzi.

## 1. Definição de função diferenciável (Guidorizzi 11.1)

> **Definição.** `f` é **diferenciável em `(x₀,y₀)`** (ponto interior de `D_f`) se as parciais `f_x(x₀,y₀)` e `f_y(x₀,y₀)` existem e
> ```
>            f(x₀+h, y₀+k) − f(x₀,y₀) − f_x(x₀,y₀)·h − f_y(x₀,y₀)·k
>   lim     ─────────────────────────────────────────────────────── = 0
> (h,k)→(0,0)                    ‖(h,k)‖
> ```

Leitura: o acréscimo real de f é aproximado pela transformação linear `L(h,k) = f_x·h + f_y·k` com **erro que vai a zero mais rápido que a distância**. É a generalização honesta de "a reta tangente aproxima a curva".

**Procedimento para provar diferenciabilidade pela definição** (Guidorizzi 11.1 ex. 1–3):
1. Calcule `f_x(x₀,y₀)` e `f_y(x₀,y₀)` — se a função é por partes, **pela definição de limite**.
2. Monte o quociente acima.
3. Mostre que o limite é 0 (confronto ou polares) — ou que **não** é 0/não existe, e conclua que f não é diferenciável.

## 2. Condição suficiente (o teorema que salva tempo)

> **Teorema (Stewart 14.4, Teor. 8).** Se `f_x` e `f_y` **existem numa vizinhança de `(a,b)` e são contínuas em `(a,b)`**, então `f` é diferenciável em `(a,b)`.

É **suficiente, não necessária**: existem funções diferenciáveis com parciais descontínuas. Mas na prática, em toda questão de cálculo direto, é isto que se cita para justificar diferenciabilidade em uma linha.

Funções cujas parciais são contínuas em todo o domínio (ditas de **classe C¹**): polinômios, exponenciais, senos/cossenos, e composições/quocientes destas onde o denominador não se anula.

## 3. Hierarquia de implicações — decore este diagrama

```
    parciais contínuas numa vizinhança
                  ⇓
            f diferenciável
              ⇙        ⇘
   f contínua        parciais existem
```

E **nenhuma seta volta**:

| Afirmação | Verdade? | Contraexemplo |
|---|---|---|
| parciais existem ⇒ contínua | **não** | `xy/(x²+y²)`, `f(0,0)=0` |
| parciais existem ⇒ diferenciável | **não** | mesmo exemplo |
| contínua ⇒ diferenciável | **não** | `√(x²+y²)` na origem (cone: bico) |
| diferenciável ⇒ contínua | **sim** | — |
| diferenciável ⇒ parciais existem | **sim** | — |
| parciais contínuas ⇒ diferenciável | **sim** | — |
| diferenciável ⇒ parciais contínuas | **não** | — |

## 4. Plano tangente

> **Definição (Guidorizzi 11.3).** Se `f` é diferenciável em `(x₀,y₀)`, o plano
> ```
> z − f(x₀,y₀) = f_x(x₀,y₀)·(x − x₀) + f_y(x₀,y₀)·(y − y₀)
> ```
> chama-se **plano tangente ao gráfico de f no ponto `(x₀, y₀, f(x₀,y₀))`**.

> **Só se define plano tangente onde f é diferenciável.** Se f admite parciais mas não é diferenciável, a equação acima ainda descreve *um* plano — mas ele **não é** o plano tangente. Escrever "plano tangente" nesse caso é erro conceitual, e o Guidorizzi grifa isso.

**Vetor normal ao plano tangente:** `n = ( f_x(x₀,y₀), f_y(x₀,y₀), −1 )`.

**Reta normal** (mesma seção do Guidorizzi):
```
(x, y, z) = (x₀, y₀, f(x₀,y₀)) + λ ( f_x(x₀,y₀), f_y(x₀,y₀), −1 ),   λ ∈ ℝ
```

**Questões inversas** (Guidorizzi 11.3 ex. 4 e 5 — caem em prova): dada a equação do plano tangente, extraia as parciais. Basta escrever o plano na forma `z = ax + by + c` e ler `f_x = a`, `f_y = b`, e `f(x₀,y₀)` = valor de z no ponto. Ex.: se `2x + y + 3z = 6` é tangente em `(1,1,1)`, então `z = 2 − (2/3)x − (1/3)y`, logo `f_x(1,1) = −2/3` e `f_y(1,1) = −1/3`.

**Plano tangente paralelo a um plano dado:** iguale as parciais aos coeficientes correspondentes e resolva o sistema para achar o ponto.

## 5. Aproximação linear (linearização)

> A **linearização** de f em `(a,b)` é
> ```
> L(x,y) = f(a,b) + f_x(a,b)(x − a) + f_y(a,b)(y − b)
> ```
> e a **aproximação linear** é `f(x,y) ≈ L(x,y)` para `(x,y)` próximo de `(a,b)`.

É exatamente o plano tangente escrito como função. Só é legítima onde f é diferenciável — sempre justifique isso antes de usar (via §2).

## 6. Diferencial

Para `z = f(x,y)` diferenciável, com acréscimos `dx = Δx` e `dy = Δy`:

```
dz = f_x(x,y) dx + f_y(x,y) dy        (diferencial total)
```

e `Δz = f(x+Δx, y+Δy) − f(x,y) ≈ dz`.

Para três variáveis: `dw = f_x dx + f_y dy + f_z dz`.

**Aplicações que caem:**
- **Valor aproximado:** `f(x₀+Δx, y₀+Δy) ≈ f(x₀,y₀) + dz`. Ex.: estimar `√(1,01) + ∛(7,9)`.
- **Propagação de erro:** se as medidas têm erro máximo `|Δx| ≤ e₁`, `|Δy| ≤ e₂`, então `|Δz| ≲ |f_x| e₁ + |f_y| e₂`. Erro **relativo**: `dz/z`.
- **Volume de material / variação de área:** trate a casca fina como `Δ` de volume (Guidorizzi 11.4 ex. 4 e 5).

## 7. Roteiro de resolução — questão típica de 14.4

1. **Identifique f, o ponto `(x₀,y₀)` e o que se pede.**
2. **Justifique a diferenciabilidade** — normalmente: "f é polinomial/racional com denominador não nulo em `(x₀,y₀)`; logo `f_x` e `f_y` são contínuas numa vizinhança e, pelo teorema da condição suficiente, f é diferenciável em `(x₀,y₀)`." Uma linha, mas vale ponto.
3. **Calcule `f(x₀,y₀)`, `f_x(x₀,y₀)`, `f_y(x₀,y₀)`** — mostrando as parciais gerais antes de avaliar.
4. **Escreva a fórmula pedida** (plano tangente / L(x,y) / dz).
5. **Substitua e simplifique**, e se for aproximação numérica, dê o valor com o número de casas do enunciado.

## 8. Erros que custam ponto

1. Montar o plano de §4 sem verificar a diferenciabilidade e chamá-lo de plano tangente.
2. Usar aproximação linear longe do ponto-base sem comentar a limitação.
3. Trocar `dz` por `Δz` como se fossem iguais — são **aproximadamente** iguais.
4. No vetor normal, esquecer o sinal negativo da terceira coordenada.
5. Provar diferenciabilidade "porque as parciais existem". Não é suficiente (§3).
