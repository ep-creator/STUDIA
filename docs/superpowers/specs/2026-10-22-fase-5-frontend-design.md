# Fase 5 — Frontend Novo: Especificação de Design

> Complementa `2026-10-20-refatoracao-plataforma-design.md` (§10 e §11). Decisões tomadas com o usuário em 2026-10-22,
> com mockups no companheiro visual (`.superpowers/brainstorm/`).

## 1. Objetivo e contexto

Trocar o uso diário do app antigo (`Calculo 2/_app/web`, uma página longa por unidade) por um app novo sobre o motor
(`_app/backend`), mais fácil de usar e mais lógico, em que **criar uma matéria nova é só dar um nome e soltar os PDFs**.

**O que o usuário pediu:**
- organização mais clara;
- criar matéria só com cliques;
- Svelte com build e KaTeX;
- a IA fica para a Fase 6, mas com os espaços dela já reservados;
- uso no notebook;
- uma identidade visual ousada, além do claro/escuro.

**Premissas assumidas:**
- roda só no computador do usuário, sem login;
- o app novo convive com o antigo até a Fase 7;
- rodar online é uma possibilidade futura, não planejada, para a qual o desenho deixa costuras baratas (§10).

## 2. Decisões

| Tema | Decisão |
|---|---|
| Organização | Barra lateral com áreas, e o **painel da unidade** como tela inicial da matéria |
| Painel | Prova com contagem regressiva, progresso dos tópicos, cronograma de hoje e próximos dias, importações pendentes |
| Listas | Grade de questões (clique troca ✓ → ✗ → ? → vazio) + painel da questão selecionada |
| Importação | Fila de arquivos + proposta do arquivo selecionado, com selo de confiança e "por quê?"; serve também para criar matéria |
| Anotação por questão | Fora desta fase |
| IA | Espaços reservados (componente único `EspacoIA`, "chega na Fase 6") |
| Dispositivo | Notebook (tela grande); no celular funciona, sem cuidado especial |
| Visual | Duas identidades × claro/escuro: **Padrão** e **Editorial** (padrão do app), seguindo o tema do sistema, com botão para trocar |
| Tecnologia | Svelte 5 + Vite + TypeScript, **sem SvelteKit**; arquivos estáticos servidos pelo próprio motor |
| App antigo | Só não recebe mudanças; o congelamento em `legado/` passa para a **Fase 7** (o agente antigo segue em uso até a Fase 6) |

## 3. Identidade visual

Cores definidas como variáveis CSS em `src/temas/`; a escolha é guardada no navegador (`localStorage`).

| Tema | Fundo | Texto | Destaque | Observações |
|---|---|---|---|---|
| Padrão claro | `#fafaf7` (lateral `#f2f1ec`) | `#1f2328` | `#3b82f6` | cartões brancos com borda suave, cantos de 10px |
| Padrão escuro | `#15171c` (lateral `#1b1e24`) | `#e6e6e6` | `#7c9cff` | cartões `#1e2128`, bordas `#2a2d35` |
| Editorial claro | `#f3ece0` | `#141413` | `#d9572b` | serifa (Fraunces) nos títulos e números grandes; moldura fina com rótulos nas bordas ("CÁLCULO 2 · 2026.2", "UNIDADE 1"); botões só com contorno |
| Editorial escuro (escuro quente) | `#191714` | `#efe6d6` | `#f07a45` | mesmo desenho do claro; moldura e linhas em creme a 65% |

- **Tipografia:** Inter para o texto; Fraunces para títulos e números no Editorial. As duas fontes ficam empacotadas no app
  (`@fontsource`), sem buscar na internet.
- **Cores de marcação nos quatro temas:** ✓ verde, ✗ vermelho, ? amarelo.
- **Selos de confiança:** verde (≥ `limiar_confianca`), amarelo (revisar), vermelho (sem palpite).

## 4. Telas

**Estrutura fixa da matéria:**
- **Barra lateral:**
  - seletor de matéria;
  - Painel, Tópicos, Listas, Cronograma, Documentos, Formulário;
  - divisor, Importar (com selo de pendências) e Histórico;
  - botão de tema no rodapé.
- **Topo:** botões das unidades, contagem até a prova e ↩ Desfazer (também Ctrl+Z).
- **À direita:** faixa recolhível do `EspacoIA`.

| Tela | Conteúdo | Componentes |
|---|---|---|
| Matérias (início) | Cartões com nome, nº de unidades, prova mais próxima e importações pendentes; "＋ Nova matéria" pede o nome e leva à Importação | `CartaoMateria` |
| Painel | Contagem até a prova (data e hora), progresso dos tópicos com atalho para o próximo, agenda de hoje e próximos dias, pendências de importação | `ContagemProva`, `ProgressoTopicos`, `AgendaCurta` |
| Tópicos | Árvore da unidade; status que muda com um clique entre **pendente, próxima e visto** (os valores do banco: `pendente`, `proxima`, `visto`); seção do livro com atalho; listas ligadas; criar, renomear, reordenar e apagar | `ArvoreTopicos`, `SeloStatus` |
| Listas | Grade de todas as listas da unidade, com placar por lista. A questão selecionada mostra o enunciado (KaTeX), o atalho para a página do livro ou PDF e o tutor reservado | `GradeQuestoes`, `DetalheQuestao`, `Placar` |
| Cronograma | Linha do tempo: sessões de estudo + aulas, feriados, extras e a prova do calendário; criar e editar sessão; marcar como feita | `LinhaDoTempo`, `EditorSessao` |
| Documentos | Lista à esquerda (resumos, resoluções, anotações, livros e PDFs); leitor Markdown com KaTeX; editor com prévia lado a lado; PDF aberto na página certa; sumário do livro | `ListaDocumentos`, `Markdown`, `EditorMarkdown`, `VisualizadorPdf` |
| Formulário | Fórmulas agrupadas por tópico, LaTeX com prévia ao digitar, modo "folha para imprimir" | `CartaoFormula`, `EditorFormula` |
| Importar | Área para soltar arquivos; fila com tipo detectado e nº de pendências; proposta do arquivo selecionado com selos e "por quê?"; confirmar, trocar tipo, descartar, "confirmar todos sem pendências"; "indexando…" enquanto o livro entra na busca | `AreaSoltar`, `FilaImportacao`, `PropostaPrograma`, `PropostaCalendario`, `PropostaTurma`, `PropostaLivro`, `PropostaLista`, `SeloConfianca` |
| Histórico | Ações agrupadas com horário; desfazer a última; "ver diferença" de documentos editados | `ItemHistorico`, `Diferenca` |

**Comportamentos de todas as telas:**
- **Avisos curtos com ação:** por exemplo, "Questão 15.4 #11 marcada ✗ · Desfazer".
- **Erros:** mostram a mensagem do motor.
- **Estados vazios guiam o próximo passo:** por exemplo, "Envie o programa para criar as unidades → Importar".
- **Teclado na grade:** setas para navegar; 1, 2 e 3 marcam ✓, ✗ e ?.
- **Textos de apresentação:** "1ª unidade" e "Cronograma da 1ª unidade" são montados pela tela a partir do número, nunca
  guardados.
- **PDF na página certa:** usa o leitor do navegador (`/arquivos/<uid>/<caminho>#page=N`).
  - Para exercícios de livro, a página é a do início da seção (`secao_livro.pagina_pdf_ini`).
  - Para questões com `pagina_pdf`, é a da questão.

## 5. Arquitetura do frontend

```
_app/frontend/
├── src/
│   ├── api/         cliente único + tipos gerados do OpenAPI (openapi-typescript)
│   ├── rotas/       Materias, Painel, Topicos, Listas, Cronograma, Documentos, Formulario, Importacao, Historico
│   ├── componentes/ peças reutilizáveis (§4) + BarraLateral, Topo, SeletorUnidade, Aviso, EspacoIA
│   ├── estado/      matéria e unidade atuais, painel carregado, tema, avisos
│   └── temas/       4 paletas em variáveis CSS
├── tests/           Vitest (unidade/componentes) e Playwright (ponta a ponta)
└── dist/            build (fora do Git)
```

**Regras:**
1. **Nenhuma tela chama `fetch` direto:** tudo passa por `src/api`. A URL base é configurável, e os erros do motor
   (`{"erro": "..."}`) viram um único tipo de erro.
2. **Os tipos da API são gerados** do OpenAPI do motor (`npm run tipos`). Mudança de formato vira erro de compilação.
3. **Roteamento por hash** (`#/m/<uid>/u/<n>/listas`): atualizar a página ou usar um favorito volta à mesma tela.
4. **Dados sempre da API.** No navegador ficam só as preferências (tema, última matéria e tela).
5. **Markdown:** `markdown-it` + KaTeX + DOMPurify (todo HTML renderizado passa pelo DOMPurify).
6. **Tudo empacotado** (fontes, KaTeX): o app funciona offline.

**Como roda:**
- **Uso:** o `_app/abrir-novo.bat` compila o frontend se o código-fonte for mais novo que o `dist/`, sobe o motor e abre
  `http://127.0.0.1:8790/`.
- **Desenvolvimento:** `npm run dev` (Vite, porta 5173), que repassa `/api` e `/arquivos` ao motor reescrevendo a origem
  para a do motor. O `OrigemLocalMiddleware` não ganha exceções.

## 6. Mudanças no motor

Todas aditivas, com testes. Nenhuma rota existente muda de formato.

1. **Servir o app:** `frontend/dist` em `/`; caminhos fora de `/api` e `/arquivos` devolvem `index.html`. Sem build,
   uma página explica como gerar.
2. **`GET /api/materias` com resumo:** `periodo`, `unidades` (quantidade), `proxima_prova` (`data`, `hora_inicio`,
   `unidade`) e `importacoes_pendentes` (quantidade).
3. **`GET …/painel` com três blocos novos:**
   - `eventos`: os da unidade exibida mais os gerais (segunda chamada, exame final);
   - `vinculos`: para cada tópico, as seções ligadas (`secao_id`, `codigo`, `titulo`, `fonte_id`, `caminho`,
     `pagina_pdf_ini`); para cada lista, tópicos e seção;
   - `importacoes_pendentes` (quantidade).
4. **`GET …/fontes`** (id, tipo, título, caminho, total de páginas) e **`GET …/fontes/{id}/secoes`** (sumário do livro).
5. **`GET …/historico/{grupo}`:** as mudanças da ação (tabela, chave, antes/depois) e, para documentos, o texto anterior e
   o posterior (de `.versoes/`).
6. **Conflito ao salvar documento:** o `PUT` de documento aceita a versão aberta (`atualizado_em` esperado). Se o arquivo
   mudou desde então, responde 409 com a versão atual, e a tela oferece ver antes de sobrescrever.

## 7. Fluxo de dados e erros

- **Fonte dos dados da unidade:** o painel, carregado ao trocar de matéria ou unidade, alimenta Painel, Tópicos, Listas,
  Cronograma e Formulário.
- **Sob demanda:** texto de documento, sumário de livro, importações, histórico e busca.
- **Marcações são otimistas:** a tela muda na hora e, se o motor recusar, volta e avisa.
- **Demais escritas:** esperam a resposta e recarregam o painel (as regras derivadas vivem no motor).
- **Desfazer** (botão ou Ctrl+Z): chama o motor, recarrega o que estiver aberto e avisa o que foi desfeito.
- **Importação:**
  - envio com progresso;
  - a lista de pendentes é relida depois de cada confirmação (traz as propostas recalculadas pelo motor);
  - edições da revisão vão por `PUT` (o motor guarda as decisões).
- **Erros:**
  - mensagem do motor num aviso;
  - validação junto do campo, sem perder o que foi digitado;
  - motor fora do ar: faixa "Motor desligado: abra o abrir-novo.bat", com nova tentativa automática;
  - conflito de documento conforme §6.6.

## 8. Testes

- **pytest:** cada item do §6.
- **Vitest:**
  - lógica: ciclo da marcação, contagem até a prova, textos de apresentação, explicação da confiança, cliente da API
    (erro do motor, motor fora do ar);
  - componentes: `GradeQuestoes`, `SeloConfianca`, `Markdown` (KaTeX e DOMPurify), `FilaImportacao`.
- **Playwright** (motor real, pasta temporária, PDFs reais de Cálculo 2):
  1. nova matéria → soltar programa, calendário, Stewart e listas → trocar a unidade da L1 na revisão → confirmar tudo
     → painel com a prova e os tópicos;
  2. marcar questões com mouse e teclado → placar → Ctrl+Z;
  3. abrir resumo → editar → salvar → ver a diferença no histórico;
  4. trocar os quatro temas e recarregar mantendo a escolha.
- **Integração contínua** (`.github/workflows/testes.yml`): passa a compilar o frontend e rodar o Vitest; o Playwright
  entra se o tempo do workflow permitir.

## 9. Critério de pronto

- [ ] **Todo o dia a dia do app antigo pelo novo:** ver onde está na unidade, marcar exercícios, acompanhar o cronograma,
  ler e editar resumos, consultar o formulário, abrir livro e PDFs na página certa.
- [ ] Matéria nova do zero só com cliques (nome → arquivos → revisão → confirmar).
- [ ] Desfazer em tudo, pelo botão e pelo Ctrl+Z.
- [ ] Quatro temas; Editorial como padrão seguindo o sistema; funciona offline.
- [ ] Espaços da IA visíveis e reservados.
- [ ] pytest, Vitest e Playwright verdes; o `abrir-novo.bat` abre o app novo.

## 10. Preparação para rodar online (possibilidade futura, fora do escopo)

**Já garantido pelo desenho do frontend:**
- cliente único com URL base configurável (onde entrariam token e "sessão expirada");
- nenhum caminho de pasta no frontend (arquivos sempre por rota da API);
- tudo endereçado pelo `uid` da matéria;
- preferências separadas dos dados.

**O que mudaria no motor:**
- PostgreSQL (ou SQLite por usuário) no lugar do SQLite por pasta;
- armazenamento de arquivos na nuvem;
- autenticação e checagem do dono da matéria em cada rota, no lugar do `OrigemLocalMiddleware`;
- fila de tarefas para a indexação;
- segredos (chave do Gemini) no ambiente do servidor.

Os repositórios concentram o acesso ao banco, então a troca de banco mexe principalmente neles. Para embeddings no
servidor, ver `2026-10-22-reestruturacao-inteligencia.md` §5.1.

## 11. Ordem de execução (o plano detalha)

1. Motor: §6.
2. Base do frontend: projeto, temas, fontes offline, cliente da API, roteador, barra lateral e topo.
3. Matérias e Painel.
4. Listas.
5. Tópicos, Cronograma e Formulário.
6. Documentos e leitor.
7. Importação.
8. Histórico, desfazer global e `EspacoIA`.
9. Playwright, integração contínua e `abrir-novo.bat`.

## 12. Fora do escopo desta fase

- renomear ou apagar matéria;
- refazer;
- anotação por questão;
- qualquer funcionalidade de IA (Fase 6);
- layout pensado para celular;
- rodar online.
