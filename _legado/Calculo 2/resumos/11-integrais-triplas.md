# 15.7 Integrais Triplas

> Somas triplas de Riemann, Teorema de Fubini em caixas retangulares, regiões sólidas gerais (Tipos I, II e III), mudança na ordem de integração, cálculo de volumes, massa, centro de massa (centroide) e momentos de inércia · Stewart 15.7 · Lista 6 UFPE (2026.1) · 3ª unidade

---

## 1. Definição Formal e o Teorema de Fubini em Caixas

Seja $f(x,y,z)$ uma função definida em uma **caixa retangular** (paralelepípedo reto) compacta:
$$B = [a,b] \times [c,d] \times [r,s] = \{(x,y,z) \in \mathbb{R}^3 \mid a \le x \le b,\; c \le y \le d,\; r \le z \le s\}$$

Subdividindo $[a,b]$ em $l$ subintervalos de largura $\Delta x$, $[c,d]$ em $m$ subintervalos de largura $\Delta y$, e $[r,s]$ em $n$ subintervalos de largura $\Delta z$, obtemos $lmn$ subcaixas $B_{ijk}$ de volume $\Delta V = \Delta x\,\Delta y\,\Delta z$.

> **Definição (Integral Tripla de Riemann).** A **integral tripla** de $f$ sobre a caixa $B$ é
> $$\iiint_B f(x,y,z)\,dV = \lim_{l,m,n \to \infty} \sum_{i=1}^l \sum_{j=1}^m \sum_{k=1}^n f(x_{ijk}^*, y_{ijk}^*, z_{ijk}^*)\,\Delta V$$
> se este limite existir.
>
> **Condição Suficiente de Integrabilidade (citar na prova):** Se $f$ é **contínua** no compacto $B$ (ou limitada e contínua exceto num conjunto de fronteira suave de volume nulo), então $f$ é integrável em $B$.

> **Teorema de Fubini para Integrais Triplas.** Se $f(x,y,z)$ é **contínua** na caixa retangular $B = [a,b] \times [c,d] \times [r,s]$, então a integral tripla pode ser calculada como uma integral iterada em **qualquer uma das $3! = 6$ ordens possíveis** de integração:
> $$\iiint_B f(x,y,z)\,dV = \int_r^s \int_c^d \int_a^b f(x,y,z)\,dx\,dy\,dz = \int_a^b \int_r^s \int_c^d f(x,y,z)\,dy\,dz\,dx = \dots$$

**Caso particular de variáveis separáveis na caixa:** Se $B = [a,b] \times [c,d] \times [r,s]$ e $f(x,y,z) = g(x)h(y)k(z)$, então:
$$\iiint_B g(x)h(y)k(z)\,dV = \left(\int_a^b g(x)\,dx\right)\left(\int_c^d h(y)\,dy\right)\left(\int_r^s k(z)\,dz\right)$$
*(Atenção: só vale quando os limites das três variáveis são **constantes** e o integrando é um **produto puro**!)*

---

## 2. Integrais Triplas sobre Sólidos Gerais: Tipos I, II e III

Para integrar sobre um sólido limitado $E \subset \mathbb{R}^3$, reduzimos a integral tripla a uma **integral simples interna** (que varre uma reta paralela a um dos eixos coordenados de uma superfície de entrada até uma superfície de saída) seguida de uma **integral dupla externa** sobre a **projeção ortogonal (sombra) $D$** do sólido num plano coordenado.

### Classificação dos Sólidos Elementares

| Tipo do Sólido | Eixo da 1ª Integração (Interna) | Limites da 1ª Integração (Superfície a Superfície) | Plano da Projeção $D$ | Fórmula de Redução ($\iiint_E f\,dV =$) |
|---|---|---|---|---|
| **Tipo I** ($xy$-projetável) | Eixo $z$ (de **baixo** p/ **cima**) | $u_1(x,y) \le z \le u_2(x,y)$ | Plano $xy$ ($z=0$) | $\iint_{D_{xy}} \left[\int_{u_1(x,y)}^{u_2(x,y)} f(x,y,z)\,dz\right] dA$ |
| **Tipo II** ($yz$-projetável) | Eixo $x$ (de **trás** p/ **frente**) | $u_1(y,z) \le x \le u_2(y,z)$ | Plano $yz$ ($x=0$) | $\iint_{D_{yz}} \left[\int_{u_1(y,z)}^{u_2(y,z)} f(x,y,z)\,dx\right] dA$ |
| **Tipo III** ($xz$-projetável) | Eixo $y$ (da **esquerda** p/ **direita**) | $u_1(x,z) \le y \le u_2(x,z)$ | Plano $xz$ ($y=0$) | $\iint_{D_{xz}} \left[\int_{u_1(x,z)}^{u_2(x,z)} f(x,y,z)\,dy\right] dA$ |

Depois de reduzir a integral tripla à integral dupla sobre $D$, descrevemos a região plana $D$ como **Tipo I ou Tipo II bidimensional** (ou em **coordenadas polares** naquele plano coordenado!).

Por exemplo, para um **Sólido Tipo I** cuja projeção $D_{xy}$ é plana do Tipo I ($a \le x \le b$, $g_1(x) \le y \le g_2(x)$):
$$\iiint_E f(x,y,z)\,dV = \int_a^b \int_{g_1(x)}^{g_2(x)} \int_{u_1(x,y)}^{u_2(x,y)} f(x,y,z)\,dz\,dy\,dx$$

> **Regra de Ouro da Estrutura dos Limites:**
> 1. **Integral de dentro** (ex.: $dz$): limites dependem de **no máximo 2 variáveis** $(x,y)$ — são equações de **superfícies** em 3D.
> 2. **Integral do meio** (ex.: $dy$): limites dependem de **no máximo 1 variável** $(x)$ — são equações de **curvas** na projeção 2D.
> 3. **Integral de fora** (ex.: $dx$): limites são **obrigatoriamente constantes** $[a,b]$ — é o intervalo numérico que varre a projeção.

---

## 3. Como Enxergar e Desenhar o Sólido 3D e sua Projeção 2D

Na prova do Prof. Henrique Araújo (e na Lista 6 da UFPE), **o esboço do sólido $E$ e da projeção $D$ é obrigatório**. Nunca tente escrever limites de integração no escuro! Siga sempre o **Método dos Dois Desenhos**:

### Passo a Passo para o Esboço e Montagem (Receita de Prova)

1. **Identifique as superfícies fronteira do enunciado:**
   - **Planos:** $ax + by + cz = d$. Se falta uma variável (ex.: $x + 2y = 2$ ou $z = 1 - x$), é umplano paralelo ao eixo da variável ausente! Para desenhar um plano oblíquo como $x + y + 2z = 2$ no 1º octante, marque os **três interceptos nos eixos** fazendo duas variáveis zero de cada vez: $(2,0,0)$, $(0,2,0)$ e $(0,0,1)$, e ligue-os formando um triângulo (tetraedro com a origem).
   - **Cilindros parabólicos ou circulares:** Equações com apenas **duas variáveis** em $\mathbb{R}^3$ (ex.: $y = x^2$, $z = 1 - x^2$, $x^2 + z^2 = 4$). Desenhe a curva no plano das duas variáveis e "arraste-a" paralelamente ao eixo da variável que não aparece na equação.
   - **Paraboloides e Cones:** Se o eixo do paraboloide/cone é o eixo $y$ (ex.: $y = x^2 + z^2$, Exemplo 3 do Stewart e Questão 4b da Lista 6) ou o eixo $x$ (ex.: $x = y^2 + z^2$, Questão 5 da Lista 6), **escolha o Tipo do sólido alinhado com o eixo do paraboloide!**
     - Paraboloide $z = x^2 + y^2 \implies$ **Tipo I** (integra em $z$ primeiro, projeta no plano $xy$).
     - Paraboloide $y = x^2 + z^2 \implies$ **Tipo III** (integra em $y$ primeiro, projeta no plano $xz$).
     - Paraboloide $x = y^2 + z^2 \implies$ **Tipo II** (integra em $x$ primeiro, projeta no plano $yz$).

2. **Faça o Desenho 1 (Sólido 3D) e trace uma seta de varredura:**
   - Se escolheu Tipo I, trace uma seta vertical (paralela ao eixo $z$) subindo por dentro do sólido.
   - Onde o pé da seta entra no sólido é o **piso** $z = u_1(x,y)$.
   - Onde a ponta da seta sai do sólido é o **teto** $z = u_2(x,y)$.
   - *Atenção:* Se o "teto" ou o "piso" muda de fórmula no meio do caminho (duas superfícies diferentes cobrindo partes diferentes do sólido), você **precisa dividir o sólido em dois ($E = E_1 \cup E_2$)** ou mudar para outro Tipo (II ou III) onde uma única superfície seja entrada e uma única seja saída!

3. **Como encontrar a Projeção 2D ($D$) com segurança algébrica:**
   - A borda da projeção $D$ vem de duas fontes:
     1. **Paredes cilíndricas verticais** já dadas no enunciado (ex.: cilindro $x^2 + y^2 = 4$ ou plano vertical $x = 2y$).
     2. **A curva de interseção entre o teto e o piso:** iguale $u_1(x,y) = u_2(x,y)$ (eliminando $z$) para achar a sombra da "costura" onde as duas superfícies se fecham!
   - *Exemplo clássico (Stewart Ex. 3):* Sólido entre o paraboloide $y = x^2 + z^2$ e o plano $y = 4$.
     - Usando **Tipo III** (seta paralela ao eixo $y$): entra em $y = x^2 + z^2$ e sai em $y = 4$.
     - Qual é a projeção $D_{xz}$ no plano $xz$? Igualamos entrada e saída: $x^2 + z^2 = 4$, que é o **disco fechado de raio $2$ no plano $xz$**!

4. **Faça o Desenho 2 (Projeção 2D isolada no plano coordenado):**
   - Desenhe os dois eixos do plano da projeção (cuidado com os rótulos dos eixos: plano $xy$, $yz$ ou $xz$!).
   - Use **linha cheia** para fronteiras incluídas ($\le$) e **hachure** o interior de $D$.
   - A partir desse desenho 2D plano, retire os dois últimos limites de integração (ou aplique coordenadas polares no plano da projeção: ex., no plano $xz$, $x = r\cos\theta$, $z = r\sin\theta$, $dA = r\,dr\,d\theta$).

---

## 4. Mudança na Ordem de Integração (e Descrição nos 3 Tipos)

Questões clássicas de prova (como Stewart Ex. 4 e Lista 6 Questões 3a e 6a) dão uma integral iterada pronta ou um sólido e pedem para **reescrever nas outras ordens (Tipos I, II e III)**.

**Algoritmo infalível (Via Projeções nos 3 Planos Coordenados):**
1. **Extraia as inequações atuais** lendo os limites de fora para dentro:
   $$\int_0^1 \int_0^{x^2} \int_0^y f(x,y,z)\,dz\,dy\,dx \implies \begin{cases} 0 \le x \le 1 \\ 0 \le y \le x^2 \\ 0 \le z \le y \end{cases}$$
2. **Liste todas as superfícies fronteira** trocando $\le$ por $=$:
   - Planos $x = 0$, $x = 1$; cilindro parabólico $y = x^2$ (com $y=0$); planos $z = 0$ e $z = y$.
3. **Desenhe as 3 projeções ortogonais ($D_{xy}$, $D_{yz}$, $D_{xz}$):**
   - **Em $D_{xy}$:** ignore $z$ (pois $0 \le z \le y$ só exige $y \ge 0$). Temos $0 \le x \le 1$ e $0 \le y \le x^2$ (ou $0 \le y \le 1$ e $\sqrt{y} \le x \le 1$).
   - **Em $D_{yz}$:** como $z \le y$ e $y \le x^2 \le 1$, o triângulo projetado no plano $yz$ é $0 \le y \le 1$, $0 \le z \le y$ (ou $0 \le z \le 1$, $z \le y \le 1$). Para cada $(y,z)$ nesse triângulo, $x$ vai da superfície de trás $x = \sqrt{y}$ até o plano da frente $x = 1$.
   - **Em $D_{xz}$:** combinando $0 \le z \le y \le x^2$, vemos que $z$ varia de $0$ até a curva $z = x^2$ (com $0 \le x \le 1$). Para cada $(x,z)$ nessa região, $y$ entra pelo plano $y = z$ e sai pelo cilindro parabólico $y = x^2$.

---

## 5. Aplicações Geométricas e Físicas de Integrais Triplas

Seja $E \subset \mathbb{R}^3$ um sólido compacto com função densidade volumétrica contínua $\rho(x,y,z)$ (ou $\delta(x,y,z)$ na notação da Lista 6 UFPE), medida em massa por unidade de volume.

| Grandeza Geométrica / Física | Fórmula Integral | Observação / Significado |
|---|---|---|
| **Volume do Sólido $E$** | $V(E) = \iiint_E 1\,dV$ | Reduz-se a $\iint_D [u_2(x,y) - u_1(x,y)]\,dA$ no Tipo I. |
| **Valor Médio de $f$ em $E$** | $f_{\text{méd}} = \frac{1}{V(E)} \iiint_E f(x,y,z)\,dV$ | Cobrado na Lista 6 (Questão 8-ii). |
| **Massa Total ($m$)** | $m = \iiint_E \rho(x,y,z)\,dV$ | Se a densidade é constante ($\rho = c$), $m = c \cdot V(E)$. |
| **Momento em relação ao plano $yz$** | $M_{yz} = \iiint_E x\,\rho(x,y,z)\,dV$ | Mede o balanço de massa usando a coordenada $x$ (distância com sinal ao plano $yz$, $x=0$). |
| **Momento em relação ao plano $xz$** | $M_{xz} = \iiint_E y\,\rho(x,y,z)\,dV$ | Usa a coordenada $y$ (distância com sinal ao plano $xz$, $y=0$). |
| **Momento em relação ao plano $xy$** | $M_{xy} = \iiint_E z\,\rho(x,y,z)\,dV$ | Usa a coordenada $z$ (distância com sinal ao plano $xy$, $z=0$). |
| **Centro de Massa $(\bar{x}, \bar{y}, \bar{z})$** | $\bar{x} = \frac{M_{yz}}{m}, \quad \bar{y} = \frac{M_{xz}}{m}, \quad \bar{z} = \frac{M_{xy}}{m}$ | Se $\rho$ é constante, chama-se **Centroide** (independe de $\rho$). |
| **Momento de Inércia no eixo $x$ ($I_x$)** | $I_x = \iiint_E (y^2 + z^2)\,\rho(x,y,z)\,dV$ | $y^2 + z^2$ é o quadrado da distância do ponto $(x,y,z)$ ao **eixo $x$**. |
| **Momento de Inércia no eixo $y$ ($I_y$)** | $I_y = \iiint_E (x^2 + z^2)\,\rho(x,y,z)\,dV$ | $x^2 + z^2$ é o quadrado da distância ao **eixo $y$**. |
| **Momento de Inércia no eixo $z$ ($I_z$)** | $I_z = \iiint_E (x^2 + y^2)\,\rho(x,y,z)\,dV$ | $x^2 + y^2$ é o quadrado da distância ao **eixo $z$**. |
| **Carga Elétrica Total ($Q$)** | $Q = \iiint_E \sigma(x,y,z)\,dV$ | Onde $\sigma(x,y,z)$ é a densidade volumétrica de carga. |
| **Probabilidade Conjunta 3D** | $P((X,Y,Z) \in E) = \iiint_E f(x,y,z)\,dV$ | Com $f \ge 0$ e $\int_{-\infty}^\infty \int_{-\infty}^\infty \int_{-\infty}^\infty f\,dV = 1$. |

### Atalho de Ouro: Uso de Simetria em Provas!
Antes de calcular $M_{yz}$, $M_{xz}$ ou $M_{xy}$, verifique se o sólido $E$ e a densidade $\rho$ possuem **simetria em relação a um plano coordenado**:
- Se $E$ é simétrico em relação ao plano $xz$ (isto é, se $(x,y,z) \in E \iff (x,-y,z) \in E$) e $\rho(x,-y,z) = \rho(x,y,z)$ (função par em $y$), então o integrando $y\,\rho(x,y,z)$ é **ímpar em $y$**, logo:
  $$M_{xz} = 0 \implies \bar{y} = 0$$
- **Justificativa obrigatória na prova:** *"Como o sólido $E$ é simétrico em relação ao plano $xz$ e a função densidade $\rho$ é par em $y$, o integrando $y\,\rho(x,y,z)$ é uma função ímpar de $y$ em um intervalo simétrico, resultando em $M_{xz} = 0$ e $\bar{y} = 0$."*

---

## 6. Erros que Custam Ponto na Prova do Prof. Henrique Araújo

| Erro Clássico | Por que acontece | Como fazer certo na prova |
|---|---|---|
| **Trocar os índices dos momentos estáticos ($M_{yz}, M_{xz}, M_{xy}$)** | Confundir com integrais duplas ($M_y$ e $M_x$). | Em 3D os momentos são em relação aos **planos coordenados**: para achar $\bar{x}$, você integra a letra que **falta** no nome do plano ($M_{yz} = \iiint x\,\rho\,dV$). Dica mnemônica: $\bar{x} \leftrightarrow x \leftrightarrow M_{yz}$. |
| **Trocar a fórmula do momento de inércia ($I_x, I_y, I_z$)** | Usar apenas uma variável ao quadrado em vez da soma das outras duas. | A distância ao quadrado até um eixo em $\mathbb{R}^3$ soma as **outras duas variáveis ao quadrado**: $I_x$ leva $(y^2+z^2)$, $I_y$ leva $(x^2+z^2)$, $I_z$ leva $(x^2+y^2)$. |
| **Deixar variáveis nos limites externos ou variáveis já integradas nos limites de fora** | Integrar primeiro em $z$, mas deixar a letra $z$ aparecer nos limites da integral do meio ou de fora. | Uma vez que uma variável foi integrada (ex.: $dz$), **ela morre**! Ela jamais pode reaparecer nos limites das integrais externas seguintes. |
| **Projetar no plano errado sem eliminar a 1ª variável** | Em um tetraedro $x+y+2z=2$, tomar o limite de $y$ como $2-x-2z$ na segunda integral. |Na projeção no plano $xy$, fazemos $z=0$ na interseção com o piso! Assim a reta fronteira em $D_{xy}$ é $x+y=2 \implies y = 2-x$ (sem $z$!). |
| **Não citar Fubini / Continuidade nem desenhar o sólido e a projeção** | Ir direto para as contas algébricas. | Desenhe sempre os **dois gráficos** (o sólido $E$ em 3D indicando a superfície superior/inferior e a projeção $D$ em 2D) e escreva: *"Como $f$ é contínua no sólido compacto $E$ de Tipo I, pelo Teorema de Fubini..."* |
