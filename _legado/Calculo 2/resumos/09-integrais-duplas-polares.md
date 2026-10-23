# 15.4 Integrais Duplas em Coordenadas Polares

> Referência · 3ª unidade · Stewart 15.4 (com base em 10.3–10.4) · Lista 5 UFPE (2026.1)

---

## 1. Contexto e Motivação

Muitas integrais duplas $\iint_R f(x,y)\,dA$ tornam-se extremamente trabalhosas ou até analiticamente impossíveis em coordenadas retangulares cartesianas $(x,y)$. Isso ocorre tipicamente em duas situações:
1. **A região de integração $R$ possui simetria circular ou radial** (discos, anéis concêntricos, setores circulares, círculos deslocados tangentes aos eixos, ou curvas polares clássicas como rosáceas, cardioides e limaçons).
2. **O integrando contém a expressão $x^2 + y^2$** (por exemplo, $\sqrt{a^2 - x^2 - y^2}$, $e^{-(x^2+y^2)}$, $\ln(x^2+y^2)$, $\frac{1}{(1+x^2+y^2)^2}$), cuja primitiva em $x$ ou $y$ isolado não é elementar ou exige substituições trigonométricas longas.

As **coordenadas polares** $(r, \theta)$ mapeiam cada ponto do plano através da distância radial $r \ge 0$ até a origem (polo) e do ângulo polar $\theta$ medido no sentido anti-horário a partir do semieixo $x$ positivo (eixo polar).

---

## 2. Definições e Teoremas Formais

### 2.1 Equações de Transformação Polar
Para qualquer ponto $(x,y) \in \mathbb{R}^2$:
$$x = r\cos\theta, \qquad y = r\sin\theta$$
$$r^2 = x^2 + y^2 \implies r = \sqrt{x^2 + y^2}, \qquad \tan\theta = \frac{y}{x} \quad (x \neq 0)$$

Na parametrização de regiões de integração em Cálculo 2, adotamos sempre **$r \ge 0$** e $\theta$ variando em um intervalo $[\alpha, \beta]$ de amplitude máxima $2\pi$ (tipicamente $[0, 2\pi]$ ou $[-\pi, \pi]$).

### 2.2 O Elemento Diferencial de Área e Dedução via Somas de Riemann / Jacobiano
Considere um **retângulo polar** $R = \{(r,\theta) \mid a \le r \le b, \; \alpha \le \theta \le \beta\}$ subdividido em pequenos sub-retângulos polares $R_{ij} = [r_{i-1}, r_i] \times [\theta_{j-1}, \theta_j]$ de larguras $\Delta r = r_i - r_{i-1}$ e $\Delta\theta = \theta_j - \theta_{j-1}$:
- A área de um setor circular de raio $r$ e abertura $\Delta\theta$ é $\frac{1}{2}r^2\Delta\theta$.
- Subtraindo o setor interno do externo, a área exata do sub-retângulo polar $R_{ij}$ é:
  $$\Delta A_i = \frac{1}{2}r_i^2\Delta\theta - \frac{1}{2}r_{i-1}^2\Delta\theta = \frac{1}{2}(r_i + r_{i-1})(r_i - r_{i-1})\Delta\theta = r_i^* \Delta r\,\Delta\theta$$
  onde $r_i^* = \frac{1}{2}(r_{i-1} + r_i)$ é o raio médio.
- Passando ao limite infinitesimal ($\Delta r \to dr$, $\Delta\theta \to d\theta$), o "retângulo polar infinitesimal" tem lados ortogonais de comprimentos $dr$ (radial) e $r\,d\theta$ (arco circular transversal), resultando no **elemento de área polar**:
  $$dA = r\,dr\,d\theta$$

Pelo **Teorema da Mudança de Variáveis** (Stewart 15.10), esse fator $r$ é o módulo do determinante Jacobiano da transformação $T(r,\theta) = (r\cos\theta, r\sin\theta)$:
$$\frac{\partial(x,y)}{\partial(r,\theta)} = \begin{vmatrix} \frac{\partial x}{\partial r} & \frac{\partial x}{\partial \theta} \\ \frac{\partial y}{\partial r} & \frac{\partial y}{\partial \theta} \end{vmatrix} = \begin{vmatrix} \cos\theta & -r\sin\theta \\ \sin\theta & r\cos\theta \end{vmatrix} = r\cos^2\theta + r\sin^2\theta = r$$
Como $r \ge 0$, temos $\left|\frac{\partial(x,y)}{\partial(r,\theta)}\right| = r$, logo $dA = dx\,dy = r\,dr\,d\theta$.

### 2.3 Teorema 1: Mudança para Coordenadas Polares em um Retângulo Polar (Stewart 15.4.2)
> **Enunciado:** Se $f(x,y)$ é uma função **contínua** no retângulo polar $R$ dado por $0 \le a \le r \le b$, $\alpha \le \theta \le \beta$, onde $0 \le \beta - \alpha \le 2\pi$, então:
> $$\iint_R f(x,y)\,dA = \int_\alpha^\beta \int_a^b f(r\cos\theta, r\sin\theta)\,r\,dr\,d\theta$$

### 2.4 Teorema 2: Regiões Polares Gerais / Simples Radicalmente (Stewart 15.4.3)
> **Enunciado:** Se $f(x,y)$ é **contínua** em uma região polar $D$ da forma
> $$D = \big\{ (r, \theta) \;\big|\; \alpha \le \theta \le \beta, \; h_1(\theta) \le r \le h_2(\theta) \big\}$$
> onde $0 \le \beta - \alpha \le 2\pi$ e $h_1, h_2$ são funções contínuas em $[\alpha, \beta]$ tais que $0 \le h_1(\theta) \le h_2(\theta)$, então:
> $$\iint_D f(x,y)\,dA = \int_\alpha^\beta \int_{h_1(\theta)}^{h_2(\theta)} f(r\cos\theta, r\sin\theta)\,r\,dr\,d\theta$$

> **Como citar na prova do Prof. Henrique Araújo:**
> *"Como $f(x,y)$ é contínua na região compacta $D$, aplicamos o Teorema da Mudança de Variáveis para Coordenadas Polares (com Jacobiano $\left|\frac{\partial(x,y)}{\partial(r,\theta)}\right| = r$) combinado ao Teorema de Fubini..."*

---

## 3. Como Enxergar e Desenhar a Região 2D (Ponto Crítico de Prova)

> **Regra de Ouro da Disciplina:** *Desenho primeiro, limites depois!* Na correção do professor Henrique Araújo, montar os limites de integração sem esboçar a região $D$ e descrever suas fronteiras custa pontos preciosos.

### 3.1 O Método da Semirreta Radial ("Tiro a partir da Origem")
Para determinar sem erro os limites de integração $h_1(\theta) \le r \le h_2(\theta)$ e $\alpha \le \theta \le \beta$:
1. **Esboce a região $D$ no plano $xy$** (use linha cheia para fronteiras fechadas $\le, \ge$ e linha tracejada para abertas $<, >$).
2. **Dispare uma semirreta radial** partindo da origem $O(0,0)$ num ângulo genérico $\theta$ que atravesse a região $D$:
   - **Onde a semirreta ENTRA na região sombreada?** Essa curva define o limite inferior $r_{\text{in}} = h_1(\theta)$. *(Dica: se o polo $(0,0)$ está dentro da região ou na sua borda inicial, então $r_{\text{in}} = 0$).*
   - **Onde a semirreta SAI da região sombreada?** Essa curva define o limite superior $r_{\text{out}} = h_2(\theta)$.
3. **Varra o feixe de semirretas no sentido anti-horário:**
   - Qual é o **menor ângulo $\alpha$** em que a semirreta toca o início da região?
   - Qual é o **maior ângulo $\beta$** em que a semirreta deixa a região?
   *(Atenção: se a curva de entrada $h_1(\theta)$ ou de saída $h_2(\theta)$ mudar ao longo da varredura, divida a região $D$ em sub-regiões $D_1 \cup D_2$ pelo raio de transição $\theta = \theta_{\text{interseção}}$!).*

### 3.2 Catálogo de Reconhecimento de Curvas Polares Clássicas (Stewart + Lista 5 UFPE)

| Equação Polar | Equação Cartesiana | Geometria e Pontos-Chave para o Esboço | Intervalo Angular Natural |
|---|---|---|---|
| **$r = R$** | $x^2 + y^2 = R^2$ | Círculo centrado na origem $(0,0)$ de raio $R$. | $\theta \in [0, 2\pi]$ |
| **$r = 2a\cos\theta$** | $(x - a)^2 + y^2 = a^2$ | **Círculo deslocado no eixo $x$**: centro em $(a,0)$ e raio $|a|$. Tangencia o eixo $y$ na origem $(0,0)$ e atinge $(2a,0)$ em $\theta = 0$. Fica nos quadrantes I e IV (se $a>0$). | **$\theta \in [-\pi/2, \pi/2]$** *(No 1º quadrante: $[0, \pi/2]$)* |
| **$r = 2a\sin\theta$** | $x^2 + (y - a)^2 = a^2$ | **Círculo deslocado no eixo $y$**: centro em $(0,a)$ e raio $|a|$. Tangencia o eixo $x$ na origem $(0,0)$ e atinge $(0,2a)$ em $\theta = \pi/2$. Fica nos quadrantes I e II (se $a>0$). | **$\theta \in [0, \pi]$** *(No 1º quadrante: $[0, \pi/2]$)* |
| **$r = a(1 \pm \cos\theta)$** ou **$a(1 \pm \sin\theta)$** | Cardioide | Curva em formato de coração com **cúspide na origem** ($r=0$). Para $r = a(1+\cos\theta)$: passa por $(2a,0)$ em $\theta=0$, $(0, \pm a)$ em $\theta=\pm\pi/2$ e $(0,0)$ em $\theta=\pi$. | $\theta \in [0, 2\pi]$ ou $[-\pi, \pi]$ |
| **$r = c + b\cos\theta$** ($c > b > 0$) | Limaçon sem laço | Semelhante à cardioide, mas **não passa pela origem** ($r_{\min} = c - b > 0$ em $\theta = \pi$; $r_{\max} = c + b$ em $\theta = 0$). Ex.: $r = 3 + 2\cos\theta$ (Lista 5, Q5 e Q6c). | $\theta \in [0, 2\pi]$ ou $[-\pi, \pi]$ |
| **$r = a\cos(n\theta)$** | Rosácea (simétrica ao eixo $x$) | Se $n$ é **ímpar**: $n$ pétalas. Se $n$ é **par**: $2n$ pétalas de comprimento $a$. A 1ª pétala está centrada em $\theta = 0$ e fecha onde $\cos(n\theta) = 0 \implies n\theta = \pm\pi/2$. | **1 pétala central:** $\theta \in \left[-\frac{\pi}{2n}, \frac{\pi}{2n}\right]$ |
| **$r = a\sin(n\theta)$** | Rosácea | Mesmo número de pétalas ($n$ se ímpar, $2n$ se par). A 1ª pétala no 1º quadrante começa em $\theta = 0$, tem pico em $\theta = \frac{\pi}{2n}$ e fecha em $n\theta = \pi$. | **1ª pétala:** $\theta \in \left[0, \frac{\pi}{n}\right]$ |
| **$\theta = \theta_0$** | $y = (\tan\theta_0)\,x$ | Semirreta radial partindo da origem com inclinação $\tan\theta_0$ (ex.: $y = x$ no 1ºQ $\iff \theta = \pi/4$; $y = \sqrt{3}x \iff \theta = \pi/3$). | $\theta = \theta_0$ (constante) |
| **$r = c\sec\theta$** | $x = c$ | Reta vertical $x = c \implies r\cos\theta = c \implies r = \frac{c}{\cos\theta} = c\sec\theta$. | $\theta \in (-\pi/2, \pi/2)$ |
| **$r = c\csc\theta$** | $y = c$ | Reta horizontal $y = c \implies r\sin\theta = c \implies r = \frac{c}{\sin\theta} = c\csc\theta$. | $\theta \in (0, \pi)$ |

### 3.3 Como Desenhar uma Rosácea Passo a Passo (Ex.: $r = a\cos(2\theta)$, Lista 5 Q5, Q6a, Q9)
1. **Número de pétalas:** Como $n = 2$ é par, há $2n = 4$ pétalas de comprimento máximo $r = a$, igualmente espaçadas de $\frac{2\pi}{4} = \frac{\pi}{2}$ ($90^\circ$).
2. **Picos das pétalas ($\cos(2\theta) = \pm 1$):** Ocorrem nos eixos coordenados: $\theta = 0, \frac{\pi}{2}, \pi, \frac{3\pi}{2}$.
3. **Tangentes no polo ($r = 0$):** Resolva $\cos(2\theta) = 0 \implies 2\theta = \pm\frac{\pi}{2}, \pm\frac{3\pi}{2} \implies \theta = \pm\frac{\pi}{4}, \pm\frac{3\pi}{4}$ (as bissetrizes $y = \pm x$ delimitam cada pétala!).
4. **Região de 1 laço (pétala da direita):** $0 \le r \le a\cos(2\theta)$ com $-\frac{\pi}{4} \le \theta \le \frac{\pi}{4}$ (ou no 1º quadrante: $0 \le \theta \le \frac{\pi}{4}$).

---

## 4. Aplicações Geométricas Diretas: Áreas e Volumes

### 4.1 Área de uma Região Polar (Stewart 15.4)
Fazendo $f(x,y) = 1$ no Teorema 15.4.3, a área plana de $D = \{(r,\theta) \mid \alpha \le \theta \le \beta, \; h_1(\theta) \le r \le h_2(\theta)\}$ é:
$$\text{Área}(D) = \iint_D 1\,dA = \int_\alpha^\beta \int_{h_1(\theta)}^{h_2(\theta)} r\,dr\,d\theta = \int_\alpha^\beta \left[\frac{r^2}{2}\right]_{h_1(\theta)}^{h_2(\theta)} d\theta = \frac{1}{2}\int_\alpha^\beta \Big([h_2(\theta)]^2 - [h_1(\theta)]^2\Big)\,d\theta$$
*(Nota: quando $h_1(\theta) = 0$ e $h_2(\theta) = h(\theta)$, recuperamos a fórmula $\text{Área} = \frac{1}{2}\int_\alpha^\beta [h(\theta)]^2\,d\theta$ da Seção 10.4).*

### 4.2 Volume entre Duas Superfícies Espaciais
Se um sólido $E \subset \mathbb{R}^3$ é limitado superiormente pelo gráfico de $z = z_{\text{sup}}(x,y)$ e inferiormente por $z = z_{\text{inf}}(x,y)$ sobre uma projeção polar $D$ no plano $xy$ (onde $z_{\text{sup}} \ge z_{\text{inf}}$ em $D$), então:
$$V(E) = \iint_D \big(z_{\text{sup}}(x,y) - z_{\text{inf}}(x,y)\big)\,dA = \int_\alpha^\beta \int_{h_1(\theta)}^{h_2(\theta)} \big(z_{\text{sup}}(r\cos\theta, r\sin\theta) - z_{\text{inf}}(r\cos\theta, r\sin\theta)\big)\,r\,dr\,d\theta$$
- **Interseção de superfícies de revolução** (ex.: paraboloide $z = 4 - x^2 - y^2$ e cone $z = \sqrt{x^2+y^2}$): projete a curva de interseção no plano $xy$ igualando $z_{\text{sup}} = z_{\text{inf}}$ já em função de $r$ ($4 - r^2 = r$) para achar o raio do disco base $D$!

---

## 5. Receita Passo a Passo para Resolver Questões de Prova

### Passo 1 — Diagnóstico ou Conversão Cartesiana $\to$ Polar
- Se a questão dá $\iint_D f(x,y)\,dA$ descrita em palavras: desenhe $D$ e converta as equações das curvas substituindo $x = r\cos\theta$, $y = r\sin\theta$ e $x^2+y^2 = r^2$.
- Se a questão pede para **converter uma integral iterada cartesiana** $\int_a^b \int_{g_1(x)}^{g_2(x)} f(x,y)\,dy\,dx$ para polares:
  1. Extraia as inequações $a \le x \le b$ e $g_1(x) \le y \le g_2(x)$.
  2. Reescreva as equações $y = g_1(x)$ e $y = g_2(x)$ eliminando os radicais (ex.: $y = \sqrt{2x - x^2} \iff x^2 + y^2 - 2x = 0$ com $y \ge 0 \iff (x-1)^2 + y^2 = 1$, semicírculo superior!).
  3. **Desenhe a região $D$** e releia os limites usando a semirreta radial.

### Passo 2 — Cálculo dos Ângulos de Interseção (Quando há 2 curvas)
Se $D$ é limitada por $r = h_1(\theta)$ e $r = h_2(\theta)$, iguale $h_1(\theta) = h_2(\theta)$ para encontrar os ângulos $\alpha$ e $\beta$ onde as curvas se cruzam:
- *Exemplo clássico (Lista 5, Q6b):* Fora de $(x-1)^2 + y^2 = 1 \iff r = 2\cos\theta$ e dentro de $x^2 + y^2 = 4 \iff r = 2$ (ou dois círculos $r = 1$ e $r = 2\cos\theta$). Igualando $2\cos\theta = 1 \implies \cos\theta = \frac{1}{2} \implies \theta = \pm\frac{\pi}{3}$.

### Passo 3 — Montagem da Integral Dupla com Justificativa Teórica
1. Cite a continuidade de $f$ em $D$ e o **Teorema da Mudança de Variáveis em Coordenadas Polares**.
2. Substitua $x = r\cos\theta$, $y = r\sin\theta$, $x^2+y^2 = r^2$ e **$dA = r\,dr\,d\theta$**.
3. Verifique se é possível usar **simetria** (com justificativa formal de paridade) para simplificar ou zerar parcelas do integrando!

### Passo 4 — Integração Interna (em $r$) e Externa (em $\theta$) sem Pular Passos
- Na integral em $\theta$, **nunca pule identidades trigonométricas** (exigência estrita de correção!):
  $$\cos^2\theta = \frac{1 + \cos(2\theta)}{2}, \qquad \sin^2\theta = \frac{1 - \cos(2\theta)}{2}, \qquad \sin\theta\cos\theta = \frac{\sin(2\theta)}{2}$$
  $$\cos^4\theta = \left(\frac{1+\cos(2\theta)}{2}\right)^2 = \frac{1}{4}\left(1 + 2\cos(2\theta) + \frac{1+\cos(4\theta)}{2}\right) = \frac{3}{8} + \frac{1}{2}\cos(2\theta) + \frac{1}{8}\cos(4\theta)$$
- Para potências ímpares ($\cos^3\theta$ ou $\sin^3\theta$), isole um fator e use $\cos^2\theta = 1 - \sin^2\theta$:
  $$\int \cos^3\theta\,d\theta = \int (1 - \sin^2\theta)\cos\theta\,d\theta = \sin\theta - \frac{\sin^3\theta}{3} + C$$

---

## 6. Exemplo Resolvido Completo no Padrão de Prova (N4)

**Problema (Inspirado em Stewart 15.4 Ex. 4 e Lista 5 Q6/Q7):**
Calcule o volume $V$ do sólido $E$ limitado superiormente pelo paraboloide $z = x^2 + y^2$, inferiormente pelo plano $xy$ ($z = 0$) e lateralmente pelo cilindro $x^2 + y^2 = 2x$.

### Resolução Padrão Henrique Araújo:
1. **Descrição Espacial e Projeção 2D ($D$):**
   O sólido $E$ está abaixo da superfície $z = f(x,y) = x^2 + y^2 \ge 0$ e acima do plano $z = 0$, dentro do cilindro vertical cuja equação no plano $xy$ é:
   $$x^2 + y^2 = 2x \iff x^2 - 2x + 1 + y^2 = 1 \iff (x - 1)^2 + y^2 = 1$$
   **Como enxergar e desenhar a região $D$:** Trata-se de um disco fechado (fronteira em linha cheia) de centro $(1,0)$ e raio $1$, tangente ao eixo $y$ na origem $(0,0)$, estendendo-se de $x = 0$ até $x = 2$ nos quadrantes I e IV.

2. **Passagem para Coordenadas Polares:**
   Substituindo $x = r\cos\theta$ e $x^2 + y^2 = r^2$ na fronteira do cilindro:
   $$r^2 = 2r\cos\theta \implies r = 2\cos\theta \quad (\text{ou } r = 0)$$
   Disparando uma semirreta radial da origem $O(0,0)$, ela entra no disco em $r_{\text{in}} = 0$ e sai na circunferência em $r_{\text{out}} = 2\cos\theta$. Para cobrir os quadrantes IV e I onde $x \ge 0$, o ângulo $\theta$ varia da reta tangente inferior $\theta = -\frac{\pi}{2}$ até a reta tangente superior $\theta = \frac{\pi}{2}$. Logo:
   $$D = \left\{ (r, \theta) \;\middle|\; -\frac{\pi}{2} \le \theta \le \frac{\pi}{2}, \; 0 \le r \le 2\cos\theta \right\}$$

3. **Aplicação do Teorema e Cálculo da Integral:**
   Como $f(x,y) = x^2 + y^2$ é uma função polinomial contínua no compacto $D$, pelo **Teorema da Mudança de Variáveis para Coordenadas Polares** (com Jacobiano $|\det J| = r$) e pelo **Teorema de Fubini**, temos:
   $$V = \iint_D (x^2 + y^2)\,dA = \int_{-\pi/2}^{\pi/2} \int_0^{2\cos\theta} (r^2)\,r\,dr\,d\theta = \int_{-\pi/2}^{\pi/2} \int_0^{2\cos\theta} r^3\,dr\,d\theta$$
   Calculando a integral interna em $r$:
   $$\int_0^{2\cos\theta} r^3\,dr = \left[ \frac{r^4}{4} \right]_0^{2\cos\theta} = \frac{(2\cos\theta)^4}{4} - 0 = \frac{16\cos^4\theta}{4} = 4\cos^4\theta$$
   Substituindo na integral externa em $\theta$ e usando a paridade de $\cos^4\theta$ no intervalo simétrico $[-\pi/2, \pi/2]$:
   $$V = \int_{-\pi/2}^{\pi/2} 4\cos^4\theta\,d\theta = 8 \int_0^{\pi/2} \cos^4\theta\,d\theta$$
   Aplicando duas vezes a identidade de arco duplo $\cos^2 u = \frac{1 + \cos(2u)}{2}$:
   $$\cos^4\theta = \left(\frac{1 + \cos(2\theta)}{2}\right)^2 = \frac{1}{4}\big(1 + 2\cos(2\theta) + \cos^2(2\theta)\big) = \frac{1}{4}\left(1 + 2\cos(2\theta) + \frac{1 + \cos(4\theta)}{2}\right)$$
   $$\implies 8\cos^4\theta = 2\left(\frac{3}{2} + 2\cos(2\theta) + \frac{1}{2}\cos(4\theta)\right) = 3 + 4\cos(2\theta) + \cos(4\theta)$$
   Integrando termo a termo de $0$ a $\pi/2$:
   $$V = \int_0^{\pi/2} \big(3 + 4\cos(2\theta) + \cos(4\theta)\big)\,d\theta = \left[ 3\theta + 2\sin(2\theta) + \frac{\sin(4\theta)}{4} \right]_0^{\pi/2}$$
   $$V = \left(3\cdot\frac{\pi}{2} + 2\sin(\pi) + \frac{\sin(2\pi)}{4}\right) - (0 + 0 + 0) = \frac{3\pi}{2}$$

---

## 7. Erros que Custam Ponto na Prova do Prof. Henrique Araújo

| Armadilha de Prova | Por que acontece | Como blindar sua resolução |
|---|---|---|
| **1. Esquecer o fator Jacobiano $r$** | Substituir $dA = dr\,d\theta$ por reflexo de coordenadas cartesianas. | **Erro gravíssimo.** Escreva sempre $dA = r\,dr\,d\theta$ e circule o $r$ antes de simplificar o integrando. |
| **2. Usar $\theta \in [0, 2\pi]$ em círculos tangentes aos eixos** | Achar que todo círculo precisa de uma volta de $2\pi$ na origem. | O círculo $r = 2a\cos\theta$ fecha 1 volta completa em **$[-\pi/2, \pi/2]$** (e $r = 2a\sin\theta$ fecha em **$[0, \pi]$**). Usar $[0, 2\pi]$ duplica o resultado ou gera $r < 0$! |
| **3. Errar o ângulo de fechamento de uma pétala de rosácea** | Usar $[0, \pi/2]$ para uma pétala de $r = \cos(2\theta)$. | A pétala fecha onde $r = 0 \iff \cos(n\theta) = 0 \iff n\theta = \pm\pi/2$. Para $n=2$, 1 pétala vai de $-\pi/4$ a $\pi/4$ (ou no 1ºQ de $0$ a $\pi/4$). |
| **4. Cancelar $r$ ao igualar duas curvas sem checar a origem** | Ao resolver $r = h_1(\theta) = h_2(\theta)$, esquecer que o polo $r = 0$ pode ser atingido em ângulos diferentes. | Sempre faça o esboço geométrico junto com a conta algébrica $h_1(\theta) = h_2(\theta)$. |
| **5. Pular a redução de potência trigonométrica** | Escrever direto o valor de $\int_0^{\pi/2} \cos^2\theta\,d\theta = \pi/4$. | O Prof. Henrique exige o passo explícito: $\cos^2\theta = \frac{1+\cos(2\theta)}{2}$ e a primitiva $\left[\frac{\theta}{2} + \frac{\sin(2\theta)}{4}\right]$. |
| **6. Omitir a citação teórica** | Começar a questão direto na integral iterada. | Sempre escreva 1 linha citando a continuidade do integrando no compacto $D$ e o **Teorema da Mudança de Variáveis em Coordenadas Polares**. |
