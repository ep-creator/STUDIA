# Tecnologia e evolução

[← README](../README.md) · [Guia de uso](guia.md) · [A ideia do projeto](ideia.md) · **Tecnologia e evolução**

---

## Visão geral

```text
navegador ──► interface (Svelte 5, compilada em _app/frontend/dist)
                │  fetch / NDJSON
                ▼
              motor (FastAPI, http://127.0.0.1:8790, só aceita requisições locais)
                ├── importação por regras ── PDFs ──► propostas para revisar
                ├── repositórios + histórico ──► materia.db (SQLite, um por matéria)
                ├── índice de busca (SQLite FTS5) ──► <matéria>/.indice/
                └── agente ──► Gemini (REST, streaming) + ferramentas locais
```

## A stack

| Parte | Tecnologia |
|---|---|
| Motor | Python 3.13, FastAPI, Uvicorn, Pydantic v2 |
| Banco | SQLite: um `materia.db` por matéria, com migrações em `estudos/db/migracoes/` |
| PDFs | PyMuPDF (leitura por fonte e posição, com tabelas para as fontes matemáticas dos livros) |
| Busca | SQLite FTS5 (BM25) sobre radicais das palavras; embeddings locais opcionais (`fastembed`, ONNX, só CPU) |
| Assistente | Gemini por REST (`httpx`, SSE), com chamadas de função |
| Calculadora do assistente | SymPy e SciPy, num processo separado com tempo limite |
| Interface | Svelte 5 (runes), Vite, TypeScript |
| Texto e fórmulas | markdown-it, KaTeX, DOMPurify |
| Testes | pytest (motor), Vitest + Testing Library (interface), Playwright (ponta a ponta) |

### Pastas

```text
_app/
├── config.toml           # porta, limiares, busca, assistente (modelo, preços, teto)
├── backend/estudos/
│   ├── api/              # rotas HTTP
│   ├── db/               # conexão, transações, migrações
│   ├── repos/            # acesso aos dados de cada tabela
│   ├── historico.py      # toda escrita passa por aqui (e pode ser desfeita)
│   ├── importacao/       # classificador, parsers, vínculos, leitura de PDF
│   ├── rag/              # índice, corte dos livros, busca
│   ├── ia/               # embeddings (opcionais)
│   ├── agente/           # modelo, papéis, contexto, ferramentas, laço, custo
│   └── avaliacao/        # gabaritos e o comando que mede busca, vínculos e contexto
└── frontend/src/
    ├── rotas/            # uma tela por área (Painel, Listas, Assistente…)
    ├── componentes/
    ├── estado/           # estado compartilhado (matéria, tema, IA…)
    └── temas/temas.css   # paleta Editorial e as classes de ação
```

## Como as peças funcionam

### Dados e histórico

Cada matéria é uma pasta com `materia.db` (unidades, tópicos, listas, questões, marcações, cronograma, fórmulas,
vínculos), `fontes/` (PDFs) e `conteudo/` (Markdown com frontmatter). Toda escrita acontece dentro de uma **operação**
do histórico: ela grava, numa transação, o que mudou no banco e nos arquivos. Desfazer reaplica o estado anterior. O
assistente grava pelo mesmo caminho, então tudo o que ele faz também se desfaz.

### Importação por regras

Um PDF passa por quatro etapas:

1. **Classificação** por pontos: datas e dias da semana sugerem calendário; "Unidade" e tópicos, programa; sumário,
   livro; "Questão 1.", lista.
2. **Extração** por parsers de regras explícitas: unidades, provas, tópicos, seções do livro (pelos marcadores do PDF
   ou pela página de sumário), questões com linha 1 e linha 2.
3. **Vínculos** por semelhança de texto (Jaccard ponderado por IDF sobre radicais): tópico ↔ seção do livro, lista ↔
   tópico, documento ↔ seção.
4. **Revisão**: tudo vira uma proposta. Cada item tem uma nota de confiança de 0 a 1; abaixo de `limiar_confianca`
   (0,75) ele aparece como **conferir**, e abaixo de `limiar_vinculo` (0,35) a ligação nem é proposta.

Nenhum dado de uma disciplina específica está no código: sem números de seção, nomes de livro ou quantidade de
unidades fixos.

### Busca

O índice guarda **trechos** de livros, slides, listas e documentos. Os livros são **cortados em teoria, exercícios e
respostas**: a busca olha a teoria, e os exercícios do livro aparecem à parte (é assim que "Ver no livro" acha o
enunciado original e a resposta do gabarito). A leitura dos PDFs é feita por fonte e posição, com tabelas que traduzem
as fontes matemáticas dos livros (letras gregas, operadores) em texto legível.

A busca padrão é **BM25** (FTS5) sobre radicais, com filtros exatos de unidade, seção e tipo. Embeddings e busca híbrida
existem, mas ficam desligados por padrão (veja a evolução).

### Assistente

O assistente tem três **papéis**, cada um num arquivo de texto em `estudos/agente/papeis/`:

| Papel | Onde aparece | Ferramentas |
|---|---|---|
| tutor | questão aberta (N1–N4) | buscar, ler seção, exercício do livro, calcular, salvar resolução |
| resumidor | seção do livro | buscar, ler seção, calcular, salvar resumo, adicionar fórmula |
| estrategista | painel e página do Assistente | buscar, ler seção |

A cada pedido:

1. **O app monta o contexto antes do modelo.** Pela tela aberta, ele já sabe o que importa: para uma questão, junta o
   enunciado, o exercício original do livro com a resposta, a teoria da seção ligada, o resumo e a resolução gravada.
   Cada pedaço vai com um rótulo para citar (ex.: *[Stewart p. 312]*).
2. **O modelo responde em streaming** e pode pedir ferramentas. O app executa só as permitidas para o papel e devolve o
   resultado, até 6 rodadas.
3. **A resposta chega na tela em pedaços** (NDJSON): texto, aviso de ferramenta, "gravado", erro e fim.
4. **O custo é calculado** com os tokens do Gemini e os preços em `config.toml` (em dólar, convertidos pela cotação), e
   somado ao total do mês. Passar do teto pede confirmação.

A **calculadora** nunca executa código vindo do modelo. A conta passa por uma lista branca de caracteres, funções e
nomes de variável, vira expressão do SymPy e roda num processo separado com tempo limite; integral que não fecha vai
para a integração numérica do SciPy.

### Interface

Svelte 5 com runes, sem biblioteca de componentes. Um tema só (**Editorial**, claro e escuro) e três tipos de ação sem
contorno: texto, suave e forte. Um teste (`scripts/estilo.test.ts`) prende as regras do estilo: falha se voltar um botão
com contorno, o tema antigo ou mais de uma ação forte por tela.

## A evolução

### Fase 0: a primeira versão

Um app só para Cálculo 2: dados num JSON, um agente Gemini que buscava em tudo ("multi-busca") e um índice de busca
próprio em dois níveis. Funcionava, mas a organização dependia de valores fixos no código e do próprio agente.

### Fases 1 a 5: a plataforma

| Fase | O que entrou |
|---|---|
| 1. Fundação | motor novo, segurança (só local), SQLite com migrações, repositórios, histórico com desfazer |
| 2. Migração | Cálculo 2 levado da primeira versão para o banco novo, por regras, com relatório de conferência |
| 3. Importação por regras | classificador, parsers, vínculos com nota de confiança, tela de revisão |
| 4. Busca | índice incremental, livros por seção, busca com filtros |
| 5. Interface | todas as telas em Svelte, com fórmulas, edição e desfazer; criar matéria só com cliques |

### Fase 6: a inteligência, e por que o RAG ficou menor

O plano original da Fase 6 era reforçar o RAG: **embeddings locais**, **busca híbrida** (texto + sentido, fundidos por
Reciprocal Rank Fusion) e embeddings também nos vínculos da importação. A regra era medir antes de trocar, com
gabaritos de perguntas reais revisados pelo autor.

**A primeira medição favoreceu a híbrida.** Com perguntas escritas à mão, a híbrida (modelo `multilingual-e5-small`)
subiu o acerto em paráfrases de 65% para 75%, sem perder nas buscas exatas.

**A medição de uso real virou o jogo.** Quando o gabarito passou a ter as perguntas do dia a dia (161 perguntas, a
maioria gerada das próprias questões das listas, do tipo "me ajude nesta questão"), a busca por texto ganhou: **91% de acerto contra 84%** da híbrida, com indexação
quase 10 vezes mais rápida. Nos vínculos, os embeddings também não ajudaram: **51 de 58 contra 52 de 58** das regras,
porque o modelo acha quase todo par de textos de matemática parecido.

Resultado: os embeddings **ficaram no código, mas desligados** (`embeddings = false`, `busca = "texto"`,
`vinculos_com_embeddings = false` em `config.toml`). A melhoria veio por outro caminho:

- **Dados mais limpos em vez de busca mais esperta.** Os livros passaram a ser cortados em teoria, exercícios e
  respostas, e a leitura dos PDFs passou a entender as fontes matemáticas.
- **Contexto montado pelo app em vez de buscado pelo modelo.** Em vez de um agente que procura tudo (como na primeira
  versão), o app já sabe, pelos vínculos do banco, qual seção, exercício e resumo pertencem à questão aberta, e entrega
  isso pronto. A busca continua existindo, mas como **ferramenta** que o modelo usa quando falta algo.

Medido: em Cálculo 2, **98%** das perguntas de questão (118 de 121) já têm a resposta certa no contexto inicial, sem o
modelo precisar buscar. Na Geometria Analítica, que tem menos vínculos, são **55%**: é o próximo ponto a melhorar.

Os números e as regras de decisão (fixadas antes de medir) estão em `docs/avaliacoes/`.

### Depois da Fase 6

- **Assistente**: os três papéis, ferramentas, calculadora segura, custo e teto, conversas por questão e seção.
- **Redesenho minimalista**: tema único, sem caixas, menos texto, a IA numa gaveta por cima da página e uma página só
  do Assistente.

### O que ainda falta

- usar o assistente com a chave real e ajustar os papéis pelo que aparecer (o formato da API, o nome do modelo e os
  preços em `config.toml` ainda não foram conferidos contra o Gemini de verdade);
- melhorar o contexto da Geometria Analítica;
- rever a forma de ligar tópicos, seções e documentos (hoje por regras de semelhança de texto).

## Desenvolvimento

```bash
# motor (em _app/backend)
.venv/Scripts/python.exe -m pytest -q

# interface (em _app/frontend)
npm test          # Vitest
npm run check     # svelte-check e TypeScript
npm run e2e       # Playwright, ponta a ponta
npm run build

# avaliação de busca, vínculos e contexto (em _app/backend)
.venv/Scripts/python.exe -m estudos.avaliacao --help
```

As especificações e os planos de cada fase ficam em `docs/superpowers/`; as medições, em `docs/avaliacoes/`.
