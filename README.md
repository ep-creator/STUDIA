# STUDIA

Plataforma local de estudos para disciplinas da faculdade, **construída inteira conversando com uma IA**. Você solta os
PDFs da matéria (programa, calendário, livros, listas, slides), e ela monta as unidades, os tópicos, as listas e as
seções do livro; marca o que você acertou e errou, mostra o que revisar e tem um assistente que ajuda nas questões,
escreve resumos e monta o plano até a prova.

Roda no próprio computador, em `http://127.0.0.1:8790`, e guarda tudo em arquivos na pasta do projeto.

## Sumário

- [Começar em um minuto](#começar-em-um-minuto)
- [Guia de uso](#guia-de-uso)
  - [Abrir](#abrir)
  - [Criar uma matéria](#criar-uma-matéria)
  - [As telas da matéria](#as-telas-da-matéria)
  - [Buscar](#buscar)
  - [Desfazer](#desfazer)
  - [Assistente (IA)](#assistente-ia)
  - [Tema](#tema)
  - [Problemas comuns](#problemas-comuns)
- [A ideia do projeto](#a-ideia-do-projeto)
  - [O experimento](#o-experimento)
  - [O problema que ele resolve](#o-problema-que-ele-resolve)
  - [Os princípios](#os-princípios)
  - [Como uma plataforma inteira foi construída conversando](#como-uma-plataforma-inteira-foi-construída-conversando)
  - [Números](#números)
  - [De onde veio](#de-onde-veio)
- [Tecnologia e evolução](#tecnologia-e-evolução)
  - [Visão geral](#visão-geral)
  - [A stack](#a-stack)
  - [Como as peças funcionam](#como-as-peças-funcionam)
  - [A evolução](#a-evolução)
  - [Desenvolvimento](#desenvolvimento)
- [Estrutura de pastas](#estrutura-de-pastas)

## Começar em um minuto

1. Instale **Python 3.13** e **Node.js**.
2. Dê dois cliques em **`abrir.bat`**, na raiz.
3. No navegador, crie uma matéria e solte os PDFs em **Importar**.

O resto está no [Guia de uso](#guia-de-uso).

## Guia de uso

### Abrir

Dê dois cliques em **`abrir.bat`**, na raiz do projeto. Ele abre uma janela de terminal e o app fica em
**http://127.0.0.1:8790**.

- Na primeira vez, ele cria o ambiente Python do motor e instala as dependências. Isso demora alguns minutos.
- Depois, ele só recompila a interface quando o código mudou, então abrir fica rápido.
- Para fechar, feche a janela do terminal.

Requisitos: **Python 3.13** e **Node.js** (a interface é compilada no seu computador).

Tudo fica na pasta do projeto: nada vai para a nuvem, exceto as perguntas que você fizer ao assistente (elas vão para o
Gemini, se você configurar a chave).

### Criar uma matéria

1. Na tela inicial, clique em **＋ Nova matéria** e dê um nome (ex.: *Cálculo 2*).
2. Vá em **Importar** e solte os PDFs da disciplina na área tracejada: programa, calendário, informações da turma,
   livros, listas de exercícios, slides. Pode mandar tudo de uma vez, em qualquer ordem.
3. Cada arquivo entra na **fila** com um estado:
   - **pronto**: o app entendeu tudo com segurança;
   - **revisar N**: N itens pedem a sua conferência.
4. Clique num arquivo para ver o que o app entendeu (unidades, datas, tópicos, questões, seções do livro). Se o tipo
   estiver errado, troque em **tipo**. Corrija o que precisar e clique em **Confirmar** (ou **descartar**).

Nada é gravado sem a sua confirmação. Itens marcados com **conferir** são os que o app não teve certeza.

Cada matéria vira uma pasta na raiz do projeto, com o banco (`materia.db`), os PDFs (`fontes/`) e os textos
(`conteudo/`).

### As telas da matéria

A barra lateral leva às áreas da matéria. No topo, **1ª 2ª 3ª** trocam de unidade e o texto ao lado diz quanto falta
para a prova.

#### Painel

A visão geral da unidade:

- **Prova**: os dias que faltam (ou *feita*, se já passou).
- **Próxima aula**: o tópico marcado como próximo, com um atalho para ler o resumo.
- **Tópicos vistos**: quantos já foram vistos, com cada tópico marcado (✓ visto, → próximo, ○ pendente).
- **Para revisar**: os números das questões que você marcou como errei ou dúvida, por lista. Clicar abre a questão.
- **Desempenho nas listas**: quanto já foi feito e a taxa de acerto, por lista.

#### Tópicos

A lista do que cai na prova. Clique no estado (*pendente → próxima → visto*) para avançar. Passe o mouse (ou use Tab)
numa linha para ver **↑ ↓** (reordenar), **editar** e o menu **···** (apagar). Para criar um tópico, escreva no campo
do fim e aperte Enter.

#### Listas

À esquerda, as listas da unidade com os números das questões; à direita, a questão aberta.

- **Marcar**: ✓ Acertei, ✗ Errei, ? Dúvida. Clicar de novo na marca ativa desmarca.
- **Teclado**: setas andam entre as questões; **1** acertei, **2** errei, **3** dúvida, **0** limpa.
- **Ver no livro**: o enunciado original do livro e a resposta do gabarito, quando a questão é um exercício do livro.
- **Ver resolução**: a resolução gravada, quando existe (fica escondida até você pedir, para não estragar a tentativa).
- **N1 N2 N3 N4**: pedem ajuda ao assistente, do mais leve ao mais completo (veja abaixo).

#### Cronograma

Aulas, provas e as suas sessões de estudo numa linha do tempo. **+ sessão** cria uma sessão; passe o mouse numa
sessão para **marcar feita** ou **editar**.

#### Documentos

Resumos, resoluções, planos e anotações (em Markdown, com fórmulas), e também os PDFs da matéria (livros, listas,
slides). Clique para ler; **editar** abre o editor. Num resumo ligado a uma seção do livro, **Resumir a seção** pede ao
assistente um resumo novo.

#### Formulário

As fórmulas da unidade, agrupadas por tópico. **+ fórmula** cria uma; **folha para imprimir** abre a impressão das fórmulas, numa folha para levar.

### Buscar

**Ctrl K** abre a busca da matéria inteira (livros, slides, listas, resumos). O resultado abre no lugar certo: o texto
no documento ou o PDF na página.

### Desfazer

Toda alteração fica registrada. **Ctrl Z** (ou **↶ Desfazer** no topo) desfaz a última, em qualquer tela. O
**Histórico** mostra tudo o que mudou, com **detalhes** de cada mudança.

### Assistente (IA)

O assistente usa o **Gemini**, do Google, e precisa de uma chave da API.

#### Configurar a chave

1. Crie uma chave de graça no **Google AI Studio**.
2. Abra **Assistente** na barra lateral. No fim da lista de conversas, em **API key**, clique em **colar** (ou
   **trocar**, para corrigir uma chave errada), cole a chave e aperte Enter.

A chave fica em `_app/.segredos.toml`, fora do Git, e nunca volta para a tela.

#### Onde usar

| Onde | Atalho | O que faz |
|---|---|---|
| Questão aberta (Listas) | **N1** Dica | só o conceito e o ponto de partida, sem contas |
| | **N2** Caminho | o roteiro em passos, sem resolver as contas |
| | **N3** Esboço | a estrutura com as passagens-chave |
| | **N4** Resolução | a resolução completa, já gravada como documento |
| Documento ligado a uma seção | **Resumir a seção** | escreve (ou melhora) o resumo e cria os cartões de fórmula |
| Painel e página do Assistente | **Plano de revisão** | diagnóstico dos erros e plano até a prova |

Você também pode escrever uma pergunta livre no campo de mensagem.

- **IA ›** no topo abre o assistente numa gaveta por cima da página (Esc fecha). **abrir em página ↗** leva a conversa
  para a página do Assistente, que lista todas as conversas da matéria.
- O assistente **cita** de onde tirou cada coisa (ex.: *[Stewart p. 312]*); clicar na citação abre o livro na página.
- O que ele grava (resolução, resumo, fórmula) aparece na conversa com **Abrir** e **Desfazer**.
- **Custo**: cada resposta mostra quanto custou em reais, e o rodapé mostra o total do mês. Se uma resposta for passar
  do **teto mensal** (R$ 20, ajustável em `_app/config.toml`), o app pede confirmação antes.
- O menu **···** tem **Recomeçar**, que abre uma conversa nova e vazia (a antiga fica guardada).

#### Sem chave

Sem chave, o resto do app funciona normalmente: só o assistente fica parado, mostrando a caixa **API key**.

### Tema

No pé da barra lateral: **Claro · Escuro · Sistema** (segue o Windows).

### Problemas comuns

- **"Não encontrei o Python 3.13"**: instale em https://www.python.org/downloads/ e abra de novo.
- **A interface não abre ou aparece antiga**: instale o Node.js (https://nodejs.org) e abra de novo; o `abrir.bat`
  recompila sozinho.
- **"O Gemini recusou a chave"**: o aviso traz o atalho **trocar a chave**.

## A ideia do projeto

### O experimento

O STUDIA é um experimento: **construir uma plataforma inteira só conversando com uma IA.** Ninguém escreveu o código à
mão. O autor (Enzo Priori, estudante) decidiu o que queria, aprovou cada desenho e testou as telas; a IA (Claude, no
Claude Code) escreveu todo o código, os testes e a documentação.

Isso costuma ser chamado de *vibe coding*. A proposta aqui foi levar a ideia até o fim, num software de uso diário de
verdade, e não num protótipo: com banco de dados, importação de PDFs, busca, um assistente de IA, centenas de testes e
uma interface pensada tela por tela.

### O problema que ele resolve

Estudar uma disciplina de exatas é juntar muita coisa espalhada: o programa e o calendário da turma, um ou dois livros,
listas de exercícios, slides, as próprias anotações. Saber o que cai na prova, o que já foi feito e o que precisa ser
revisado vira um trabalho em si.

O STUDIA junta tudo isso por matéria e por unidade:

- você solta os PDFs, e ele monta sozinho as unidades, as datas, os tópicos, as listas e as seções do livro;
- você marca as questões que acertou, errou ou ficou em dúvida, e ele mostra o que revisar;
- um assistente ajuda a resolver questões em níveis (da dica à resolução completa), escreve resumos e monta um plano
  de revisão, sempre citando de onde tirou cada coisa.

Tudo roda no próprio computador, e os dados ficam em arquivos na pasta do projeto.

### Os princípios

Algumas regras guiaram todas as decisões:

1. **Organizar não depende de IA.** Criar uma matéria e ligar as peças é feito por regras explícitas, que dá para
   entender e conferir. A IA entra só no que exige raciocínio: explicar, resolver, resumir, planejar.
2. **Nada é adivinhado.** Toda decisão automática tem origem e uma nota de confiança; quando o app não tem certeza, ele
   pergunta em vez de gravar.
3. **Medir antes de trocar.** Uma técnica nova só entra se ganhar da atual num gabarito de casos reais. Foi assim que
   os embeddings ficaram desligados (veja [Tecnologia e evolução](#tecnologia-e-evolução)).
4. **Tudo se desfaz.** Toda alteração, sua ou do assistente, vai para o histórico e pode ser desfeita.
5. **Local e barato.** O que roda a cada busca ou importação roda offline. A API paga só para o que precisa de raciocínio,
   com o custo à vista e um teto mensal.
6. **Útil antes de bonito, e bonito do jeito simples.** Na visão geral, só o que ajuda a decidir o próximo clique; o
   detalhe fica para quando você abre o item.

### Como uma plataforma inteira foi construída conversando

Cada fase seguiu o mesmo ciclo, sempre com o autor aprovando antes do passo seguinte:

1. **Conversa de desenho.** A IA pergunta o objetivo, propõe caminhos com prós e contras e mostra esboços das telas no
   navegador. O autor escolhe.
2. **Especificação.** O desenho aprovado vira um documento (`docs/superpowers/specs/`), que o autor revisa.
3. **Plano.** A especificação vira um plano de tarefas pequenas, cada uma com os testes que provam que ficou pronta
   (`docs/superpowers/plans/`).
4. **Execução com testes primeiro.** Para cada tarefa, a IA escreve o teste, vê falhar, escreve o código e vê passar.
5. **Revisão.** No fim de cada fase, um revisor novo (outra instância da IA, sem o contexto da conversa) lê o trabalho
   inteiro e aponta problemas; os importantes são corrigidos, cada um com um teste.
6. **Uso de verdade.** O autor usa o app, manda capturas de tela e diz o que incomoda; os ajustes entram antes do merge.

Esse ciclo é o que permitiu ir longe sem perder o controle: o autor não precisava ler o código, mas lia e aprovava
cada decisão, e os testes garantiam que o que já funcionava continuava funcionando.

### Números

Em 9 dias (20 a 28 de outubro de 2026):

- 7 fases de refatoração, 14 pull requests;
- mais de 150 commits;
- cerca de 620 testes no motor, 180 na interface e 6 de ponta a ponta;
- cada fase com especificação e plano escritos, e as decisões técnicas medidas em `docs/avaliacoes/`.

### De onde veio

Antes desta refatoração havia uma primeira versão, feita só para Cálculo 2: um app com os dados num arquivo JSON, um
agente que buscava em tudo e um índice de busca próprio. Ela funcionava, mas tudo era específico daquela disciplina
(números de seção, nomes de livros, quantidade de unidades escritos no código). A refatoração começou com uma pergunta:
dá para transformar isso numa plataforma para qualquer matéria, em que a organização sai das regras e não da IA? A
resposta está nas [fases](#a-evolução).

## Tecnologia e evolução

### Visão geral

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

### A stack

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

#### Pastas

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

### Como as peças funcionam

#### Dados e histórico

Cada matéria é uma pasta com `materia.db` (unidades, tópicos, listas, questões, marcações, cronograma, fórmulas,
vínculos), `fontes/` (PDFs) e `conteudo/` (Markdown com frontmatter). Toda escrita acontece dentro de uma **operação**
do histórico: ela grava, numa transação, o que mudou no banco e nos arquivos. Desfazer reaplica o estado anterior. O
assistente grava pelo mesmo caminho, então tudo o que ele faz também se desfaz.

#### Importação por regras

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

#### Busca

O índice guarda **trechos** de livros, slides, listas e documentos. Os livros são **cortados em teoria, exercícios e
respostas**: a busca olha a teoria, e os exercícios do livro aparecem à parte (é assim que "Ver no livro" acha o
enunciado original e a resposta do gabarito). A leitura dos PDFs é feita por fonte e posição, com tabelas que traduzem
as fontes matemáticas dos livros (letras gregas, operadores) em texto legível.

A busca padrão é **BM25** (FTS5) sobre radicais, com filtros exatos de unidade, seção e tipo. Embeddings e busca híbrida
existem, mas ficam desligados por padrão (veja a evolução).

#### Assistente

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

#### Interface

Svelte 5 com runes, sem biblioteca de componentes. Um tema só (**Editorial**, claro e escuro) e três tipos de ação sem
contorno: texto, suave e forte. Um teste (`scripts/estilo.test.ts`) prende as regras do estilo: falha se voltar um botão
com contorno, o tema antigo ou mais de uma ação forte por tela.

### A evolução

#### Fase 0: a primeira versão

Um app só para Cálculo 2: dados num JSON, um agente Gemini que buscava em tudo ("multi-busca") e um índice de busca
próprio em dois níveis. Funcionava, mas a organização dependia de valores fixos no código e do próprio agente.

#### Fases 1 a 5: a plataforma

| Fase | O que entrou |
|---|---|
| 1. Fundação | motor novo, segurança (só local), SQLite com migrações, repositórios, histórico com desfazer |
| 2. Migração | Cálculo 2 levado da primeira versão para o banco novo, por regras, com relatório de conferência |
| 3. Importação por regras | classificador, parsers, vínculos com nota de confiança, tela de revisão |
| 4. Busca | índice incremental, livros por seção, busca com filtros |
| 5. Interface | todas as telas em Svelte, com fórmulas, edição e desfazer; criar matéria só com cliques |

#### Fase 6: a inteligência, e por que o RAG ficou menor

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

#### Depois da Fase 6

- **Assistente**: os três papéis, ferramentas, calculadora segura, custo e teto, conversas por questão e seção.
- **Redesenho minimalista**: tema único, sem caixas, menos texto, a IA numa gaveta por cima da página e uma página só
  do Assistente.

#### O que ainda falta

- usar o assistente com a chave real e ajustar os papéis pelo que aparecer (o formato da API, o nome do modelo e os
  preços em `config.toml` ainda não foram conferidos contra o Gemini de verdade);
- melhorar o contexto da Geometria Analítica;
- rever a forma de ligar tópicos, seções e documentos (hoje por regras de semelhança de texto).

### Desenvolvimento

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

## Estrutura de pastas

```text
Refatoração Site Estudos/
├── abrir.bat             # abre o STUDIA
├── README.md
├── _app/                 # o aplicativo
│   ├── config.toml       # porta, limiares, busca, assistente (modelo, preços, teto)
│   ├── backend/          # motor: Python, FastAPI e SQLite
│   └── frontend/         # interface: Svelte 5, Vite e TypeScript
├── <Matéria>/            # uma pasta por matéria
│   ├── materia.db        # unidades, tópicos, listas, marcações, cronograma, histórico
│   ├── conteudo/         # resumos, resoluções, anotações e planos em Markdown
│   ├── fontes/           # PDFs: documentos da turma, listas e livros
│   └── figuras/          # imagens usadas pelos textos
└── docs/
    ├── avaliacoes/       # medições de busca, vínculos e contexto
    └── superpowers/      # especificações e planos de cada fase
```
