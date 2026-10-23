# 15.5 Aplicações de Integrais Duplas

> Densidade superficial, massa, carga elétrica, momentos estáticos, centro de massa (e centroide), momentos de inércia ($I_x, I_y, I_0$), raio de giração e densidade conjunta de probabilidade · Stewart 15.5 · Guidorizzi cap. 18 (Massa e Centro de Massa) · Listas 4 e 5 UFPE · 3ª unidade

---

## 1. Contexto e Motivação

No Cálculo 1, estudamos como calcular a massa e o centro de massa de placas planas finas (**lâminas**) supondo que a densidade superficial fosse **constante** (lâmina homogênea). Com as integrais duplas, podemos generalizar essa análise para:
1. **Lâminas heterogêneas**, onde a densidade superficial $\rho(x,y)$ varia ponto a ponto.
2. **Distribuições superficiais gerais**, como densidade superficial de carga elétrica $\sigma(x,y)$ ou funções densidade conjunta de probabilidade $f(x,y)$ para duas variáveis aleatórias contínuas $(X,Y)$.

---

## 2. Densidade Superficial, Massa e Carga Elétrica

### Definição 1 — Densidade Superficial e Massa Total
Considere uma lâmina fina ocupando uma região compacta $D \subset \mathbb{R}^2$. Se a massa de um pequeno sub-retângulo de área $\Delta A$ contendo $(x,y)$ é $\Delta m$, a **densidade superficial de massa** no ponto $(x,y)$ é definida por:
$$\rho(x,y) = \lim_{\Delta A \to 0} \frac{\Delta m}{\Delta A}$$
*(medida em unidades de massa por unidade de área, ex.: $\text{kg/m}^2$ ou $\text{g/cm}^2$).*

**Hipótese de Integrabilidade (Citar na prova):** Sendo $\rho: D \to \mathbb{R}$ uma função contínua na região limitada e fechada $D$, o limite das somas de Riemann $\sum \rho(x_{ij}^*, y_{ij}^*)\,\Delta A$ existe e fornece a **massa total $m$** da lâmina:
$$m = \iint_D \rho(x,y)\,dA$$

### Definição 2 — Carga Elétrica Total
Analogamente, se uma carga elétrica está distribuída sobre a região plana $D$ com **densidade superficial de carga** contínua $\sigma(x,y)$ (em $\text{C/m}^2$), a **carga elétrica total $Q$** na região é:
$$Q = \iint_D \sigma(x,y)\,dA$$

### Tradução dos Enunciados Clássicos de Densidade (Crucial em Provas)
Em problemas de prova (como na Lista 5 da UFPE e nos exercícios do Stewart), a função $\rho(x,y)$ quase nunca é dada pronta na forma algébrica; ela vem descrita em palavras. Use o dicionário abaixo para montar $\rho(x,y)$:

| Expressão no Enunciado | Fator de Distância Geométrica | Função Densidade $\rho(x,y)$ ($k > 0$ constante) |
|---|---|---|
| *"Lâmina homogênea"* ou *"Centroide da região"* | — | $\rho(x,y) = k$ (constante; pode-se usar $\rho = 1$ no centroide) |
| *"Proporcional à distância à origem $(0,0)$"* | $d = \sqrt{x^2 + y^2} = r$ | $\rho(x,y) = k\sqrt{x^2 + y^2} \quad (\text{em polares: } \rho = kr)$ |
| *"Proporcional ao quadrado da distância à origem"* | $d^2 = x^2 + y^2 = r^2$ | $\rho(x,y) = k(x^2 + y^2) \quad (\text{em polares: } \rho = kr^2)$ |
| *"Proporcional à distância ao eixo $x$"* | $d(P, \text{eixo } x) = |y|$ | $\rho(x,y) = k|y|$ (se $D$ está no semiplano $y \ge 0$, $\rho = ky$) |
| *"Proporcional à distância ao eixo $y$"* | $d(P, \text{eixo } y) = |x|$ | $\rho(x,y) = k|x|$ (se $D$ está no semiplano $x \ge 0$, $\rho = kx$) |
| *"Proporcional à distância à reta $y = y_0$"* | $d = |y - y_0|$ | $\rho(x,y) = k|y - y_0|$ |

---

## 3. Primeiros Momentos e Centro de Massa (e Centroide)

O momento estático (ou primeiro momento) de uma partícula em relação a um eixo mede a tendência de giro ou ponderação de posição: é o produto da **massa** pela **distância orientada** ao eixo.

### Definição 3 — Momentos Estáticos ($M_x$ e $M_y$)
Para uma lâmina ocupando $D$ com densidade contínua $\rho(x,y)$:
- **Momento em relação ao eixo $x$** (a distância orientada ao eixo $x$ é a coordenada **$y$**):
  $$M_x = \iint_D y\,\rho(x,y)\,dA$$
- **Momento em relação ao eixo $y$** (a distância orientada ao eixo $y$ é a coordenada **$x$**):
  $$M_y = \iint_D x\,\rho(x,y)\,dA$$

> **Atenção aos subscritos trocados!** No momento $M_x$ multiplica-se por $y$; no momento $M_y$ multiplica-se por $x$.

### Definição 4 — Centro de Massa $(\bar{x}, \bar{y})$
O **centro de massa** é o ponto $(\bar{x}, \bar{y})$ onde toda a massa $m$ da lâmina poderia ser concentrada sem alterar seus momentos estáticos em relação aos eixos ($m\bar{x} = M_y$ e $m\bar{y} = M_x$), isto é, o ponto de equilíbrio horizontal da placa:
$$\bar{x} = \frac{M_y}{m} = \frac{1}{m}\iint_D x\,\rho(x,y)\,dA, \qquad \bar{y} = \frac{M_x}{m} = \frac{1}{m}\iint_D y\,\rho(x,y)\,dA$$

### Caso Particular: Centroide (Centro Geométrico)
Quando a lâmina é **homogênea** ($\rho(x,y) = \rho_0 = \text{constante}$) ou o enunciado pede o **centroide** da região plana $D$, a constante $\rho_0$ cancela no numerador e no denominador ($m = \rho_0 \cdot \text{Área}(D)$), restando apenas a geometria de $D$:
$$\bar{x} = \frac{1}{A(D)}\iint_D x\,dA, \qquad \bar{y} = \frac{1}{A(D)}\iint_D y\,dA, \qquad \text{onde } A(D) = \iint_D 1\,dA$$

---

## 4. Como Enxergar, Desenhar e Explorar Simetrias (Atalho de Ouro na Prova)

> **Regra da Disciplina:** *Desenho primeiro, limites depois!* Além de obrigatório na correção do professor Henrique Araújo, o esboço geométrico da região $D$ permite usar **simetria** para zerar integrais inteiras sem fazer conta!

### Teorema Prático da Simetria para Centro de Massa
1. **Simetria em relação ao eixo $y$** ($D$ é invariante por $(x,y) \mapsto (-x,y)$, isto é, o lado esquerdo espelha o lado direito):
   - Se a densidade também for par em $x$, $\rho(-x,y) = \rho(x,y)$, então o integrando $x\,\rho(x,y)$ é uma função **ímpar** em $x$ num domínio simétrico.
   - **Conclusão imediata:** $M_y = \iint_D x\,\rho(x,y)\,dA = 0 \implies \bar{x} = 0$ (o centro de massa está sobre o eixo $y$).
2. **Simetria em relação ao eixo $x$** ($D$ é invariante por $(x,y) \mapsto (x,-y)$, isto é, a metade de cima espelha a metade de baixo):
   - Se a densidade também for par em $y$, $\rho(x,-y) = \rho(x,y)$, então o integrando $y\,\rho(x,y)$ é **ímpar** em $y$.
   - **Conclusão imediata:** $M_x = \iint_D y\,\rho(x,y)\,dA = 0 \implies \bar{y} = 0$ (o centro de massa está sobre o eixo $x$).
3. **Simetria em relação à reta $y = x$** ($D$ não se altera ao trocar $x \leftrightarrow y$, como o setor no 1º quadrante limitado por $x^2+y^2 = R^2$):
   - Se $\rho(x,y) = \rho(y,x)$, então por mudança de nomes das variáveis mudas, $M_x = M_y \implies \bar{x} = \bar{y}$ (basta calcular $\bar{x}$ e concluir que $\bar{y}$ tem o mesmo valor!).

> **Como redigir na prova para ganhar 100% dos pontos:**
> *"Como a região $D$ é simétrica em relação ao eixo $y$ e a função densidade $\rho(x,y)$ é par na variável $x$, a função $g(x,y) = x\,\rho(x,y)$ é ímpar em $x$. Logo, por simetria, $M_y = \iint_D x\,\rho(x,y)\,dA = 0$, o que implica $\bar{x} = 0$."*

---

## 5. Segundos Momentos: Momentos de Inércia e Raio de Giração

Enquanto a massa mede a resistência de um corpo à aceleração linear, o **momento de inércia** (ou segundo momento) mede a resistência da lâmina à aceleração angular (rotação) em torno de um eixo. Para uma partícula de massa $m$ a uma distância perpendicular $r$ do eixo de rotação, $I = m r^2$.

### Definição 5 — Momentos de Inércia ($I_x, I_y, I_0$)
Seja $D$ uma lâmina com densidade contínua $\rho(x,y)$:
1. **Momento de inércia em relação ao eixo $x$** (quadrado da distância ao eixo $x$ é $y^2$):
   $$I_x = \iint_D y^2\,\rho(x,y)\,dA$$
2. **Momento de inércia em relação ao eixo $y$** (quadrado da distância ao eixo $y$ é $x^2$):
   $$I_y = \iint_D x^2\,\rho(x,y)\,dA$$
3. **Momento de inércia em relação à origem** (ou **Momento Polar de Inércia** / em torno do eixo $z$ perpendicular ao plano na origem; quadrado da distância à origem é $x^2 + y^2$):
   $$I_0 = \iint_D (x^2 + y^2)\,\rho(x,y)\,dA$$

### Propriedade Fundamental Aditiva (Teorema dos Eixos Perpendiculares)
Pela linearidade da integral dupla, vale sempre:
$$I_0 = I_x + I_y$$
**Truque clássico de prova (Veja Exemplo 4 do Stewart):** Para um disco centrado na origem $x^2 + y^2 \le a^2$ com densidade radial $\rho(r)$, calcular $I_x$ ou $I_y$ diretamente exige integrar $\sin^2\theta$ ou $\cos^2\theta$. Em vez disso:
1. Calcule primeiro $I_0 = \iint_D (x^2+y^2)\rho\,dA = \int_0^{2\pi}\int_0^a r^2\,\rho(r)\,r\,dr\,d\theta$ (que não depende de $\theta$!).
2. Use a simetria entre $x$ e $y$ no disco para afirmar que $I_x = I_y$.
3. Conclua em uma linha que $I_x = I_y = \frac{1}{2}I_0$!

### Definição 6 — Raio de Giração
O **raio de giração** $R$ de uma lâmina de massa $m$ em relação a um eixo é a distância na qual toda a massa $m$ poderia ser concentrada num único ponto mantendo o mesmo momento de inércia $I$ em relação àquele eixo ($m R^2 = I$):
- **Raio de giração em relação ao eixo $x$** ($\bar{\bar{y}}$):
  $$m\,\bar{\bar{y}}^2 = I_x \implies \bar{\bar{y}} = \sqrt{\frac{I_x}{m}}$$
- **Raio de giração em relação ao eixo $y$** ($\bar{\bar{x}}$):
  $$m\,\bar{\bar{x}}^2 = I_y \implies \bar{\bar{x}} = \sqrt{\frac{I_y}{m}}$$

---

## 6. Conversão para Coordenadas Polares (Alerta Máximo de Jacobiano!)

Mais da metade das questões de centro de massa e momento de inércia (como as questões 8 e 9 da Lista 5 da UFPE) envolve discos, setores, cardioides ou rosáceas. Ao passar para coordenadas polares ($x = r\cos\theta$, $y = r\sin\theta$, $dA = r\,dr\,d\theta$), o fator $r$ do Jacobiano se junta aos fatores $r$ vindos de $x$, $y$ ou $\rho(r,\theta)$:

| Grandeza Física | Integral em Cartesianas $(x,y)$ | Integral em Polares $(r,\theta)$ — **Cuidado com a potência de $r$!** |
|---|---|---|
| **Massa** $m$ | $\iint_D \rho(x,y)\,dx\,dy$ | $\iint_D \rho(r\cos\theta, r\sin\theta)\,\mathbf{r}\,dr\,d\theta$ |
| **Momento** $M_y$ (para $\bar{x}$) | $\iint_D x\,\rho(x,y)\,dx\,dy$ | $\iint_D (r\cos\theta)\,\rho(r,\theta)\,\mathbf{r}\,dr\,d\theta = \iint_D \mathbf{r^2}\cos\theta\,\rho(r,\theta)\,dr\,d\theta$ |
| **Momento** $M_x$ (para $\bar{y}$) | $\iint_D y\,\rho(x,y)\,dx\,dy$ | $\iint_D (r\sin\theta)\,\rho(r,\theta)\,\mathbf{r}\,dr\,d\theta = \iint_D \mathbf{r^2}\sin\theta\,\rho(r,\theta)\,dr\,d\theta$ |
| **Inércia** $I_x$ | $\iint_D y^2\,\rho(x,y)\,dx\,dy$ | $\iint_D (r^2\sin^2\theta)\,\rho(r,\theta)\,\mathbf{r}\,dr\,d\theta = \iint_D \mathbf{r^3}\sin^2\theta\,\rho(r,\theta)\,dr\,d\theta$ |
| **Inércia** $I_y$ | $\iint_D x^2\,\rho(x,y)\,dx\,dy$ | $\iint_D (r^2\cos^2\theta)\,\rho(r,\theta)\,\mathbf{r}\,dr\,d\theta = \iint_D \mathbf{r^3}\cos^2\theta\,\rho(r,\theta)\,dr\,d\theta$ |
| **Inércia Polar** $I_0$ | $\iint_D (x^2+y^2)\,\rho(x,y)\,dx\,dy$ | $\iint_D r^2\,\rho(r,\theta)\,\mathbf{r}\,dr\,d\theta = \iint_D \mathbf{r^3}\,\rho(r,\theta)\,dr\,d\theta$ |

*(E se além disso a densidade for $\rho = k\sqrt{x^2+y^2} = kr$, todas as potências de $r$ acima sobem em mais $1$ grau!)*

---

## 7. Probabilidade Conjunta e Valores Esperados

As mesmas ideias matemáticas aplicam-se à Teoria das Probabilidades quando distribuímos "massa de probabilidade total igual a $1$" pelo plano $\mathbb{R}^2$.

### Definição 7 — Função Densidade Conjunta
Sejam $X$ e $Y$ duas variáveis aleatórias contínuas. Uma função $f: \mathbb{R}^2 \to \mathbb{R}$ é a **função densidade conjunta** de $(X,Y)$ se satisfaz as duas condições de legitimidade:
1. **Não-negatividade:** $f(x,y) \ge 0$ para todo $(x,y) \in \mathbb{R}^2$.
2. **Normalização (Probabilidade Total = 1):**
   $$\iint_{\mathbb{R}^2} f(x,y)\,dA = \int_{-\infty}^{\infty}\int_{-\infty}^{\infty} f(x,y)\,dx\,dy = 1$$

A **probabilidade de o par $(X,Y)$ pertencer a uma região $D \subset \mathbb{R}^2$** (evento $(X,Y) \in D$) é o volume sob o gráfico de $z = f(x,y)$ acima da região $D$:
$$P\big((X,Y) \in D\big) = \iint_D f(x,y)\,dA$$
Em particular, para um retângulo: $P(a \le X \le b,\; c \le Y \le d) = \int_a^b \int_c^d f(x,y)\,dy\,dx$.

### Definição 8 — Variáveis Aleatórias Independentes
Se $X$ tem função densidade marginal $f_1(x)$ e $Y$ tem função densidade marginal $f_2(y)$, dizemos que $X$ e $Y$ são **independentes** se, e somente se, sua função densidade conjunta é o produto das densidades individuais:
$$f(x,y) = f_1(x)\,f_2(y)$$

**Modelos Clássicos de Densidade Unidimensional (usados nos Exemplos 7 e 8 do Stewart):**
- **Distribuição Exponencial** (tempo de espera com média $\mu > 0$):
  $$f(t) = \begin{cases} 0, & \text{se } t < 0 \\ \frac{1}{\mu}e^{-t/\mu}, & \text{se } t \ge 0 \end{cases}$$
- **Distribuição Normal (Gaussiana)** (com média $\mu$ e desvio-padrão $\sigma > 0$):
  $$f(x) = \frac{1}{\sigma\sqrt{2\pi}}\,\exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$$

### Definição 9 — Valores Esperados (Médias $\mu_1$ e $\mu_2$)
Os **valores esperados** (ou médias) de $X$ e $Y$, denotados por $\mu_1 = E(X)$ e $\mu_2 = E(Y)$, são exatamente as coordenadas $(\bar{x}, \bar{y})$ do "centro de massa" da distribuição de probabilidade (já que a "massa total" é $\iint_{\mathbb{R}^2} f\,dA = 1$):
$$\mu_1 = \iint_{\mathbb{R}^2} x\,f(x,y)\,dA, \qquad \mu_2 = \iint_{\mathbb{R}^2} y\,f(x,y)\,dA$$

---

## 8. Receita Passo a Passo para Questões de Prova

1. **Esboce a região $D$ com rigor geométrico:**
   - Identifique todas as curvas da fronteira, calcule os pontos de interseção e sombreie a região $D$.
   - Decida se é melhor descrever $D$ como Tipo I, Tipo II ou em **Coordenadas Polares** (pelo método da semirreta radial).
2. **Escreva explicitamente a função densidade $\rho(x,y)$:**
   - Traduza o texto do enunciado para a expressão matemática de $\rho(x,y)$. Se for centroide, fixe $\rho(x,y) = 1$.
   - Cite que $\rho$ é contínua em $D$ para garantir a integrabilidade e o uso do Teorema de Fubini.
3. **Verifique Simetrias ANTES de integrar:**
   - Olhe para o seu desenho de $D$ e para a função $\rho(x,y)$. Há simetria em relação ao eixo $x$, ao eixo $y$ ou à reta $y = x$? Se houver, justifique a paridade do integrando e economize uma das integrais de momento!
4. **Calcule a Massa Total $m$:**
   - Monte e calcule $m = \iint_D \rho(x,y)\,dA$. Verifique se $m > 0$ (massa nunca pode ser zero ou negativa!).
5. **Calcule os Momentos Solicitados ($M_x, M_y$ ou $I_x, I_y, I_0$):**
   - Não esqueça de dividir $M_y$ e $M_x$ pela massa $m$ no final para obter $(\bar{x}, \bar{y})$.
   - Faça o **teste de sanidade visual**: marque o ponto $(\bar{x}, \bar{y})$ encontrado no seu esboço de $D$. Se $D$ for convexa (ex.: triângulo, disco, semidisco), o centro de massa **obrigatoriamente** tem que cair dentro do desenho!

---

## 9. Erros que Custam Ponto (Armadilhas Clássicas de Prova)

1. **Trocar as fórmulas de $M_x$ e $M_y$:**
   - *Erro fatal:* Escrever $M_x = \iint_D x\rho\,dA$.
   - *Como nunca errar:* Pense diretamente na coordenada do centro de massa: $\bar{x}$ tem que ter $x$ dentro da integral ($\bar{x} = \frac{1}{m}\iint_D x\rho\,dA = \frac{M_y}{m}$) e $\bar{y}$ tem que ter $y$ dentro da integral ($\bar{y} = \frac{1}{m}\iint_D y\rho\,dA = \frac{M_x}{m}$). O mesmo vale para inércia: $I_x$ usa a distância ao eixo $x$, que é $y^2$, e $I_y$ usa $x^2$.
2. **Esquecer de dividir pela massa $m$:**
   - Muitos alunos calculam $M_y$ e $M_x$ com perfeição e entregam $(M_y, M_x)$ como resposta do centro de massa, esquecendo de dividir por $m$.
3. **Cometer erro na potência de $r$ em Coordenadas Polares:**
   - Ao calcular $\bar{x}$ ou $\bar{y}$ em polares, lembre-se de que $x = r\cos\theta$ já traz um $r$ e o diferencial $dA = r\,dr\,d\theta$ traz **outro** $r$. Se $\rho = 1$ (centroide), o integrando tem $r^2$, e não $r$!
4. **Usar simetria da região $D$ sem checar a simetria da densidade $\rho(x,y)$:**
   - Uma região $D$ pode ser perfeitamente simétrica em relação ao eixo $y$ (ex.: semidisco superior $x^2+y^2 \le a^2, y \ge 0$), mas se a densidade for $\rho(x,y) = 1 + x + y$ (que não é par em $x$), a metade direita é mais pesada que a esquerda, e portanto $\bar{x} \ne 0$! Só use simetria se **tanto $D$ quanto $\rho$** forem simétricos.
5. **Errar os limites de integração em probabilidade conjunta quando o evento é uma desigualdade acoplada:**
   - No Exemplo 7 do Stewart, pede-se $P(X + Y < 20)$ com $X \ge 0, Y \ge 0$. A região $D$ não é um quadrado $[0,20]\times[0,20]$, mas sim o **triângulo** $0 \le x \le 20$, $0 \le y \le 20 - x$. Desenhe sempre a região do evento antes de integrar $f(x,y)$!
