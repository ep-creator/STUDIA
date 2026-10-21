---
tipo: anotacao
titulo: Listas de 2026.1
unidade: null
secao: null
questao: null
origem: migrado
---
# Listas de 2026.1 — mapa por assunto

As seis listas estão em `disciplina/listas-2026-1/`. São do semestre **2026.1**, de outra equipe (profs. Daniel Lopes, Eddygledson Gama, Matheus Oliveira, William Roqueta) — **não** do prof. Henrique.

> **Como ler isso.** Elas não são a lista da sua turma e não substituem a lista oficial do Stewart. O que elas são: o estilo de questão que o Departamento de Matemática da UFPE escreve — enunciado em palavras, item (a)/(b) encadeado, "justifique", "acompanhe com uma figura". O Stewart treina técnica; estas treinam **prova**.

## Correspondência

| Lista | Conteúdo | Stewart | Unidade |
|---|---|---|---|
| **1** | Funções de duas variáveis, limite e continuidade | 14.1, 14.2 | 1ª ✔ |
| **2** | Parciais, diferenciabilidade, gradiente, plano tangente, reta normal, regra da cadeia, derivação implícita | 14.3, 14.4, 14.5 | 1ª ✔ |
| 3 | Derivada direcional e máxima, máx/mín, Lagrange com um e dois vínculos | 14.6, 14.7, 14.8 | 2ª ✔ |
| 4 | Integral dupla, integral dupla sobre regiões | 15.2, 15.3 | 2ª ✔ |
| **5** | Coordenadas polares, integral dupla em polares, mudança de variáveis | 15.4, 15.10 | 3ª |
| **6** | Integral tripla, cilíndricas e esféricas, aplicações | 15.7, 15.8, 15.9, 15.10 | 3ª |

**As listas 3 e 4 cobriram a 2ª unidade inteira; as listas 5 e 6 cobrem a 3ª** — por isso elas entram no plano da 3ª unidade (`plano-estudos-unidade3.md`). A 15.6, que o professor pulou, não aparece em nenhuma.

---

## Lista 5 — detalhada (15.4, 15.5, 15.10) ← 3ª unidade

15 questões.

| Questões | Assunto | Seção |
|---|---|---|
| 1, 2, 3, 4 | Coordenadas polares puras: converter pontos e curvas, **desenhar** curvas polares | 10.3 |
| 5, 6, 7, 10 | Área e integral dupla em polares | 15.4 |
| 8, 9 | Centroide, massa e centro de massa | 15.5 |
| 11, 12, 13, 14, 15 | Mudança de variáveis | 15.10 |

### As que valem mais do que parecem

- **#4** — desenhar `r = cos 3θ`, `r = sen 2θ`. É desenho, o seu ponto fraco conhecido, e em 15.4 o desenho da região **é** metade do exercício. Entra antes da primeira aula (sessão P1).
- **#5** — área de `r = 3 + 2cos θ` **fora** da rosácea. Obriga a achar onde as curvas se cruzam e a subtrair regiões — a questão de prova típica de 15.4.
- **#6(b)** — região entre `x² + y² = 4` e `(x − 1)² + y² = 1`: um círculo **não centrado na origem**, que em polar vira `r = 2cos θ`. Pega quem só sabe polar de disco centrado.
- **#9** — massa e centro de massa com densidade, em região polar: junta 15.4 e 15.5 numa questão só.
- **#10** — região que **não** é retângulo polar (`y = √(2 − x²)`, `y = x²`, `x = 0`, `x = 1`). Obriga a decidir onde polar ajuda e onde atrapalha.
- **#12** — paralelogramo com lados `x + y = c` e `x − 2y = c`: a escolha `u = x + y`, `v = x − 2y` é o exemplo-padrão de mudança de variáveis.

## Lista 6 — detalhada (15.7, 15.8, 15.9) ← 3ª unidade

14 questões.

| Questões | Assunto | Seção |
|---|---|---|
| 1, 2, 3, 4, 6 | Integral tripla em caixas e sólidos gerais, tipos I/II/III, volume | 15.7 |
| 5, 7, 8, 11 | Cilíndricas | 15.8 |
| 9, 10, 12, 13, 14 | Esféricas (e a escolha entre os sistemas) | 15.9 / 15.10 |

### As que valem mais do que parecem

- **#2 e #4** — "faça um desenho de E", "desenhe e calcule". Mesmo motivo da L5 #4: treino dirigido do ponto fraco.
- **#3 e #6** — escrever o mesmo sólido como **tipo I, II e III**. É a versão de prova do 15.7 #29 e #33 (seis ordens).
- **#8** — pede a integral **em cilíndricas e em cartesianas** e que você **escolha** a mais apropriada. A escolha justificada é o item que o professor gosta.
- **#9** — elipsoide em esféricas: só sai com mudança de variáveis antes (`x = au`, `y = bv`, `z = cw`). Junta 15.9 e 15.10; entra na S12.
- **#12** — descrever sólidos por desigualdades em esféricas, **com figura**. Questão de teoria/desenho, sem conta.
- **#14** — o mesmo sólido em **cartesianas, cilíndricas e esféricas**. Se você só puder fazer uma questão desta lista, é esta.

---

## Lista 3 — detalhada (14.6, 14.7, 14.8) · 2ª unidade, encerrada

13 questões. Divisão por assunto:

| Questões | Assunto | Seção |
|---|---|---|
| 1, 2, 3, 4 | Derivada direcional e gradiente | 14.6 |
| 5, 6 | Classificar pontos críticos | 14.7 |
| 7, 8, 9 | Extremos absolutos em região fechada | 14.7 |
| 10, 11 | Lagrange, um vínculo | 14.8 |
| 12, 13 | Lagrange, **dois vínculos** | 14.8 |

### As que valem mais do que parecem

- **#2** — a função `x⁴y/(x⁸+y⁴)` tem derivada direcional em **toda** direção e mesmo assim não é contínua na origem. É o contraexemplo que mostra por que o teorema da §3 do resumo 06 exige *diferenciabilidade*, e não "as direcionais existem". Questão de teoria mais provável da seção.
- **#4** — dá duas derivadas direcionais e pede o gradiente. Inverte o sentido usual do exercício e por isso pega gente que decorou a fórmula sem entender que é produto escalar.
- **#6** — classificar pontos críticos **na dependência de um parâmetro c**. Obriga a discutir o sinal de D em vez de calcular um número. Se aparecer na prova, é a questão que separa as notas.
- **#8(b) e #9** — o roteiro completo de extremos absolutos: interior + fronteira. O #9 tem fronteira circular (parametrizar) e o #8(b) tem fronteira poligonal (lado a lado + vértices). Fazer os dois cobre as duas técnicas.
- **#11** — pede o mesmo problema **com e sem Lagrange**. É a melhor questão da lista para entender o método, porque você vê o que ele economiza.
- **#12, #13** — dois vínculos (`∇f = λ∇g + μ∇h`). O Stewart trata isso rápido no fim do 14.8; aqui tem duas questões inteiras.

### Onde ela é mais dura que o Stewart

Nas questões de Lagrange com superfície não trivial (#11b `x²y⁴z = 1`, #11c `z² = x²y + 1`), o sistema sai feio. Não desista na álgebra: o padrão é dividir uma equação pela outra para eliminar λ.

---

## Lista 4 — detalhada (15.2, 15.3) · 2ª unidade, encerrada

9 questões.

| Questões | Assunto |
|---|---|
| 1, 5 | Integral iterada sobre retângulo, Fubini |
| 2, 9 | Volume por integral dupla |
| 3, 4, 6, 7 | Regiões gerais (tipo I e tipo II) |
| 8 | **Inverter a ordem de integração** |

### As que valem mais do que parecem

- **#1 e #4** — pedem explicitamente as **duas** ordens, e o #4 avisa que uma é muito mais fácil. Essa escolha é o conteúdo real da seção.
- **#8** — dada `∫₀¹ ∫₀^{arctg y} f dx dy`, desenhar a região, inverter e calcular para `f = sec³x`. Sem inverter não sai. É a questão-padrão de prova do assunto.
- **#3(a)** — pede para **comparar** com o método de Cálculo 1. É pedido de justificativa escrita, não de conta: exatamente o tipo de item que o Henrique gosta.
- **#2** — "acompanhe sua resolução com uma figura". Esse é o seu ponto fraco conhecido. Faça essa.

---

## Listas 1 e 2 — já passaram (1ª unidade)

Guardadas para quando a nota da 1ª unidade sair. Se algum assunto vier fraco na correção, o reforço vem daqui e não de mais Stewart — **lista 1 #4, #6, #7, #8** são limites no estilo do enunciado de prova, e **lista 2 #6 e #7** são os contraexemplos de diferenciabilidade.

## Aviso sobre gabarito

Estas listas também vêm **sem respostas**. Vale a mesma regra do resto do projeto: traga a resolução escrita e a gente corrige no critério do professor.
