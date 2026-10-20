# 14.5 Regra da cadeia e derivação implícita

> Stewart 14.5 (e o início do 14.6) · Guidorizzi cap. 12
> **Aulas de 02/09 e 04/09** — é o que fecha o programa da 1ª unidade.

## 1. O caso de uma variável, para lembrar

Se `y = f(x)` e `x = g(t)`, então `dy/dt = f'(g(t))·g'(t)`. Tudo o que vem abaixo é a mesma ideia com mais caminhos ligando a saída à entrada — e a regra é sempre **somar sobre todos os caminhos**.

## 2. Caso 1 — uma variável independente

> **Teorema.** Seja `z = f(x,y)` **diferenciável**, com `x = x(t)` e `y = y(t)` deriváveis. Então `z` é função derivável de `t` e
> ```
> dz/dt = (∂f/∂x)(dx/dt) + (∂f/∂y)(dy/dt)
> ```

Repare na notação: `dz/dt` e `dx/dt` são derivadas **totais** (uma variável só), `∂f/∂x` é parcial. Misturar `d` com `∂` na hora errada é erro de escrita que o professor marca.

**Forma vetorial (Guidorizzi 12.1).** Com `γ(t) = (x(t), y(t))` e `F(t) = f(γ(t))`:

```
F'(t) = ∇f(γ(t)) · γ'(t)
```

É a mesma fórmula — produto escalar do gradiente pelo vetor velocidade. Vale a pena aprender nesta forma: é ela que reaparece na 2ª unidade em derivada direcional.

## 3. Caso 2 — duas variáveis independentes

> Seja `z = f(x,y)` diferenciável, com `x = x(s,t)` e `y = y(s,t)` com parciais. Então
> ```
> ∂z/∂s = (∂f/∂x)(∂x/∂s) + (∂f/∂y)(∂y/∂s)
> ∂z/∂t = (∂f/∂x)(∂x/∂t) + (∂f/∂y)(∂y/∂t)
> ```

## 4. Versão geral e o diagrama em árvore

> Se `u = f(x₁, …, xₙ)` é diferenciável e cada `xᵢ = xᵢ(t₁, …, t_m)`, então para cada `j`
> ```
> ∂u/∂t_j = Σᵢ (∂u/∂xᵢ)(∂xᵢ/∂t_j)
> ```

**Como montar o diagrama** — é o que evita esquecer parcela:

1. Escreva `u` no topo.
2. Desça um ramo para **cada variável intermediária** (`x`, `y`, `z`, …).
3. De cada intermediária, desça um ramo para **cada variável independente** (`s`, `t`, …).
4. Para achar `∂u/∂t`: percorra **todos os caminhos** de `u` até `t`; em cada caminho **multiplique** as derivadas dos ramos; **some** os caminhos.

Regra de bolso: o número de parcelas é o número de variáveis intermediárias.

## 5. Derivação implícita

### Uma equação, duas variáveis

Se `F(x,y) = 0` define `y` como função de `x`, derive os dois lados em relação a `x` pela regra da cadeia:

```
F_x + F_y·(dy/dx) = 0   ⟹   dy/dx = − F_x / F_y      (F_y ≠ 0)
```

### Uma equação, três variáveis

Se `F(x,y,z) = 0` define `z = z(x,y)`:

```
∂z/∂x = − F_x / F_z          ∂z/∂y = − F_y / F_z       (F_z ≠ 0)
```

> **O sinal de menos e o denominador são a fonte de erro nº 1.** Derive-se em relação a `x`: `F_x·1 + F_y·0 + F_z·(∂z/∂x) = 0`. Isolando, sai o menos. Faça essa conta uma vez à mão para nunca mais trocar.

### Teorema das funções implícitas (Guidorizzi 12.2)

> Seja `F` de classe C¹ numa vizinhança de `(x₀, y₀, z₀)`, com `F(x₀,y₀,z₀) = 0` e **`F_z(x₀,y₀,z₀) ≠ 0`**. Então existe uma vizinhança de `(x₀,y₀)` na qual a equação `F(x,y,z) = 0` define uma única função `z = z(x,y)` de classe C¹, com `z(x₀,y₀) = z₀`, e valem as fórmulas acima.

**Cite as hipóteses.** Escrever `∂z/∂x = −F_x/F_z` sem verificar `F_z ≠ 0` é exatamente o tipo de passo omitido que custa ponto. E note que o teorema é **local**: garante a função perto do ponto, não no plano todo.

## 6. Ordens superiores pela cadeia

Ao derivar de novo, lembre que `∂f/∂x` **continua sendo função de x e y**, que por sua vez dependem dos parâmetros. Então a segunda derivada exige aplicar a cadeia outra vez:

```
∂²z/∂t²  =  ∂/∂t [ f_x·(∂x/∂t) + f_y·(∂y/∂t) ]
         =  [ f_xx·(∂x/∂t) + f_xy·(∂y/∂t) ]·(∂x/∂t) + f_x·(∂²x/∂t²)
          + [ f_yx·(∂x/∂t) + f_yy·(∂y/∂t) ]·(∂y/∂t) + f_y·(∂²y/∂t²)
```

Não decore: refaça aplicando produto + cadeia. É o assunto da seção 14.2 do Guidorizzi, e aparece nos exercícios que pedem para mostrar que uma mudança de variáveis leva uma EDP em outra.

## 7. Aplicações que caem

- **Taxas relacionadas**: volume, temperatura ou pressão que dependem do tempo através de várias grandezas. Monte o diagrama, substitua os valores **só no fim**.
- **Mudança para coordenadas polares**: com `x = r cos θ`, `y = r sen θ`, mostrar que
  `(∂z/∂x)² + (∂z/∂y)² = (∂z/∂r)² + (1/r²)(∂z/∂θ)²`.
- **Funções homogêneas** — relação de Euler: se `f` é homogênea de grau `n`, então
  `x·f_x + y·f_y = n·f`. Sai derivando `f(tx, ty) = tⁿ f(x,y)` em relação a `t` e fazendo `t = 1`.

## 8. Erros que custam ponto

1. **Esquecer uma parcela.** Cada variável intermediária contribui com um termo. Diagrama antes da conta.
2. **Trocar `d` por `∂`.** Se a função depende de um só parâmetro no fim, a derivada é total.
3. **Usar a cadeia sem diferenciabilidade.** O teorema exige `f` **diferenciável** — parciais existirem não basta. Diga isso na primeira linha da resolução.
4. **Perder o sinal na derivação implícita**, ou dividir por `F_z` sem dizer que é não nulo.
5. **Substituir cedo demais.** Deixe em termos de `x` e `y` e só no final troque por `x(t)`, `y(t)` — a conta fica menor e o erro fica mais fácil de achar.
