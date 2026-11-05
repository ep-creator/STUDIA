---
name: STUDIA
description: Plataforma de estudos local para exatas — papel creme, tinta escura, um laranja brasa de sinal.
colors:
  brasa: "#d9572b"
  brasa-noite: "#f07a45"
  brasa-texto: "#ad3e18"
  papel: "#f3ece0"
  papel-lateral: "#ece3d3"
  papel-elevado: "#f8f2e8"
  tinta: "#141413"
  tinta-suave: "#5f5a52"
  noite: "#191714"
  noite-lateral: "#201d19"
  noite-elevado: "#221f1a"
  giz: "#efe6d6"
  giz-suave: "#b3a994"
  acerto: "#276d2c"
  erro: "#c62828"
  duvida: "#f9a825"
  duvida-texto: "#855800"
  acerto-noite: "#8fcf8f"
  erro-noite: "#f28b82"
  duvida-noite: "#f2c25b"
typography:
  display:
    fontFamily: "Fraunces Variable, Georgia, serif"
    fontSize: "2.2rem"
    fontWeight: 500
    lineHeight: 1.15
  headline:
    fontFamily: "Fraunces Variable, Georgia, serif"
    fontSize: "1.6rem"
    fontWeight: 500
    lineHeight: 1.2
  title:
    fontFamily: "Fraunces Variable, Georgia, serif"
    fontSize: "1.05rem"
    fontWeight: 500
    lineHeight: 1.3
  body:
    fontFamily: "Inter Variable, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  small:
    fontFamily: "Inter Variable, system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Inter Variable, system-ui, sans-serif"
    fontSize: "0.7rem"
    fontWeight: 400
    letterSpacing: "0.1em"
  marca:
    fontFamily: "Fraunces Variable, Georgia, serif"
    fontSize: "0.95rem"
    fontWeight: 500
    letterSpacing: "0.28em"
rounded:
  fino: "4px"
  menu: "6px"
  campo: "8px"
  bolha: "10px"
  pilula: "999px"
spacing:
  xs: "0.4rem"
  sm: "0.75rem"
  md: "1.1rem"
  lg: "2rem"
  xl: "3rem"
components:
  acao-forte:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
    rounded: "{rounded.pilula}"
    padding: "0.25rem 1rem"
  acao-forte-hover:
    backgroundColor: "{colors.brasa}"
    textColor: "#ffffff"
  acao-suave:
    textColor: "{colors.tinta}"
    rounded: "{rounded.pilula}"
    padding: "0.32rem 1rem"
  acao-texto:
    textColor: "{colors.tinta-suave}"
    padding: "0"
  acao-texto-hover:
    textColor: "{colors.tinta}"
  campo:
    textColor: "{colors.tinta}"
    rounded: "{rounded.campo}"
    padding: "0.5rem 0.7rem"
  busca:
    textColor: "{colors.tinta-suave}"
    rounded: "{rounded.pilula}"
    padding: "0.3rem 0.5rem 0.3rem 0.9rem"
  barra-lateral:
    backgroundColor: "{colors.papel-lateral}"
    width: "13rem"
    padding: "1rem"
  gaveta-ia:
    backgroundColor: "{colors.papel-lateral}"
    width: "24rem"
    padding: "1.1rem 1.2rem"
---

# Design System: STUDIA

## Overview

**Creative North Star: "A mesa silenciosa"**

O STUDIA é o lugar onde se estuda por horas: pouca coisa na mesa, tudo no lugar, um único sinal de cor. A tela é papel creme (ou noite quente, no escuro) com tinta escura, e a hierarquia vem só da tipografia — Fraunces para o que tem nome e número, Inter para o resto. Não há caixas, contornos nem cartões: seções são um rótulo pequeno em caixa alta e um fio de 1px.

A densidade é de ferramenta, não de vitrine. Na visão geral aparece só o assunto e os números (dias até a prova, `9/9`, `0%`); enunciados, legendas e referências moram no detalhe, quando o item é aberto. O que é raro fica a um gesto: ações de linha aparecem no hover ou no foco, e apagar mora no menu `···`.

O laranja brasa é o sinal único de "aqui" e "agora": o item ativo, a aba atual, o traço do hover, a próxima aula. Verde, vermelho e amarelo existem só para marcar acerto, erro e dúvida. Rejeições confirmadas: o tema "Padrão" antigo, caixas com borda, botões com contorno e texto explicativo fixo na tela.

**Key Characteristics:**
- A casa da matéria é **Hoje**: a sessão do plano em foco, com o material a um clique.
- Texto puro em repouso; estado mostrado por cor e por um traço (embaixo ou à esquerda), nunca por moldura.
- Fraunces para títulos, unidades e números grandes; Inter para o texto corrido e controles.
- Um laranja de sinal; três cores semânticas só para marcação.
- Plano: sombra só no que flutua (gaveta, menus, busca, avisos).
- Dois temas de igual peso: Editorial claro e Editorial escuro.

## Colors

Uma paleta de papel e tinta, quente nos dois temas, com um único laranja brasa e três cores semânticas reservadas à marcação de questões.

### Primary
- **Laranja brasa** (`brasa` no claro, `brasa-noite` no escuro). Em letra no tema claro usa-se **brasa de texto** (`brasa-texto`), mais funda, para passar de 4,5:1 no papel; traços, foco, fundos e números grandes ficam com a brasa normal. No escuro as duas são iguais. Usos: o sinal de "aqui/agora". Traço de 2px do item ativo na barra lateral e nas listas verticais, sublinhado da aba ativa (1ª 2ª 3ª, Claro/Escuro/Sistema), sublinhado de hover das ações de texto, "Enviar ↵", a seta da próxima aula, o fundo de hover da ação forte e o anel de foco (a 70%).

### Neutral
- **Papel** (`papel`): fundo da página no tema claro.
- **Papel da lateral** (`papel-lateral`): barra lateral, gaveta da IA e menus flutuantes — um degrau mais escuro que o fundo.
- **Papel elevado** (`papel-elevado`): fundo de listas de opções (seletor) e do antigo cartão.
- **Tinta** (`tinta`): texto, e o fundo da ação forte.
- **Tinta suave** (`tinta-suave`): texto secundário, rótulos, ações de texto em repouso, números de questão não marcados.
- **Noite / Noite da lateral / Noite elevada** (`noite`, `noite-lateral`, `noite-elevado`): os mesmos três papéis no tema escuro.
- **Giz / Giz suave** (`giz`, `giz-suave`): texto e texto secundário no tema escuro.

Três tons derivados do texto, sempre por mistura e nunca como hex fixo: **fio** (texto a 14%) para separadores; **leve** (texto a 6%) para o fundo de ações suaves e campos; **realce** (brasa a 9%) para hover discreto.

### Semânticas (só marcação)
- **Acerto** (`acerto` / `acerto-noite`): questão acertada, tópico visto, selo "pronto", progresso.
- **Erro** (`erro` / `erro-noite`): questão errada, parte vermelha do fio de desempenho, hover de "apagar".
- **Dúvida** (`duvida` / `duvida-noite`): questão em dúvida, selo "revisar". No tema claro o amarelo não se lê como letra: traços usam `duvida`, texto usa **dúvida de texto** (`duvida-texto`).

### Named Rules
**The Um Sinal Rule.** O laranja brasa marca uma coisa por região: o ativo, o próximo, o foco. Se dois elementos vizinhos pedem laranja, um deles está errado.

**The Letra Legível Rule.** Toda cor usada em letra passa de 4,5:1 no papel e na noite. Se o tom da marca não passa, ele ganha uma variante `-texto` e fica só para traços e superfícies.

**The Cor É Dado Rule.** Verde, vermelho e amarelo só aparecem quando dizem algo sobre a marcação do aluno. Nunca como decoração, categoria ou ênfase.

## Typography

**Display Font:** Fraunces Variable (com Georgia, serif)
**Body Font:** Inter Variable (com system-ui, sans-serif)

**Character:** Uma serifa editorial com contraste macio para o que tem nome e número, ao lado de uma sans neutra e muito legível para o trabalho. A serifa dá o tom de página impressa; a sans garante leitura longa sem cansaço.

### Hierarchy
- **Display** (Fraunces 500, 2.2rem, lh 1.15): o título de cada tela ("Hoje", "Tópicos da 3ª unidade", o nome do tópico, "Adicionar material"). A sessão do dia em Hoje usa 2rem. "Boa tarde." na tela inicial vai até 3.6rem.
- **Headline** (Fraunces 500, 1.6rem): identificação da questão aberta (`14.1 #22`), títulos de bloco grandes.
- **Title** (Fraunces 500, 1.05rem): assuntos e listas, abas de unidade, nomes de tópico, nome da matéria na lateral.
- **Body** (Inter 400, **16px de base**, lh 1.5; 1.6 em enunciados e resumos): texto corrido, itens de navegação, respostas da IA. O enunciado da questão sobe para 1.12rem.
- **Small** (Inter 400, 0.85rem): metadados, contagens, custo, ações dentro de cabeçalhos.
- **Label** (Inter 400, 0.7rem = 11,2px, tracking 0.1em, CAIXA ALTA, tinta suave): rótulos de seção ("SESSÃO DE HOJE", "PARA REVISAR", "LINHA 1"). Nunca abaixo de 11px.
- **Marca** (Fraunces 500, tracking 0.28em, caixa alta): só o nome STUDIA.

Números em contagens e grades usam `font-variant-numeric: tabular-nums`. Títulos quebram com `text-wrap: balance`; parágrafos e itens com `text-wrap: pretty`. Texto corrido longo (resumo, documento, resolução) fica em no máximo 42rem (≈70 caracteres, classe `.leitura-medida`).

### Named Rules
**The Serifa Nomeia Rule.** Fraunces é para o que tem nome ou é um número que decide algo. Texto de interface, controles e parágrafos ficam em Inter.

**The Sem Sobretítulo Rule.** Nada de rótulo pequeno em cima do título da tela: o título fala sozinho; data e contexto vêm ao lado ou embaixo.

## Layout

Barra lateral fixa de 13rem à esquerda e conteúdo fluido à direita com respiro de 2rem. A barra tem as **quatro áreas do estudo** (Hoje · Tópicos · Praticar · Biblioteca) em texto maior e, depois de um fio, o **apoio** em tinta suave (Plano completo, Folha de fórmulas, ＋ Material, Histórico). No topo de cada tela da matéria: abas de unidade, a prova (fora de Hoje, que a tem no cabeçalho), a busca (Ctrl K), Desfazer e "IA ›". Cada tela tem um título real (h1).

- **Hoje:** cabeçalho (título, data, prova à direita) e duas colunas 1.55fr / 1fr: à esquerda a sessão do plano (o foco da tela) e "Para revisar"; à direita "Próximos 7 dias" e os tópicos da unidade. A faixa "Reta final" entra por cima com 7 dias ou menos.
- **Tópico:** cabeçalho (voltar, título, estado, seções do livro) e duas colunas 1.5fr / 1fr: o resumo para ler (até 42rem) e, ao lado, questões, fórmulas e resoluções.
- **Praticar:** grade de números estreita (≥17rem, 0.8fr) e a questão aberta larga (1.5fr), cada coluna rolando por conta própria com a página parada; Biblioteca segue o mesmo modelo de altura fixa.

Ritmo de espaçamento: 0.4rem entre itens de uma linha, 0.6rem dentro de um bloco, 2–2.4rem entre blocos, 3–4rem entre colunas. Só computador; abaixo de 1100px as colunas empilham. Colunas de grade usam `minmax(0, 1fr)` para fórmulas largas rolarem dentro, sem empurrar a página.

### Named Rules
**The Fio Único Rule.** Nunca dois fios encostados: um elemento logo depois de outro com fio não ganha o seu.

## Elevation & Depth

Plano por padrão. A profundidade vem de tons (fundo → lateral → elevado, um degrau de papel por vez) e de fios, não de sombra. Sombra só existe no que flutua por cima do conteúdo, e sempre escura e difusa; o véu da gaveta escurece a página a 45%.

### Shadow Vocabulary
- **Gaveta** (`box-shadow: -18px 0 40px rgb(0 0 0 / 35%)`): a gaveta da IA, que abre por cima da página.
- **Menu** (`box-shadow: 0 8px 24px rgb(0 0 0 / 30%)`): menu `···`.
- **Opções** (`box-shadow: 0 12px 32px rgb(0 0 0 / 28%)`): lista aberta do seletor.
- **Diálogo** (`box-shadow: 0 24px 60px rgb(0 0 0 / 35%)` e `0 4px 16px rgb(0 0 0 / 20%)`): busca da matéria e avisos.

### Named Rules
**The Só Flutua Rule.** Nada que está no fluxo da página tem sombra. Se tem sombra, está por cima de algo.

## Shapes

Formas mínimas: a maior parte da interface não tem forma nenhuma, só texto. Onde existe superfície, ela é pílula (ações suaves e fortes, busca, seletor de nível) ou um retângulo de cantos discretos — 8px nos campos, 10px na bolha da pergunta do aluno, 6px em menus, 4px no seletor. Indicadores de estado são traços retos: 2px à esquerda (item ativo), 2px embaixo (número de questão marcado), 1.5px embaixo (aba ativa, marcação Acertei/Errei/Dúvida).

## Components

Precisos e discretos: formas mínimas e alinhadas, sem enfeite, com o estado sempre legível.

### Buttons
- **Três tipos, nenhum com contorno.** A escolha é pela importância, não pelo gosto.
- **Ação de texto** (secundária: descartar, detalhes, fechar, desfazer, "+ sessão"): só a palavra em tinta suave; no hover vai para tinta com sublinhado brasa (offset 3px).
- **Ação suave** (principal de uma área: Ver no livro, Ver resolução, atalhos da IA): pílula sem borda, fundo leve (texto a 6%), padding 0.32rem 1rem; hover sobe para texto a 11%.
- **Ação forte** (uma por tela, no máximo: Confirmar no Importar): pílula cheia, fundo tinta e letra papel, peso 500; hover vira brasa.
- **Desabilitado:** opacidade 50%.
- **Foco:** anel de 2px em brasa a 70%, afastado 2px, em tudo que recebe teclado.

### Marcação e números de questão
- **Marcação** (✓ Acertei, ✗ Errei, ? Dúvida): texto com símbolo; a marcada ganha a cor semântica, peso 500 e sublinhado de 1.5px. Clicar de novo desmarca.
- **Números de questão:** soltos, sem caixa, em tinta suave; marcados ganham a cor semântica e um traço de 2px embaixo; a questão aberta fica em negrito na cor do texto.

### Selos
- Texto pequeno colorido (0.78rem), sem fundo nem borda: próxima em brasa, vista/pronto em verde, revisar em amarelo, pendente em tinta suave.

### Inputs / Fields
- **Estilo:** sem borda, fundo leve, cantos de 8px (chat, chave da API). A busca é uma pílula com o atalho `Ctrl K` à direita em 0.72rem.
- **Foco:** o anel global em brasa.
- **Exceção atual:** o seletor (lista suspensa) ainda tem contorno fino que vira brasa no hover e um halo de 3px no foco.

### Navigation
- **Barra lateral:** fundo papel da lateral, marca STUDIA no topo, matéria como seletor serifado, itens em texto. Ativo: traço brasa de 2px à esquerda + negrito. Hover: traço brasa a 45%. Grupos separados por fio. Seletor de tema no rodapé: **Claro · Escuro · Sistema** em texto, o ativo sublinhado em brasa.
- **Abas de unidade (1ª 2ª 3ª):** Fraunces 1.05rem, tinta suave; ativa em tinta com traço brasa de 1.5px embaixo.

### Sessão de hoje (signature)
O foco de Hoje: rótulo "SESSÃO DE HOJE · S3" (com "feita" em verde quando há trabalho), o título da sessão em Fraunces 2rem, o detalhe em tinta suave e, depois de um fio, o material numa lista de definição (rótulo à esquerda, item à direita): **Livro** (abre o PDF na página), **Resumo**, **Fórmulas** (quantas, da seção), **Questões** (números por lista, com a marcação e um traço pontilhado quando há resolução gravada). Embaixo, a única ação forte da tela: "Começar pelas questões".

### Questão aberta (Praticar)
`15.4 #7` em Fraunces 1.6rem com "‹ Anterior · Próxima ›" à direita; o enunciado em 1.12rem; o enunciado original do livro logo abaixo, recuado por um fio de 1px à esquerda; a marcação; e, depois de um fio, **uma só área de ajuda em abas** (Ajuda da IA · Resposta do livro · Resolução · Fórmulas). A IA da questão traz o seletor de nível **Dica · Caminho · Esboço · Resolução** (N1–N4 no nome acessível) numa pílula leve; **Resolução** pergunta antes, numa linha.

### Gaveta da IA
A IA da matéria (plano e dúvidas gerais, ou a seção pedida da Biblioteca): painel de 24rem que desliza da direita por cima da página, fundo papel da lateral, fio à esquerda e a sombra de gaveta. No topo diz sobre o que conversa; embaixo, a chave do Gemini. A pergunta do aluno numa bolha leve de 10px à direita, a resposta em texto corrido, o campo preso ao pé com o custo do mês e "Enviar ↵" em brasa.

### Primeiros passos
Matéria vazia: título, uma frase, três passos numerados (número em Fraunces brasa; o arquivo em peso 500 e o que ele vira) e o botão forte "＋ Adicionar material".

### Linha com ações ocultas
Linhas do mapa de Tópicos, do Plano, da Folha de fórmulas e do Histórico mostram ↑ ↓ editar e `···` só no hover, no foco por teclado ou com o menu aberto (transição de opacidade de 160ms).

## Do's and Don'ts

### Do:
- **Do** separar seções com um rótulo em caixa alta (0.7rem sobre 16px de base, tracking 0.1em) e um fio de 1px (texto a 14%).
- **Do** organizar cada tela pelo que o aluno faz na sessão (a sessão de hoje, o tópico, a questão), não pelo tipo de dado guardado.
- **Do** mostrar progresso que se deriva sozinho (datas do plano, marcações, resoluções); nunca pedir registro manual para a tela fazer sentido.
- **Do** mostrar estado com cor e traço: 2px à esquerda para o item ativo de lista vertical, 2px embaixo para número marcado, 1.5px embaixo para aba e marcação.
- **Do** limitar texto corrido a 42rem e quebrar títulos com `text-wrap: balance`.
- **Do** escolher o tipo de ação pela importância: texto para o secundário, suave para o principal da área, forte só uma vez por tela.
- **Do** deixar ações raras a um gesto (hover, foco, `···`) e garantir que apareçam também com Tab.
- **Do** derivar fio, leve e realce por mistura com o texto ou a brasa, para que funcionem nos dois temas.
- **Do** usar `--destaque-texto` e `--dub-texto` sempre que a cor for de letra; `--destaque` e `--dub` só em traços, fundos e números grandes.
- **Do** deixar a contagem da prova em brasa só com 7 dias ou menos; no dia, "hoje" e a frase "Boa prova.".
- **Do** transições curtas (160ms ease) e respeitar `prefers-reduced-motion`.

### Don't:
- **Don't** usar caixas, cartões com borda ou contornos em botões.
- **Don't** usar o laranja brasa como decoração ou em mais de um sinal por região.
- **Don't** usar verde, vermelho ou amarelo fora da marcação de acerto, erro e dúvida.
- **Don't** pôr sombra em nada que está no fluxo da página.
- **Don't** colocar parágrafos explicativos fixos na tela; estado vazio é uma frase curta, ajuda longa vai para o `title` ou para o detalhe.
- **Don't** encostar dois fios.
- **Don't** trazer de volta o tema "Padrão" nem cores fora das duas paletas Editorial.
- **Don't** pôr rótulo pequeno em cima do título da tela, nem texto abaixo de 11px.
- **Don't** abrir uma segunda superfície de IA para a mesma coisa: a da questão fica na questão; a da matéria, na gaveta.
