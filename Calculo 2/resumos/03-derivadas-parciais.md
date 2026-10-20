# 14.3 Derivadas parciais

> Derivadas parciais e de ordens superiores · Stewart 14.3 · Guidorizzi caps. 10 e 14

## 1. Definição

Fixando `y = y₀`, a função de uma variável `g(x) = f(x, y₀)` tem derivada em `x₀` (se existir), e essa é a derivada parcial de f em relação a x:

```
∂f/∂x (x₀,y₀) = g'(x₀) = lim_{x→x₀}  [ f(x,y₀) − f(x₀,y₀) ] / (x − x₀)

              = lim_{h→0}  [ f(x₀+h, y₀) − f(x₀,y₀) ] / h
```

Analogamente:

```
∂f/∂y (x₀,y₀) = lim_{k→0}  [ f(x₀, y₀+k) − f(x₀,y₀) ] / k
```

**Notações equivalentes:** `∂f/∂x = f_x = f₁ = D₁f = D_x f`. Na prova use uma só e seja consistente.

## 2. Como calcular (regra prática)

> Para achar `f_x`, trate **y como constante** e derive normalmente em x. Para `f_y`, trate x como constante.

Todas as regras de uma variável valem: produto, quociente, cadeia de uma variável.

**Quando a regra prática NÃO serve:** funções definidas por partes, no ponto de junção. Aí é obrigatório **voltar à definição por limite**. Esse é o item que separa nota 7 de nota 10.

Exemplo (Stewart 14.3 #100-ish): `f(x,y) = ∛(x³+y³)`.
```
f_x(0,0) = lim_{h→0} [ ∛(h³+0) − 0 ] / h = lim_{h→0} h/h = 1.
```
Derivar pela regra da cadeia daria `x²/(x³+y³)^{2/3}`, indefinido em (0,0) — a definição resolve, a regra não.

## 3. Interpretações

**Geométrica.** `f_x(a,b)` é o coeficiente angular da reta tangente, no ponto `P(a, b, f(a,b))`, à curva `C₁` obtida cortando a superfície `z = f(x,y)` com o plano vertical `y = b`. Idem `f_y` com o plano `x = a`.

**Taxa de variação.** `f_x(a,b)` = taxa instantânea de variação de f na direção de x, com y parado.

**Em tabelas** (exercícios do tipo "índice de sensação térmica", "temperatura T(x,t)"): estime por diferenças
```
f_x(a,b) ≈ [ f(a+h, b) − f(a−h, b) ] / (2h)
```
usando os valores vizinhos na **mesma linha** da tabela; para `f_y`, na mesma coluna. Sempre diga a **unidade** do resultado — o Stewart cobra e o professor também.

**Determinar sinal pelo gráfico/mapa de contorno:** ande na direção positiva de x; se os níveis crescem, `f_x > 0`.

## 4. Três ou mais variáveis

Mesma ideia: `∂f/∂x_i` deriva em `x_i` mantendo as demais fixas. Para `w = f(x,y,z)` são três parciais de 1ª ordem.

## 5. Derivadas de ordens superiores

```
f_xx = ∂/∂x (∂f/∂x) = ∂²f/∂x²
f_xy = ∂/∂y (∂f/∂x) = ∂²f/∂y∂x     ← deriva primeiro em x, depois em y
f_yx = ∂/∂x (∂f/∂y) = ∂²f/∂x∂y
f_yy = ∂²f/∂y²
```

> **Atenção à ordem de leitura.** Na notação de índices, `f_xy` significa "primeiro x, depois y" — lê-se da esquerda para a direita. Na notação `∂²f/∂y∂x`, lê-se **da direita para a esquerda**. As duas dizem a mesma coisa. Escolha uma.

### Teorema de Clairaut (ou de Schwarz)

> Seja `f` definida numa bola aberta `D` contendo `(a,b)`. Se `f_xy` e `f_yx` são **contínuas em D**, então
> ```
> f_xy(a,b) = f_yx(a,b).
> ```

A hipótese de continuidade é essencial. O contraexemplo (Stewart 14.3 #101, e o Guidorizzi repete):

```
f(x,y) = (x³y − xy³)/(x² + y²)  se (x,y) ≠ (0,0);   f(0,0) = 0
```
tem `f_xy(0,0) = −1` e `f_yx(0,0) = 1`. Não há contradição: as mistas não são contínuas na origem. **Faça esse exercício inteiro** — é a questão de teoria mais provável da unidade.

Corolário útil: se as parciais de 3ª ordem forem contínuas, `f_xyy = f_yxy = f_yyx` (Stewart #97).

## 6. Equações diferenciais parciais que aparecem

Vários exercícios pedem só "verifique que f satisfaz a equação". Calcule as parciais e substitua.

| Nome | Equação |
|---|---|
| Laplace | `u_xx + u_yy = 0` (em 3D, `+ u_zz = 0`) |
| Onda | `u_tt = a² u_xx` |
| Calor | `u_t = k u_xx` |

## 7. O aviso mais importante desta seção

> **Existir as derivadas parciais em um ponto NÃO implica que f seja contínua nesse ponto**, e muito menos que seja diferenciável.

Exemplo: `f(x,y) = xy/(x²+y²)` para `(x,y) ≠ (0,0)`, `f(0,0) = 0`. Como `f(x,0) = 0` e `f(0,y) = 0`, temos `f_x(0,0) = f_y(0,0) = 0` — ambas existem. Mas sobre `y = x` a função vale `1/2` constante, então nem limite tem na origem: **descontínua**.

A razão conceitual: as parciais só olham duas direções. Diferenciabilidade (próximo resumo) é a condição que olha **todas** as direções de uma vez.

## 8. Erros que custam ponto

1. Usar a regra prática em ponto de junção de função por partes, em vez da definição.
2. Confundir a ordem em `f_xy` vs `∂²f/∂x∂y`.
3. Aplicar Clairaut sem mencionar a hipótese de continuidade.
4. Estimar parcial em tabela e não dar a unidade.
5. Dizer "as parciais existem, logo f é diferenciável". Falso — ver §7.
