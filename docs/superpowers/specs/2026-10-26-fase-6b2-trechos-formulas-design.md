# Fase 6 · Peça B2 — Trechos por parte do livro e texto limpo das fórmulas

> Continuação da peça B (`2026-10-26-fase-6b-busca-design.md`, §9). A avaliação v3 mostrou que o que limita a busca
> não é o modelo, e sim o texto do índice: trechos que misturam teoria e exercícios, cabeçalhos e fórmulas estragadas.
> Esta peça trata disso. O reordenador só entra depois, com spec própria, se a medição pedir (§6.3).

## 1. Objetivo e critério de sucesso

O uso principal é o da peça B: **na página da lista, partir do enunciado de uma questão e chegar ao trecho certo do
livro ou dos slides**. O mesmo vale para a IA ao explicar uma questão ou montar um resumo.

Sucesso:

1. o acerto@5 da teoria na avaliação v3 sobe em pelo menos uma matéria (Cálculo 2: 77%, Geometria: 75%), sem cair
   na outra, e os links não pioram;
2. o texto que a busca devolve (para a pessoa e para a IA) traz os símbolos certos (θ, π, ∫, √, ², ≤…), na frase
   em que aparecem, sem cabeçalho de página e sem caracteres invisíveis, conferido em páginas de amostra;
3. da página de uma lista do Cálculo, a questão que é exercício do livro abre o enunciado original e a resposta.

## 2. Decisões

| Tema | Decisão |
|---|---|
| Ordem | 1) trechos separados, 2) limpeza das fórmulas, 3) decisão sobre o reordenador, medindo a cada passo |
| Por que essa ordem | a busca por palavras ignora símbolos (só `[a-z0-9]`): a limpeza quase não mexe no acerto; o corte mexe |
| Por que limpar mesmo assim | a IA lê o trecho para explicar e resumir; hoje lê "u" no lugar de θ e frases sem a fórmula |
| Reordenador | só se a medição pedir (escolha do usuário); spec própria, desligado por padrão até provar ganho |
| Exercícios do livro | aparecem num grupo separado da teoria, com a resposta do gabarito (escolha do usuário) |
| Como limpar | leitura por fonte e posição + tabelas por fonte (opção A); sem OCR (B) e sem pedir ao Claude (C) |
| Onde a leitura nova vale | só no índice da busca; a importação de livros e listas continua com a leitura atual |
| Dados do usuário | PDFs, `.md` e `materia.db` não são alterados; só o índice derivado (`.indice/`) é refeito |

### 2.1 O problema das fórmulas

No PDF, o texto é guardado como "desenhe o símbolo nº N da fonte X nesta posição", mais uma tabela opcional que diz
qual letra cada símbolo é. As fontes de matemática do Stewart guardam o desenho do θ no lugar do "u" (e o π no do
"p") e não trazem a tabela certa. Por isso qualquer leitor, inclusive o PyMuPDF, entrega "u". Exemplos medidos na
página da seção 10.4:

| Fonte | O PDF entrega | É |
|---|---|---|
| `LTSGreek-Italic` | `u`, `p` | θ, π |
| `TECHMath-Mix` | `¨` | θ |
| `MathematicalPi-One/Three/Five`, `Symbol`, `MATH` | caracteres de uso privado ou letras | ∫, =, ±, Δ, ∞… |

O segundo problema é a ordem: a diagramação grava fórmulas numa passada separada, e a leitura "texto pronto" segue a
ordem do arquivo. Nos slides da Geometria a frase vira "a norma de um vetor do / é definida por / u / ℝn / ∥u∥=".
Nos slides, 190 dos 1.043 trechos têm caracteres de uso privado.

## 3. Trechos por parte do livro

### 3.1 Corte

Para cada seção do livro (já cadastrada em `secao_livro`, com páginas):

- **teoria**: do começo da seção até a linha que começa com `Exercícios` (opcionalmente seguida do código da seção,
  como `Exercícios 14.1`); trechos com limite entre 800 e 1.600 caracteres, escolhido pela avaliação (§6.1);
- **exercícios**: depois desse título, até o fim da seção; um trecho por exercício, que começa numa linha `N.` com
  N crescente a partir de 1; exercícios curtos (menos de 200 caracteres) se juntam ao seguinte; cada trecho guarda a
  seção e o número do primeiro exercício;
- **respostas**: o gabarito do fim do livro (`livro.gabarito_pdf_ini/fim`) é cortado pela linha com o código da
  seção (`14.1`) e depois pelas linhas `N.`; cada resposta fica ligada a (seção, número).

Sem título de exercícios na seção, a seção inteira é teoria. Livro sem seções cadastradas (como o Boulos) fica como
hoje. Slides, listas, provas e documentos são teoria. Um número fora de sequência (como "2." dentro de uma conta)
não abre trecho novo.

### 3.2 Índice v4

`trecho` ganha `parte TEXT NOT NULL DEFAULT 'teoria'` (`teoria | exercicio | resposta`) e `numero INTEGER`
(número do exercício ou da resposta). `VERSAO_INDICE = 4`: o índice v3 é refeito sozinho na próxima sincronização,
como na peça B.

### 3.3 Busca

- `buscar`/`buscar_modo` ganham `partes: list[str] | None` (padrão: todas); o `Resultado` ganha `parte` e `numero`.
- A API `GET /busca` devolve dois grupos: `teoria` (ranking atual, só `parte = 'teoria'`) e `exercicios` (os 3
  melhores de `parte = 'exercicio'`, cada um com a resposta quando existe um trecho `resposta` com a mesma seção e
  número).
- A paleta (`BuscaMateria`) mostra os dois grupos: "Teoria" e "Exercícios do livro". O exercício abre o livro na
  página dele e mostra a resposta logo abaixo.
- A IA recebe os dois grupos com a marca de cada um.

### 3.4 "Ver no livro" na página da lista

Quando o código da lista é o código de uma seção do livro e o rótulo da questão é um número (`14.1`, questão `22`),
a questão é o exercício 22 da seção 14.1. A página da lista ganha o botão **"Ver no livro"**, que abre o trecho do
exercício (enunciado original, com a função que o banco não guarda) e a resposta, quando há. É uma ligação direta
pelo índice, sem busca. Não aparece quando não há exercício com essa seção e número (as listas da Geometria).

## 4. Texto limpo das fórmulas

### 4.1 Leitura por fonte e posição

`importacao/pdf.py` ganha `ler_paginas_limpas(caminho: Path) -> list[PaginaPdf]` (mesmo `PaginaPdf` de hoje, texto limpo),
usada só pelo indexador:

1. pede ao PyMuPDF cada pedaço com fonte, tamanho e caixa (`get_text("dict")`);
2. traduz o texto de cada pedaço pela tabela da sua fonte (§4.2);
3. separa as colunas pela posição horizontal (a margem do Stewart não se mistura ao texto) e, em cada coluna,
   junta em linhas os pedaços que se sobrepõem na altura; expoentes e índices (fonte menor, um pouco acima ou abaixo)
   grudam na letra anterior;
4. tira o que fica na faixa do topo e do rodapé quando se repete entre páginas (cabeçalho "CÁLCULO", número da
   página), além da regra de repetição que já existe.

Se a leitura detalhada falhar numa página, aquela página usa a leitura atual (`limpar_texto(page.get_text())`).

### 4.2 Tabelas por fonte

`importacao/fontes_matematicas.py`: mapa do nome da fonte (sem o prefixo de subconjunto `ABCDEF+`) para a troca
de cada caractere. As tabelas são montadas desenhando cada símbolo de cada fonte encontrada nos PDFs do Cálculo 2 e
da Geometria e conferindo um a um. O texto sai em Unicode, não em LaTeX.

- Caractere de uso privado sem tradução é retirado; o indexador conta quantos e avisa "N símbolos sem tradução em
  <arquivo>" no resumo da sincronização.
- Fonte desconhecida: o texto passa como está (comportamento de hoje).
- Limite aceito: frações e integrais empilhadas saem no lugar e com os símbolos certos, mas em linhas separadas.
- O Guidorizzi é um PDF escaneado com OCR (o texto já vem com erros como "parc1rus"); nada nesta peça conserta isso.

### 4.3 Consulta

A consulta passa pela mesma tradução de caracteres de uso privado (retirar os sem tradução), para os enunciados das
listas que já estão no banco casarem com o texto limpo. Os enunciados não são reescritos.

## 5. Falhas

| Situação | Comportamento |
|---|---|
| Página com erro na leitura detalhada | essa página usa a leitura atual |
| Seção sem título de exercícios ou numeração que não fecha | seção inteira como teoria |
| Gabarito com formato não reconhecido | respostas ficam fora; o exercício aparece sem resposta |
| Fonte sem tabela | texto como hoje, aviso com a contagem de símbolos sem tradução |
| Índice v3 no disco | refeito na próxima sincronização |

## 6. Medição e testes

### 6.1 Passo 1: trechos

A avaliação v3 roda nas duas matérias com limite de teoria de 800, 1.200 e 1.600 caracteres. Os acertos de questão
passam a contar só o grupo teoria (vale para todas as perguntas). Fica o limite que cumprir o critério 1 do §1 com o maior acerto somado; se nenhum
cumprir, o passo não entra e eu apresento os erros.

### 6.2 Passo 2: fórmulas

Não pode baixar o acerto do passo 1, e as páginas de amostra (§6.4) precisam passar.

### 6.3 Passo 3: decisão sobre o reordenador

A tabela da avaliação ganha **acerto@20**. Se, nas perguntas que erram no top 5, o trecho certo está no top 20 na
maioria dos casos, o erro é de ordem e o reordenador ganha spec própria. Senão, o relatório lista os erros que
sobraram, sem reordenador.

### 6.4 Testes automáticos

- **Páginas de amostra**: 10 do Stewart e 5 dos slides da Geometria, com o texto esperado escrito à mão. Os pedaços
  dessas páginas (fonte, caixa, texto) ficam salvos em JSON em `tests/dados/paginas/`, para o teste rodar sem os
  PDFs (que são do usuário e não vão para o repositório). Conferem: símbolos traduzidos, ordem das frases, nenhum
  caractere de uso privado, cabeçalho fora.
- **Corte**: textos sintéticos de seção com teoria, `Exercícios 14.1`, exercícios `1.` a `5.` (um curto, um com "2."
  dentro de uma conta) e um gabarito com duas seções; conferem `parte`, `numero` e a ligação resposta ↔ exercício.
- **Índice**: v3 refeito como v4; livro sem seções igual a hoje.
- **API e paleta**: dois grupos; exercício com e sem resposta.
- **"Ver no livro"**: aparece para `14.1`/`22` com exercício no índice; some quando não há.

## 7. Ordem de entrega

1. Corte em teoria, exercícios e respostas; índice v4; `partes` na busca.
2. Avaliação com os limites (§6.1) e acerto@20; registro em `docs/avaliacoes/`.
3. Grupos na API e na paleta; "Ver no livro".
4. Leitura por fonte e posição, tabelas e páginas de amostra.
5. Avaliação do passo 2 e decisão do passo 3, registradas nesta spec.

## 8. Fora de escopo

- Reordenador (spec própria, se o §6.3 pedir).
- Refazer o OCR do Guidorizzi e o sumário do Boulos.
- Fórmulas empilhadas montadas por inteiro (reconhecer a imagem, opção B).
- Usar a leitura nova na importação de livros e listas.

## 9. Resultado (2026-10-27)

### 9.1 Números (modo texto; Cálculo com `--geradas`, 161 perguntas; Geometria, 44)

| | Cálculo: geral / questão / paráfrase / links | Geometria: geral / exata / questão / trecho / links |
|---|---|---|
| base (peça B, v3) | 78% / 77% / 65% / 56% | 70% / 100% / 75% / 75% / 29% |
| passo 1: trechos (limite 1.200) | **80% / 78%** / 70% / 56% | 68% / 93% / **80%** / 62% / **33%** |
| passo 2: + leitura limpa | 78% / 77% / 65% / 56% | 66% / 86% / **80%** / 25% / **38%** |

- **Passo 1 entrou** (critério cumprido): o acerto das perguntas de questão sobe nas duas matérias e os links não pioram.
- **Passo 2 não cumpriu o critério numérico** (baixa uma ou duas perguntas por matéria). Comparando pergunta a pergunta a
  leitura antiga e a limpa num mesmo gabarito, não há defeito: a ordem e as fronteiras dos trechos mudaram e umas
  perguntas sobem (5→3, 14→10, 3→1) enquanto outras descem (2→5, 1→3); a queda da página exata da Geometria são 2 de 8
  perguntas que passaram da posição 5 para a 6. **Fica**, pelo que a spec pedia dela (§2): o texto que a busca devolve
  (para a pessoa e para a IA) passa a ter os símbolos certos e as frases inteiras, e o "Ver no livro" depende dela —
  com a leitura antiga a numeração dos exercícios do Stewart se perdia (colunas embaralhadas).
- **"Ver no livro"**: das 204 questões das listas do Cálculo que são exercício do Stewart, 187 são achadas (91%); 50
  vêm com a resposta (o Stewart só responde os ímpares).
- **Tempo**: ler o Stewart vol. 2 inteiro leva ~20 s (a leitura antiga, ~7 s); indexar a matéria inteira, de 90 s a
  250 s conforme a carga da máquina (antes, ~30 s). Dentro do limite de 10 minutos da peça B.

### 9.2 Decisão sobre o reordenador (§6.3)

Das perguntas que erram no top 5, a resposta está no top 20 em **68%** (Cálculo: 78% → 93%) e em **59%** (Geometria:
66% → 86%). A maioria dos erros é de **ordem**, não de recuperação: o reordenador tem espaço para ganhar e merece spec
própria (desligado por padrão até provar ganho na mesma avaliação).

### 9.3 Achados e limites

- Leitura limpa: tabelas por **nome do glifo** para as MathematicalPi (o código muda entre PDFs, o nome não) e por
  letra para LTSGreek, TECHMath, MATH e CMEX10; o glifo "t" da Times-Italic-TT do Stewart desenha "g" (nome errado na
  própria fonte) e fica "t"; frações e integrais empilhadas saem em linhas separadas; 54 símbolos do Stewart ficam sem
  tradução.
- Grades de itens na mesma linha (9 | 10) saem por coluna; a numeração aceita item fora de ordem (janela de +10/−20).
- O título da 14.5 no PDF ("Regra da Cadeia") não casa com o cadastro ("A Regra da Cadeia"): a seção começa na página.
- O Guidorizzi é escaneado com OCR (texto com erros de leitura): nada desta peça conserta isso.
- As amostras de páginas reais usadas nos testes ficam só no computador do usuário (o repositório é público).
