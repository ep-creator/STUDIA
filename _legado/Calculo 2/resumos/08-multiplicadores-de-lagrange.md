# 14.8 Multiplicadores de Lagrange

> Extremos condicionados com um e dois vínculos, interpretação geométrica de curvas/superfícies de nível e otimização em compactos · Stewart 14.8 · Guidorizzi 16.5

---

## 1. A ideia geométrica (Como enxergar e desenhar a região/sólido)

Na Seção 14.7 buscamos extremos livres no interior de um domínio ($\nabla f = \vec{0}$). Agora queremos extremizar uma **função objetivo** $f$ sujeita a uma **restrição (ou vínculo)** $g = k$.

### Caso 2D: Curvas de nível no plano $\mathbb{R}^2$
Queremos maximizar ou minimizar $f(x,y)$ sujeita a $g(x,y) = k$.
- A restrição $g(x,y) = k$ é uma **curva fixa** no plano $xy$ (por exemplo, uma circunferência, elipse ou hipérbole).
- A função $f(x,y)$ gera uma família de **curvas de nível** $f(x,y) = c$.
- **Como enxergar no esboço:** à medida que variamos a altura $c$, as curvas de nível $f(x,y) = c$ se expandem ou se deslocam pelo plano. Enquanto uma curva de nível *atravessa* (corta transversalmente) a curva de restrição $g(x,y) = k$, ainda podemos aumentar ou diminuir $c$ andando ao longo da restrição. O valor extremo $c$ ocorre exatamente no instante limite em que a curva de nível $f(x,y) = c$ **tangencia** a curva de restrição $g(x,y) = k$.
- Duas curvas suaves são tangentes em $P_0(x_0, y_0)$ se, e somente se, suas retas normais coincidem — isto é, seus **vetores gradientes são paralelos**:

$$\nabla f(x_0, y_0) = \lambda \nabla g(x_0, y_0)$$

### Caso 3D com 1 vínculo: Superfícies de nível em $\mathbb{R}^3$
Queremos extremizar $f(x,y,z)$ sobre a superfície $S$ dada por $g(x,y,z) = k$.
- Nos pontos extremos, a superfície de nível $f(x,y,z) = c$ **tangencia** a superfície de restrição $g(x,y,z) = k$.
- Logo, os planos tangentes coincidem e os vetores normais $\nabla f$ e $\nabla g$ são colineares: $\nabla f = \lambda \nabla g$.

---

## 2. Teorema de Lagrange com Uma Restrição

> **Teorema 1 (Multiplicadores de Lagrange — 1 vínculo).** Sejam $f$ diferenciável num aberto $A \subset \mathbb{R}^n$ ($n = 2$ ou $3$) e $g$ de classe $C^1$ em $A$. Seja $B = \{P \in A : g(P) = k\}$ o conjunto de restrição, e suponha que a **condição de regularidade**
> $$\nabla g(P) \neq \vec{0}$$
> seja satisfeita em todo ponto $P \in B$. Se $f$ restrita a $B$ atinge um extremo local (máximo ou mínimo) em $P_0 \in B$, então existe um número real $\lambda \in \mathbb{R}$ (chamado **multiplicador de Lagrange**) tal que:
> $$\nabla f(P_0) = \lambda \nabla g(P_0)$$

### Demonstração (para entender a exigência das hipóteses)
Seja $P_0 \in B$ um extremo local de $f$ sobre $S: g(x,y,z) = k$. Tome qualquer curva diferenciável $\vec{r}(t) = \langle x(t), y(t), z(t) \rangle$ contida em $S$ passando por $P_0 = \vec{r}(t_0)$.
1. A função composta de uma variável $h(t) = f(\vec{r}(t))$ tem um extremo local em $t_0$, logo $h'(t_0) = 0$. Pela Regra da Cadeia:
   $$0 = h'(t_0) = \nabla f(P_0) \cdot \vec{r}\,'(t_0)$$
   Portanto, $\nabla f(P_0)$ é ortogonal ao vetor tangente $\vec{r}\,'(t_0)$ de **toda** curva sobre $S$, o que significa que $\nabla f(P_0)$ é ortogonal ao plano tangente a $S$ em $P_0$.
2. Como $g(\vec{r}(t)) = k$ é constante ao longo de $\vec{r}(t)$, derivando pela Regra da Cadeia temos $\nabla g(P_0) \cdot \vec{r}\,'(t_0) = 0$, ou seja, $\nabla g(P_0)$ também é ortogonal ao plano tangente a $S$ em $P_0$.
3. Como o complemento ortogonal de um plano em $\mathbb{R}^3$ tem dimensão 1 e $\nabla g(P_0) \neq \vec{0}$, segue que $\nabla f(P_0)$ é múltiplo escalar de $\nabla g(P_0)$, isto é, $\nabla f(P_0) = \lambda \nabla g(P_0)$.

### O Sistema de Equações de Lagrange
Escrevendo componente a componente, buscamos os pontos candidatos resolvendo:

| Em $\mathbb{R}^2$ (3 equações, 3 incógnitas: $x, y, \lambda$) | Em $\mathbb{R}^3$ (4 equações, 4 incógnitas: $x, y, z, \lambda$) |
|---|---|
| $$\begin{cases} f_x(x,y) = \lambda g_x(x,y) \\ f_y(x,y) = \lambda g_y(x,y) \\ g(x,y) = k \end{cases}$$ | $$\begin{cases} f_x(x,y,z) = \lambda g_x(x,y,z) \\ f_y(x,y,z) = \lambda g_y(x,y,z) \\ f_z(x,y,z) = \lambda g_z(x,y,z) \\ g(x,y,z) = k \end{cases}$$ |

> **Atenção para a prova (O que citar):**
> 1. **Condição necessária, não suficiente:** O sistema de Lagrange fornece apenas os **candidatos** a extremos condicionados (assim como $f'(x)=0$ em Cálculo 1). No Exemplo 2 do Guidorizzi (§16.5), $f(x,y) = y + x^3$ sujeita a $y - x^3 = 0$ tem $(0,0)$ como único candidato de Lagrange, mas $f(x, x^3) = 2x^3$ não tem máximo nem mínimo!
> 2. **Como garantir que o candidato é extremo global:** Cite o **Teorema de Weierstrass**: *"Como $f$ é contínua e a restrição $B = \{g(P) = k\}$ é um conjunto fechado e limitado (compacto) — por exemplo, circunferência, elipse, esfera ou elipsoide —, $f$ assume máximo e mínimo globais em $B$."* Basta então comparar os valores de $f$ nos candidatos encontrados!
> 3. **E se $\nabla g(P_0) = \vec{0}$?** Se houver algum ponto na curva/superfície onde $\nabla g = \vec{0}$ (como um bico/cúspide, ex.: $y^2 - x^3 = 0$ na origem, Ex. 23 do Stewart), o teorema não se aplica ali: você deve incluir esse ponto **manualmente** na lista de candidatos!

---

## 3. Multiplicadores de Lagrange com Duas Restrições (Dois Vínculos)

Suponha agora que queremos extremizar $f(x,y,z)$ sujeita simultaneamente a **duas restrições**:
$$g(x,y,z) = k \quad \text{e} \quad h(x,y,z) = c$$

### Interpretação Geométrica (Como enxergar no 3D)
- Cada equação $g = k$ e $h = c$ define uma superfície em $\mathbb{R}^3$ (por exemplo, um cilindro $x^2 + y^2 = 1$ e um plano $x - y + z = 1$).
- A interseção das duas superfícies é uma **curva espacial $C$** (no exemplo acima, uma elipse inclinada no espaço).
- Em um ponto extremo $P_0 \in C$, o gradiente $\nabla f(P_0)$ é ortogonal ao vetor tangente $\vec{r}\,'(t_0)$ da curva $C$.
- Mas $\nabla g(P_0)$ e $\nabla h(P_0)$ são normais às suas respectivas superfícies, logo ambos também são ortogonais a $C$.
- Portanto, $\nabla f(P_0)$, $\nabla g(P_0)$ e $\nabla h(P_0)$ moram todos no mesmo **plano normal** à curva $C$ em $P_0$. Se $\nabla g(P_0)$ e $\nabla h(P_0)$ forem linearmente independentes, eles formam uma base desse plano normal, e $\nabla f(P_0)$ é combinação linear deles!

> **Teorema 2 (Multiplicadores de Lagrange — 2 vínculos).** Sejam $f$ diferenciável num aberto $A \subset \mathbb{R}^3$ e $g, h$ de classe $C^1$ em $A$. Seja $C = \{P \in A : g(P) = k \text{ e } h(P) = c\}$. Suponha que a **condição de regularidade (independência linear)**
> $$\nabla g(P) \times \nabla h(P) \neq \vec{0} \quad (\text{isto é, } \nabla g \text{ e } \nabla h \text{ não são paralelos nem nulos})$$
> valha em todo ponto $P \in C$. Se $f$ restrita a $C$ atinge extremo local em $P_0 \in C$, então existem dois multiplicadores de Lagrange $\lambda, \mu \in \mathbb{R}$ tais que:
> $$\nabla f(P_0) = \lambda \nabla g(P_0) + \mu \nabla h(P_0)$$

Isso gera um **sistema de 5 equações e 5 incógnitas** ($x, y, z, \lambda, \mu$):
$$\begin{cases}
f_x(x,y,z) = \lambda g_x(x,y,z) + \mu h_x(x,y,z) \\
f_y(x,y,z) = \lambda g_y(x,y,z) + \mu h_y(x,y,z) \\
f_z(x,y,z) = \lambda g_z(x,y,z) + \mu h_z(x,y,z) \\
g(x,y,z) = k \\
h(x,y,z) = c
\end{cases}$$

---

## 4. Receita Passo a Passo e Truques Algébricos para Resolver o Sistema

O sistema de Lagrange quase nunca é linear. O segredo é **não tentar achar o valor numérico de $\lambda$ à força logo de cara**, a menos que seja imediato. Use um dos **4 padrões algébricos** abaixo:

### Algoritmo Geral de Prova
1. **Identifique $f$ e $g$ (e $h$):** Escreva claramente quem é a função objetivo e quem são os vínculos.
2. **Justifique existência e regularidade:**
   - Verifique se $\nabla g \neq \vec{0}$ (ou $\nabla g \times \nabla h \neq \vec{0}$) sobre a restrição.
   - Se a restrição for fechada e limitada, cite o **Teorema de Weierstrass** para garantir que os extremos globais existem.
3. **Monte o sistema de Lagrange** e resolva dividindo em **Casos** (nunca cancele variáveis sem testar se podem ser zero!).
4. **Avalie $f$ em todos os pontos candidatos:** Compare os valores e responda exatamente o que foi pedido (o valor máximo/mínimo, ou as coordenadas do ponto).

### Tabela de Reconhecimento: Os 4 Truques Algébricos Clássicos

| Padrão do Sistema | Exemplo Típico | Truque Algébrico para Resolver |
|---|---|---|
| **1. Fator comum nas variáveis**<br>$2x = 2\lambda x \implies 2x(1-\lambda) = 0$ | $f(x,y) = x^2 + 2y^2$ em $x^2 + y^2 = 1$ | **Fatore, nunca divida por $x$!**<br>Abra em casos:<br>• **Caso 1:** $x = 0$ (substitua na restrição e ache $y$).<br>• **Caso 2:** $\lambda = 1$ (substitua na equação de $y$ e ache $y$). |
| **2. Simetria de produtos**<br>$yz = \lambda g_x$, $xz = \lambda g_y$, $xy = \lambda g_z$ | Caixa de volume $V = xyz$ ou $f = xyz$ em elipsoide | **Multiplique a 1ª eq. por $x$, a 2ª por $y$ e a 3ª por $z$:**<br>Os lados esquerdos viram todos $xyz$, permitindo igualar os lados direitos: $\lambda x g_x = \lambda y g_y = \lambda z g_z$. |
| **3. Gradiente de $f$ constante ou linear**<br>$a = 2\lambda x \implies x = \frac{a}{2\lambda}$ | Minimizar distância a um ponto $(x_0, y_0, z_0)$ ou otimizar plano $ax+by+cz$ em esfera/elipsoide | **Isole $x, y, z$ em função de $\lambda$** (verificando antes se $1-\lambda \neq 0$ ou $\lambda \neq 0$) e substitua direto na equação da restrição $g(x,y,z)=k$ para achar $\lambda$. |
| **4. Eliminação de $\lambda$ por razão/subtração**<br>$f_x = \lambda g_x$ e $f_y = \lambda g_y$ | $f(x,y) = xy$ em $x^2 + y^2 = 1$ | Isole $\lambda = \frac{f_x}{g_x} = \frac{f_y}{g_y}$ (desde que $g_x, g_y \neq 0$), obtendo uma relação direta entre $x$ e $y$ (ex.: $y^2 = x^2 \implies y = \pm x$), e substitua na restrição. |

---

## 5. Como Combinar Seção 14.7 + Seção 14.8 (Desigualdades $g(x,y) \le k$)

Quando o enunciado pede os extremos absolutos de $f(x,y)$ numa região dada por uma **desigualdade** $g(x,y) \le k$ (como o disco fechado $x^2 + y^2 \le 9$ ou a elipse cheia $x^2 + 4y^2 \le 1$, Ex. 19–21 do Stewart), estamos num compacto com **interior** e **fronteira**:

1. **Etapa 1 — Interior ($g(x,y) < k$):**
   Resolva $\nabla f(x,y) = \vec{0}$. Descarte os pontos que caírem fora da região (onde $g > k$) e guarde apenas os que satisfazem $g(x,y) < k$.
2. **Etapa 2 — Fronteira ($g(x,y) = k$):**
   Use **Multiplicadores de Lagrange** resolvendo $\nabla f = \lambda \nabla g$ junto com $g(x,y) = k$.
3. **Etapa 3 — Comparação Final (Weierstrass):**
   Calcule $f(x,y)$ em todos os pontos da Etapa 1 e da Etapa 2. O maior valor é o máximo absoluto; o menor é o mínimo absoluto.

---

## 6. Truque da Distância: Sempre otimize $d^2$!

Em problemas de *"ponto mais próximo / mais distante de $P_0(x_0, y_0, z_0)$"* (Lista 3 #11b, #11c, #12, #13a e Exemplo 4 do Stewart):
- A distância é $d = \sqrt{(x-x_0)^2 + (y-y_0)^2 + (z-z_0)^2}$.
- Como a função raiz quadrada $u \mapsto \sqrt{u}$ é **estritamente crescente** para $u \ge 0$, os pontos que minimizam/maximizam $d$ são **exatamente os mesmos** que minimizam/maximizam o quadrado da distância:
  $$f(x,y,z) = d^2 = (x-x_0)^2 + (y-y_0)^2 + (z-z_0)^2$$
- Isso elimina todas as raízes quadradas das derivadas parciais: $\nabla f = \langle 2(x-x_0),\, 2(y-y_0),\, 2(z-z_0) \rangle$.
- **Cuidado no final:** se o enunciado pedir **a distância mínima**, lembre-se de tirar a raiz quadrada $\sqrt{f}$ na resposta final!

---

## 7. Erros que Custam Ponto na Prova

1. **Dividir por uma variável que pode ser zero:** Em $2x = 4\lambda x$, cortar o $x$ e escrever $\lambda = 1/2$ elimina toda a família de soluções com $x = 0$ (que geralmente contém o máximo ou o mínimo!). Sempre passe subtraindo e fatore: $2x(1 - 2\lambda) = 0 \implies x = 0$ ou $\lambda = 1/2$.
2. **Perder sinais ao tirar raiz quadrada:** Em $x^2 = y^2$ ou $\lambda^2 = 4$, escrever apenas $x = y$ ou $\lambda = 2$ perde metade dos candidatos. Escreva sempre $x = \pm y$ e $\lambda = \pm 2$, testando todas as combinações de sinais compatíveis com o sistema.
3. **Esquecer de verificar $\lambda = 0$:** Às vezes $\lambda = 0$ é solução válida (significa que um ponto crítico livre de $f$, onde $\nabla f = \vec{0}$, deu a sorte de cair exatamente em cima da restrição $g = k$, como na Lista 3 #13b).
4. **Assumir que todo vínculo é compacto:** Esferas ($x^2+y^2+z^2=1$) e elipses são compactas (têm máximo e mínimo). Mas hiperboloides, paraboloides ($z^2 = x^2y + 1$) ou superfícies como $x^2y^4z = 1$ são **ilimitadas**! Nelas, a distância à origem tem mínimo global (pois $d^2 \to +\infty$ quando $\|(x,y,z)\| \to \infty$), mas **não tem máximo global**.
5. **Ignorar restrições de domínio ou fronteira do próprio vínculo:** No Ex. 22 do Stewart (maximizar $2x+3y$ em $\sqrt{x}+\sqrt{y}=5$), o método de Lagrange acha $(9,4)$ com $f(9,4)=30$, mas a curva termina nas extremidades $(25,0)$ e $(0,25)$ onde as derivadas não existem e $f(25,0)=50 > 30$. Sempre cheque se as variáveis têm restrição de sinal ($x > 0, y > 0$ em caixas geométricas) ou extremidades de domínio.
6. **Esquecer o interior quando a restrição é desigualdade ($\le$):** Aplicar apenas Lagrange em $x^2 + y^2 \le 1$ avalia somente a circunferência $x^2 + y^2 = 1$ e esquece os pontos críticos de dentro do disco aberto $x^2 + y^2 < 1$.
