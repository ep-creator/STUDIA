# Redesenho minimalista do STUDIA — design

**Data:** 2026-10-28 · **Branch base:** `refatoracao/fase-6-assistente`
**Esboços aprovados:** `.superpowers/brainstorm/700-1793189126/content/` (`listas-combinada.html`,
`painel-3-completo-v3.html`, `painel-sem-faixa.html`, `painel-topicos.html` (regras), `ia-importar-historico.html`
(Importar e Histórico), `assistente-gaveta-pagina.html`).

## 1. Objetivo

Levar o app inteiro para a linguagem da barra lateral, que o usuário apontou como referência: texto puro, hierarquia
pela tipografia, um único sinal de estado, respiro e quase nenhum enfeite. Duas metas, nesta ordem:

1. **Útil:** na visão geral, só o que ajuda a decidir o próximo clique. Enunciados, legendas secundárias, referências
   de livro em cada linha e listas descritivas ficam no detalhe (ao abrir o item), não na visão geral.
2. **Belo:** sem caixas, contornos nem pílulas com borda; seções separadas por um rótulo pequeno e um fio.

Nenhuma função some. O que é pouco usado fica a um gesto (passar o mouse, menu “···”).

## 2. Decisões do usuário

| Pergunta | Decisão |
|---|---|
| Alcance | Aparência + esconder o que é raro (hover ou menu “···”) |
| Temas | Ficar só com o Editorial (claro e escuro); o tema Padrão sai |
| Questão aberta | Grade do esboço B, marcação do A, botões e chat do C |
| Texto | Menos texto: assunto + números na visão geral |
| Painel | Faixa de cima Prova · Próxima aula · Tópicos vistos; embaixo Para revisar · Desempenho; sem semana, sessões nem próximo passo |
| IA | Abre por cima da página (gaveta), não espreme o conteúdo |
| Assistente | Página própria na barra lateral, com as conversas existentes; sem “+ nova conversa” |

## 3. Linguagem visual (vale para todas as telas)

### 3.1 Temas

- Ficam só `editorial-claro` e `editorial-escuro`. Saem as paletas `padrao-*` de `temas/temas.css`, a identidade
  `padrao` de `estado/tema.svelte.ts` e todas as regras `:root[data-tema^='padrao']`/`^='editorial'` dos componentes:
  o que hoje é condicional ao Editorial passa a ser o estilo único.
- Preferência salva com `identidade: 'padrao'` é lida como Editorial (sem quebrar quem já tem a chave
  `estudos.tema` no navegador). O tipo `Identidade` deixa de existir; fica só o `Modo`.
- O seletor de tema do rodapé da barra lateral vira texto em linha: **Claro · Escuro · Sistema**, o ativo com o traço
  laranja embaixo. Na tela inicial, o mesmo, no canto.

### 3.2 Três tipos de ação

| Tipo | Aparência | Uso |
|---|---|---|
| **texto** | só a palavra, cor `--suave`; ao passar o mouse, `--texto` com sublinhado laranja | ações secundárias: descartar, detalhes, fechar, abrir, desfazer, “+ sessão” |
| **suave** | pílula sem borda, fundo `--leve` (texto a 6%), sem contorno | ações principais de uma área: Ver no livro, Ver resolução, Ler o resumo, atalhos da IA |
| **forte** | pílula cheia (fundo `--texto`, letra `--fundo`) | uma por tela, no máximo: Confirmar (Importar) |

A classe global `.botao` com borda deixa de existir; viram `.acao-texto`, `.acao-suave` e `.acao-forte` em
`temas.css`. Os 51 usos de `.botao` são migrados um a um para o tipo certo.

### 3.3 Estado

- **Marcação da questão** (Acertei/Errei/Dúvida): texto com símbolo; a marcada fica na cor da marca e sublinhada
  (1,5 px). Clicar de novo na marcada desmarca — o botão **Limpar** sai.
- **Números de questão** (grade das Listas, Para revisar): número solto, sem caixa; marcado ganha a cor da marca e um
  traço de 2 px embaixo; a questão aberta fica em negrito na cor do texto.
- **Item ativo de uma lista vertical** (barra lateral, fila do Importar, lista de documentos, conversas do Assistente):
  traço laranja de 2 px à esquerda + negrito — o gesto da barra lateral.
- **Abas em linha** (1ª 2ª 3ª, Claro/Escuro/Sistema): texto serifado; a ativa com traço laranja embaixo.
- **Selos** (pendente, próxima, vista, revisar, pronto): texto pequeno colorido, sem fundo nem borda — próxima/agora
  em laranja, vista/pronto em verde, revisar em amarelo, pendente em cinza.
- **Progresso:** fio de 1 px na cor `--fio`, preenchido com 2 px de verde (acertos) e vermelho (erros).

### 3.4 Estrutura

- **Sem caixas.** `.cartao` perde borda e fundo. A moldura com etiqueta (`MolduraEditorial`, “CÁLCULO 2 · 2026.2 /
  3ª UNIDADE”) é trocada por uma linha com os dois rótulos pequenos (matéria à esquerda, unidade à direita) e um fio
  embaixo.
- **Seções** = rótulo pequeno em caixa alta (`.rotulo`) + conteúdo; faixas separadas por um fio de 1 px.
- **Nunca dois fios encostados:** um elemento logo depois de outro com fio não ganha o seu (`.x + .y { border-top: 0 }`).
- **Ações de linha** (↑ ↓ editar apagar em Tópicos, Cronograma, Formulário; detalhes no Histórico) ficam invisíveis
  até passar o mouse **ou** a linha receber foco do teclado (`:hover, :focus-within`). Apagar vai para dentro do “···”.
- **Números grandes** (dias até a prova, x/y, %): Fraunces 3 rem, sufixo pequeno em `--suave`.
- **Campos:** sem borda, fundo `--leve`, cantos 8 px (busca, chat, API key, novo tópico pode ser só sublinhado).

### 3.5 Menos texto

Saem os parágrafos explicativos fixos (Importar, Histórico, chave do Gemini, Para revisar vazio). Estado vazio vira
uma frase curta (“Nada para revisar ainda.”). Ajuda longa, se precisar, vai para o `title` do elemento.

## 4. Telas

### 4.1 Topo (todas as telas da matéria)

1ª 2ª 3ª como abas em linha (§3.3) · “Prova em 33 dias” / “Prova já foi · seg 14/09” em `--suave` · busca como
campo suave · “↶ Desfazer” e “IA ›” como ações de texto. Abaixo, a linha matéria/unidade com fio (§3.4).

### 4.2 Listas

- Lista de tópicos à esquerda: título serifado + contagem `9/9` em `--suave`; “LINHA 1/2” como rótulo; grade de
  números (§3.3).
- Questão aberta à direita, separada por um fio vertical, sem cartão:
  - `14.1 #22` (Fraunces) e o título da lista em `--suave`;
  - marcação em texto (§3.3), sem Limpar;
  - enunciado;
  - **Ver no livro** e **Ver resolução** como ações suaves (o “Abrir o livro na p.” já saiu);
  - **N1 N2 N3 N4** num seletor suave único (pílula com os quatro; o último usado em destaque) e “···” ao lado com
    Recomeçar;
  - conversa e chat como no esboço C: bolha do usuário com fundo leve, resposta em texto corrido, campo com fundo
    leve, rodapé com custo em `--suave` e “Enviar ↵” em laranja.

### 4.3 Painel

Duas faixas, sem caixas:

1. **Prova | Próxima aula | Tópicos vistos**
   - Prova: “33 dias” + data; unidade com prova passada mostra “feita” + data.
   - Próxima aula: o tópico com status `proxima` (senão o primeiro `pendente`) — a mesma regra do `ProximoPasso`
     atual —, em Fraunces, com “ler o resumo” como ação de texto quando houver resumo ligado. Sem data nesta fase
     (o app não sabe a data das aulas). Some quando não há tópico pendente.
   - Tópicos vistos: `0/8` grande, fio de progresso e os tópicos em colunas: ✓ verde (visto), seta laranja (o da
     próxima aula), ○ cinza (pendente). Sem referências de livro.
2. **Para revisar | Desempenho nas listas**
   - Para revisar: agrupado por lista (título serifado) e só os números das questões com ✗ ou ?, no estilo da grade.
     Clicar no número abre a questão nas Listas. Vazio: “Nada para revisar ainda.”
   - Desempenho: `% feito` e `% de acerto` grandes (“—” sem marcação) e uma linha por lista: nome, `feitas/total`,
     fio verde/vermelho.

Saem do Painel: semana (`SemanaPainel`), sessões, próximo passo (`ProximoPasso`), legendas extras como “9/38 da
linha 1”. O Cronograma continua sendo o lugar da semana.

### 4.4 Tópicos

Linha = selo em texto (§3.3) · título · seções do livro como links pequenos em `--suave` · ações no hover (↑ ↓
editar ···). Novo tópico: campo de uma linha, Enter adiciona (sem botão “+ Adicionar”).

### 4.5 Cronograma

Mesmo padrão de linha: data em `--suave`, código (P3, S1) e foco; ✎ e o marcar como feito no hover; feito em verde
como selo de texto. “+ Sessão” vira ação de texto ao lado do título. O texto do foco fica em uma linha (o restante ao
abrir/editar).

### 4.6 Formulário

Fórmulas sem caixa, separadas por fio; título como rótulo pequeno; ✎ e apagar no hover. “+ Fórmula” e “Folha para
imprimir” viram ações de texto ao lado do título.

### 4.7 Documentos

Lista à esquerda com o padrão de item ativo (§3.3, já é assim); “+ Novo documento” vira ação de texto; “Resumir a
seção” vira ação suave.

### 4.8 Importar

Título “Importar” · área de soltar em uma linha com borda tracejada (“Solte os PDFs aqui ou *escolha arquivos*”) ·
fila: nome + estado em selo de texto (pronto, revisar N, lendo…), item aberto com traço laranja · proposta à direita,
separada por fio: tipo (Fraunces), resumo curto em `--suave`, “tipo: lista ⌄” para trocar, itens numerados com
“conferir” em amarelo nos que pedem revisão · **Confirmar** (forte) e “descartar” (texto). O selo de confiança
detalhado vira o `title` do “conferir”.

### 4.9 Histórico

Título + “Ctrl+Z desfaz a última” pequeno no canto (sai o parágrafo). Linha: hora em negrito + dia em `--suave` ·
descrição · “detalhes” no hover · “↶ desfazer” em laranja só na mais recente. Desfeitas riscadas.

### 4.10 IA: gaveta por cima

- O botão “IA ›” abre uma gaveta de 24 rem fixa à direita, **sobre** a página: o conteúdo não muda de largura
  (`.ia` sai do fluxo do `.app`; vira `position: fixed`). Um véu escurece o resto; Esc, o ✕ ou clicar no véu fecham.
  Foco vai para o campo ao abrir e volta ao botão ao fechar.
- Dentro: “Assistente” + fechar; atalho do papel (Plano de revisão / Resumir a seção) como ação suave; “abrir em
  página ↗” (vai para a página do Assistente com a conversa aberta); “···” com Recomeçar; conversa e chat como nas
  Listas. Sem chave: só a caixa “API key”.
- “Ver resolução” não precisa mais recolher a IA (a gaveta não ocupa espaço da página); a regra sai de
  `DetalheQuestao`.

### 4.11 Página do Assistente

- Novo item **Assistente** na barra lateral, num grupo próprio entre as telas da matéria e Importar/Histórico. Rota
  `#/m/<uid>/assistente` (como `importar`/`historico`, sem unidade).
- Duas colunas: à esquerda as conversas **ativas** da matéria, agrupadas em Geral · Questões · Seções, cada uma com
  o rótulo e quando foi usada (“hoje”, “ontem”, “12/09”), a aberta com traço laranja; à direita a conversa aberta
  (mesmo `PainelIA`, mais largo). Sem “+ nova conversa”: o Recomeçar do “···” basta, porque o uso principal
  (resolução de questão, resumo) gera conversas curtas.
- **Backend:** `GET /api/materias/{uid}/agente/conversas` → lista de `{id, alvo, papel, rotulo, atualizada_em}` das
  conversas ativas que têm ao menos uma mensagem, mais recentes primeiro. `rotulo`: `geral` → “Geral”;
  `questao:<id>` → “<código da lista> #<rótulo>”; `secao:<id>` → “<código> <título>”. `atualizada_em` = data da última
  mensagem. Nenhuma mudança de tabela.

## 5. Fora do escopo

- Datas das aulas (a Próxima aula fica sem data).
- Mudanças no comportamento do agente, da busca ou do Histórico além do que está aqui.
- Responsividade para celular além do que já existe.
- Remover a rota `GET …/agente/contexto` (sem uso na tela desde a retirada do “Copiar o contexto”) — pode sair junto,
  se o plano achar barato.

## 6. Testes e verificação

- Testes do Vitest que procuram textos, botões ou papéis alterados são atualizados no mesmo passo da mudança (ex.:
  Limpar some; clicar na marca ativa desmarca; ações de linha existem no DOM e aparecem com foco; a gaveta fecha com
  Esc; a página do Assistente lista as conversas).
- Backend: teste da rota de conversas (ordem, rótulos dos três tipos de alvo, conversa vazia fora da lista).
- `npm run check` sem erros nem avisos; suíte completa do backend e do frontend verdes.
- Conferência visual numa cópia temporária, Editorial claro e escuro, em cada tela da §4, comparando com os esboços.
- Teclado: tudo que aparece no hover também aparece com foco; a gaveta prende e devolve o foco.
