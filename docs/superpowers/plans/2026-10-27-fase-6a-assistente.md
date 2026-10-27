# Peça A — O assistente · Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** trazer de volta o assistente (tutor N1–N4, resumidor e estrategista) sobre o banco e a busca novos, com
conversa por questão ou seção, gravação pelo Histórico, custo com teto e calculadora segura.

**Architecture:** o motor ganha o pacote `estudos/agente/` (modelo, contexto, ferramentas, calculadora, papéis, laço,
conversas, custo, segredos). Uma rota de streaming (NDJSON) roda o laço e a tela (`EspacoIA` → painel) mostra a
conversa aos pedaços. O Gemini fica atrás de `agente/modelo.py`; os testes usam `ModeloFalso`.

**Tech Stack:** Python 3.13, FastAPI, SQLite, httpx (REST do Gemini, `streamGenerateContent?alt=sse`), SymPy, SciPy;
Svelte 5 + TS, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-27-fase-6a-assistente-design.md`

## Global Constraints

- Nenhum código vindo do modelo é executado; a calculadora só aceita contas pela lista branca (Task 3).
- O que o agente grava (resolução, resumo, fórmula) passa por `ctx.acao`/`operacao` (Histórico) com `origem="agente"`.
  As conversas e mensagens não passam pelo Histórico.
- A chave do Gemini fica só em `_app/.segredos.toml` (no `.gitignore`); nenhuma rota a devolve.
- Padrões do `[agente]`: `modelo = "gemini-3.8-flash"`, `teto_mensal_brl = 20`, `max_rodadas = 6`,
  `tempo_limite_s = 60`, `cotacao_dolar` e `[agente.precos]` (US$ por milhão de tokens, entrada e saída). Os preços e
  a cotação iniciais são estimativas; o `config.toml` diz para o usuário conferir na página de preços do Gemini.
- Dependências do motor: `httpx>=0.27` (sai do `dev`), `sympy>=1.13`, `scipy>=1.14`.
- Testes não chamam a API; o teste real usa o marcador `gemini` e fica fora por padrão
  (`addopts = "-m 'not modelo and not gemini'"`).
- Rótulos de citação no texto do modelo e do contexto: `[Stewart p. 312]`, `[Aula 11 p. 6]`,
  `[resumo 14.1 — 2. Definições]`, `[Lista 14.1 #22]`.
- Backend: `cd _app/backend && .venv/Scripts/python -m pytest -q`; frontend: `cd _app/frontend && npm test` e
  `npm run check`; tipos: gerar o OpenAPI do app sobre uma pasta temporária e `npm run tipos -- <arquivo.json>`.
- Nunca commitar `Calculo 2/`, `Geometria Analítica/`, `calculo 1(teste)/`, `.claude/`,
  `docs/superpowers/specs/2026-10-22-sugestao-antigravity-fase-6-embeddings-ia.md`; commits terminam com
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. Expressão maliciosa ou inválida na calculadora (`__import__('os')`, `().__class__`, `open('x')`, texto enorme):
   recusada sem executar nada — `test_calculadora_recusa_entrada_perigosa` (Task 3).
2. Conta que o SymPy não termina (integral difícil): a calculadora responde em até 10 s com o valor numérico ou "não
   consegui" — `test_calculadora_tem_tempo_limite` (Task 3).
3. Gemini cai no meio da resposta: o que já chegou fica guardado e a tela recebe `erro` — `test_erro_no_meio_guarda_o_parcial`
   (Task 6).
4. Questão sem seção, sem exercício no livro ou matéria sem livro: o contexto sai só com o que existe, sem erro —
   `test_contexto_de_questao_sem_livro` (Task 5).
5. Dois pedidos ao mesmo tempo na mesma conversa (clique duplo): as mensagens não se misturam — o segundo recebe
   `erro` "já estou respondendo" — `test_pedido_simultaneo_na_mesma_conversa` (Task 7).

---

### Task 1: Configuração, segredos e custo

**Files:**
- Modify: `_app/backend/estudos/config.py` (`Settings`, `_MAPA_TOML`), `_app/config.toml` (seção `[agente]`),
  `_app/backend/pyproject.toml`, `.gitignore`
- Create: `_app/backend/estudos/agente/__init__.py`, `agente/segredos.py`, `agente/custo.py`
- Test: `_app/backend/tests/test_agente_config.py`

**Interfaces:**
- Produces:
  - `Settings` ganha `agente_modelo: str = "gemini-3.8-flash"`, `teto_mensal_brl: float = 20.0`,
    `cotacao_dolar: float = 5.6`, `max_rodadas: int = 6`, `tempo_limite_s: int = 60`,
    `agente_precos: dict[str, dict[str, float]]` (padrão `{"gemini-3.8-flash": {"entrada": 0.30, "saida": 2.50}}`).
  - `ler_chave(app_dir: Path) -> str | None`; `gravar_chave(app_dir: Path, chave: str) -> None` (arquivo
    `_app/.segredos.toml`, chave `gemini`).
  - `custo_brl(settings: Settings, modelo: str, tokens_entrada: int, tokens_saida: int) -> float` (modelo sem preço →
    usa o do `agente_modelo`; arredonda em 4 casas).

- [ ] **Step 1: Testes** — `test_config_le_a_secao_agente` (toml com `[agente]` e `[agente.precos]` vira os campos),
  `test_chave_gravada_fora_do_git` (`gravar_chave` + `ler_chave`; o caminho está no `.gitignore`: `git check-ignore`),
  `test_custo_em_reais` (1 milhão de entrada + 1 milhão de saída a 0,30/2,50 e cotação 5,6 → `round(2.8*5.6, 4)`),
  `test_modelo_sem_preco_usa_o_padrao`.
- [ ] **Step 2: Ver falhar.** **Step 3: Implementar** (dependências no `pyproject.toml` e `pip install -e .`).
  **Step 4: Ver passar.**
- [ ] **Step 5: Commit** — `feat: configuração do agente, chave fora do Git e custo em reais`

### Task 2: Conversas e mensagens

**Files:**
- Create: `_app/backend/estudos/db/migracoes/0006_agente.sql`, `_app/backend/estudos/agente/conversas.py`
- Test: `_app/backend/tests/test_agente_conversas.py`

**Interfaces:**
- Produces:
  - tabelas `conversa (id, papel, alvo, ativa INTEGER, criada_em)` e `mensagem (id, conversa_id, autor, texto,
    tokens_entrada, tokens_saida, custo_brl, modelo, criada_em)`, `autor IN ('voce','agente','ferramenta')`,
    `papel IN ('tutor','resumidor','estrategista')`.
  - `@dataclass Conversa(id, papel, alvo)`, `@dataclass Mensagem(id, autor, texto, custo_brl, criada_em)`.
  - `conversa_ativa(con, alvo: str, papel: str) -> Conversa` (cria se não há); `recomecar(con, alvo, papel) -> Conversa`;
    `mensagens(con, conversa_id: int) -> list[Mensagem]`;
    `adicionar(con, conversa_id, autor, texto, tokens_entrada=0, tokens_saida=0, custo_brl=0.0, modelo=None) -> int`;
    `total_do_mes(workspace: Path, hoje: date) -> float` (soma em todas as matérias, só leitura);
    `estimativa(workspace: Path) -> float` (maior custo entre as 10 últimas respostas do workspace, ou 0,05).
  - Escrita direta com `commit` (fora do Histórico).

- [ ] **Step 1: Testes** — `test_uma_conversa_ativa_por_alvo_e_papel`, `test_recomecar_arquiva_e_abre_outra`
  (mensagens antigas continuam no banco, a nova vem vazia), `test_total_do_mes_soma_as_materias` (duas matérias, mês
  anterior fora), `test_conversa_nao_entra_no_historico` (nenhum `historico_grupo` novo), `test_estimativa_padrao`.
- [ ] **Step 2–4.** **Step 5: Commit** — `feat: conversas do agente guardadas na matéria`

### Task 3: Calculadora segura

**Files:**
- Create: `_app/backend/estudos/agente/calculadora.py`
- Test: `_app/backend/tests/test_agente_calculadora.py`

**Interfaces:**
- Produces: `calcular(pedido: dict) -> dict`. Pedido: `operacao` ∈ `integral | derivada | limite | resolver |
  pontos_criticos | avaliar`; `expressao: str` (ou `expressoes: list[str]` em `resolver`); `variaveis: list[str]`;
  `limites: list[[str, str]]` (integral, um par por variável, de dentro para fora); `ponto: str` (limite);
  `ordem: list[str]` (derivada). Resposta: `{"resultado": str, "numerico": float | None}` ou `{"erro": str}`.

Segurança: antes de qualquer análise, o texto passa por uma lista branca — até 500 caracteres; só dígitos, letras,
espaço e `+-*/^().,` ; cada identificador precisa ser uma variável do pedido ou um nome de
`{sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, exp, log, ln, sqrt, pi, E, oo, Abs}`; nada de `__`. Só então
`parse_expr` com `global_dict` contendo apenas esses nomes. O cálculo roda num processo separado
(`multiprocessing`, 10 s); integral simbólica que não termina cai para `scipy.integrate.nquad`.

- [ ] **Step 1: Testes** — `test_integral_dupla_em_polares` (r·1 em r∈[0,1], θ∈[0,2π] → π),
  `test_derivada_parcial`, `test_limite`, `test_pontos_criticos_de_lagrange` (`resolver` do sistema ∇f = λ∇g, g),
  `test_avaliar_numerico`, `test_calculadora_recusa_entrada_perigosa` (os exemplos do Review Focus 1 → `erro`, e um
  arquivo-sentinela não é criado), `test_calculadora_tem_tempo_limite` (integral sem forma fechada → `numerico`
  preenchido ou `erro` em < 12 s).
- [ ] **Step 2–4.** **Step 5: Commit** — `feat: calculadora segura do agente (SymPy/SciPy, sem executar código)`

### Task 4: Modelo (Gemini) e modelo falso

**Files:**
- Create: `_app/backend/estudos/agente/modelo.py`
- Test: `_app/backend/tests/test_agente_modelo.py`

**Interfaces:**
- Produces:
  - Eventos: `@dataclass Texto(texto: str)`, `@dataclass Chamada(nome: str, argumentos: dict)`,
    `@dataclass Uso(entrada: int, saida: int)`.
  - `@dataclass Turno(autor: str, texto: str | None = None, chamadas: list[Chamada] = (), resultados: list[tuple[str, dict]] = ())`
    — `autor` em `usuario | modelo | ferramenta`.
  - `class Modelo(Protocol)`: `nome: str`; `responder(sistema: str, turnos: list[Turno], ferramentas: list[dict]) -> Iterator[Texto | Chamada | Uso]`.
  - `class ErroModelo(Exception)` com `motivo` (`sem_chave | chave_invalida | indisponivel | limite_de_uso | tempo_esgotado`).
  - `class Gemini(Modelo)`: `__init__(chave: str, modelo: str, tempo_limite_s: int)`; POST em
    `https://generativelanguage.googleapis.com/v1beta/models/{modelo}:streamGenerateContent?alt=sse` com cabeçalho
    `x-goog-api-key`, `systemInstruction`, `contents` (turnos → `role: user|model`, partes `text`,
    `functionCall`, `functionResponse`) e `tools: [{functionDeclarations}]`; cada evento SSE vira `Texto`/`Chamada`;
    `usageMetadata` vira `Uso`. HTTP 400/403 → `chave_invalida`, 429 → `limite_de_uso`, 5xx/rede → `indisponivel`.
  - `class ModeloFalso(Modelo)`: `__init__(rodadas: list[list[Texto | Chamada | Uso | ErroModelo]])`; cada chamada a
    `responder` consome uma rodada (um `ErroModelo` na lista é levantado naquele ponto) e guarda `self.pedidos`.

- [ ] **Step 1: Testes** — `test_gemini_monta_a_requisicao` (com `httpx.MockTransport`: corpo com systemInstruction,
  contents e functionDeclarations; cabeçalho da chave; nunca a chave na URL), `test_gemini_le_texto_chamada_e_uso_do_sse`,
  `test_gemini_erros_viram_motivo` (403, 429, 503, tempo), `test_modelo_falso_roteiriza_rodadas`.
- [ ] **Step 2–4.** **Step 5: Commit** — `feat: modelo do agente (Gemini por REST) e modelo falso para testes`

### Task 5: Papéis e contexto inicial

**Files:**
- Create: `_app/backend/estudos/agente/papeis/tutor.md`, `resumidor.md`, `estrategista.md`, `agente/papeis.py`,
  `agente/contexto.py`
- Test: `_app/backend/tests/test_agente_contexto.py`

**Interfaces:**
- Consumes: `buscar_modo`, `exercicio_de`, `resposta_de`, `secao_completa` (rag), repositórios de listas, documentos,
  marcações, eventos e tópicos.
- Produces:
  - `@dataclass Papel(nome, instrucoes: str, ferramentas: list[str], modelo: str | None)`; `carregar_papel(nome) -> Papel`
    (frontmatter `ferramentas`, `modelo`; corpo = instruções).
  - `ATALHOS: dict[str, str]` — `N1` "Nível N1 (dica): só o conceito e o ponto de partida, sem contas.", `N2` "Nível N2
    (caminho): o roteiro em passos, sem resolver as contas.", `N3` "Nível N3 (esboço): a estrutura com as passagens-chave,
    deixando as contas finais.", `N4` "Nível N4 (resolução completa no padrão prova): resolva e grave com
    salvar_resolucao.", `resumir` "Resuma a seção no formato dos meus resumos, grave com salvar_resumo e crie os cartões
    de fórmula.", `plano` "Monte o diagnóstico e o plano de revisão até a próxima prova.".
  - `@dataclass Pedaco(rotulo: str, texto: str)`; `montar_contexto(con, raiz: Path, alvo: str, papel: str) -> list[Pedaco]`
    (conteúdo por alvo como na spec §3.2; índice desatualizado → sem trechos do livro e um `Pedaco("aviso", …)`);
    `contexto_em_texto(pedacos) -> str`; `rotulo_de(resultado: Resultado, fontes) -> str`.

- [ ] **Step 1: Testes** (com o `cenario_busca` e listas/documentos montados) — `test_contexto_de_questao` (enunciado,
  exercício do livro com resposta, trechos da seção com rótulo `[livro p. N]`, resumo ligado), `test_contexto_de_secao`,
  `test_contexto_geral_traz_marcacoes_e_prova`, `test_contexto_de_questao_sem_livro` (Review Focus 4),
  `test_papeis_carregam_ferramentas_e_instrucoes`.
- [ ] **Step 2–4.** **Step 5: Commit** — `feat: papéis do agente e contexto inicial da tela`

### Task 6: Ferramentas e laço de uma resposta

**Files:**
- Create: `_app/backend/estudos/agente/ferramentas.py`, `agente/laco.py`
- Test: `_app/backend/tests/test_agente_laco.py`

**Interfaces:**
- Consumes: Tasks 1–5.
- Produces:
  - `@dataclass Ferramenta(nome, descricao, parametros: dict, grava: bool, executar: Callable[[Ambiente, dict], dict])`;
    `FERRAMENTAS: dict[str, Ferramenta]` com `buscar`, `ler_secao`, `exercicio_do_livro`, `calcular`,
    `salvar_resolucao`, `salvar_resumo`, `adicionar_formula`; `declaracoes(nomes) -> list[dict]` (formato
    `functionDeclarations`).
  - `@dataclass Ambiente(con, raiz: Path, settings, alvo: str, acao: Callable[[str], ContextManager[Operacao]])`.
    As que gravam usam `ambiente.acao("Agente: …")` e devolvem `{"gravado": {"tipo", "id", "titulo", "grupo_id"}}`.
  - Eventos de saída: `@dataclass Saida(tipo: str, dados: dict)` com `tipo` em `texto | ferramenta | gravado | confirmar
    | erro | fim`.
  - `responder(ambiente: Ambiente, modelo: Modelo, papel: Papel, texto: str, confirmado: bool, workspace: Path, hoje: date) -> Iterator[Saida]`
    — ordem da spec §3.5: teto (`total_do_mes + estimativa > teto` e não confirmado → `confirmar` e para); guarda a
    mensagem `voce`; monta o sistema (instruções + contexto) e os turnos (últimas 20 mensagens `voce`/`agente`); laço
    de até `max_rodadas` com ferramentas; erro de ferramenta vira resultado `{"erro": …}`; `ErroModelo` → guarda o
    parcial como mensagem `agente` e emite `erro`; no fim guarda a mensagem `agente` com tokens e custo e emite `fim`
    com `custo_brl` e `total_mes`.

- [ ] **Step 1: Testes** (com `ModeloFalso`) — `test_resposta_simples_guarda_e_custa`, `test_ferramenta_de_busca_volta_para_o_modelo`,
  `test_n4_grava_resolucao_pelo_historico_e_desfaz` (documento `resolucao` ligado à questão, origem `agente`;
  `desfazer_ultimo` remove), `test_salvar_resumo_e_formula`, `test_teto_pede_confirmacao` (e com `confirmado=True`
  segue), `test_limite_de_rodadas`, `test_erro_de_ferramenta_vira_resultado`, `test_erro_no_meio_guarda_o_parcial`
  (Review Focus 3).
- [ ] **Step 2–4.** **Step 5: Commit** — `feat: ferramentas e laço do agente`

### Task 7: API do agente

**Files:**
- Create: `_app/backend/estudos/api/agente.py`
- Modify: `_app/backend/estudos/main.py` (registrar o router), `estudos/api/respostas.py`, `estudos/api/esquemas.py`,
  `_app/frontend/src/api/tipos.gerados.ts` (regenerado)
- Test: `_app/backend/tests/test_api_agente.py`

**Interfaces:**
- Consumes: `responder`, `conversas`, `montar_contexto`, `carregar_papel`, `ATALHOS`, `ler_chave`, `gravar_chave`.
- Produces (spec §4):
  - `POST /api/materias/{uid}/agente/mensagem` — corpo `PedidoAgente(alvo: str, papel: str, texto: str | None,
    atalho: str | None, confirmado: bool = False)`; `StreamingResponse` `application/x-ndjson`, uma `Saida` por linha.
    O gerador abre a própria conexão (`conectar(materia.db)`) e usa `operacao(...)` + `podar` para as gravações. Sem
    chave → uma linha `erro` com `motivo: "sem_chave"`. Uma conversa por vez: trava por (`materia`, `alvo`, `papel`);
    ocupada → `erro` "já estou respondendo" (Review Focus 5). `modelo` injetável por `app.state.fabrica_modelo` para os
    testes.
  - `GET …/agente/conversa?alvo&papel` → `ConversaSaida(id, alvo, papel, mensagens)`;
    `POST …/agente/conversa/recomecar` (corpo `alvo`, `papel`) → `ConversaSaida`.
  - `GET …/agente/contexto?alvo&papel&atalho` → `PacoteContexto(texto: str)` (instruções + contexto + pedido).
  - `GET /api/agente/estado` → `EstadoAgente(chave_configurada: bool, modelo: str, total_mes: float, teto: float)`;
    `PUT /api/agente/chave` (corpo `{"chave": str}`) → `Ok`.

- [ ] **Step 1: Testes** — `test_mensagem_em_streaming` (linhas `texto…fim` com o modelo falso),
  `test_sem_chave_avisa`, `test_estado_nao_expoe_a_chave`, `test_conversa_e_recomecar`, `test_pacote_de_contexto`,
  `test_pedido_simultaneo_na_mesma_conversa`.
- [ ] **Step 2–4** (e regenerar os tipos). **Step 5: Commit** — `feat: API do agente com resposta em streaming`

### Task 8: Painel do assistente na tela

**Files:**
- Create: `_app/frontend/src/api/agente.ts`, `_app/frontend/src/componentes/PainelIA.svelte`,
  `PainelIA.test.ts`, `_app/frontend/src/componentes/ConfigurarChave.svelte`
- Modify: `estado/ia.svelte.ts` (`ia` ganha `alvo` e `papel`), `componentes/EspacoIA.svelte` (vira o invólucro do
  painel), `componentes/DetalheQuestao.svelte` (alvo `questao:<id>`, papel tutor), `App.svelte` (alvo do contexto
  geral), `rotas/Documentos.svelte` (botão "Resumir a seção" com resumo ou seção aberta)
- Test: `PainelIA.test.ts`, `DetalheQuestao.test.ts`, `Documentos.test.ts`

**Interfaces:**
- Consumes: as rotas da Task 7.
- Produces:
  - `conversar(uid, pedido, aoEvento: (e: {tipo, dados}) => void, sinal?: AbortSignal): Promise<void>` — `fetch` com
    leitura do corpo por linhas (NDJSON), no `api/agente.ts` (único lugar com `fetch` direto além do `cliente.ts`).
  - `PainelIA` props `{ uid, alvo, papel, atalhos: string[] }`: carrega a conversa; atalhos e "Recomeçar" e "Copiar o
    contexto" no topo; mensagens com `Markdown` (KaTeX); citação `[Livro p. N]` vira link que usa `pedido.fonte`/
    `pedido.documento` (mesmo mecanismo da busca, resolvendo o rótulo pelas fontes e documentos do painel); evento
    `gravado` vira aviso com "Abrir" e "Desfazer" — o Histórico só desfaz a última ação, então "Desfazer" fica
    ativo só enquanto o `grupo_id` gravado for o último grupo do Histórico (consulta a lista do Histórico ao clicar);
    senão vira "Abrir o Histórico"; `confirmar` abre a confirmação do
    teto e reenvia com `confirmado: true`; rodapé com o custo e "mês: R$ x de R$ y"; sem chave mostra `ConfigurarChave`
    e "Copiar o contexto".

- [ ] **Step 1: Testes** — `PainelIA.test.ts`: streaming simulado escreve aos pedaços; citação vira link e abre a
  fonte na página; "Resolução salva" com Desfazer chama a rota; teto pede confirmação e reenvia; sem chave mostra
  o campo e "Copiar o contexto"; "Desfazer" vira "Abrir o Histórico" quando houve outra ação depois; `DetalheQuestao.test.ts`: o painel recebe `questao:<id>` e os atalhos N1–N4;
  `Documentos.test.ts`: "Resumir a seção" abre o painel no alvo da seção.
- [ ] **Step 2: Ver falhar**; **Step 3: Implementar**; **Step 4:** `npm test` e `npm run check`.
- [ ] **Step 5: Conferir na tela** com uma cópia do Cálculo 2 num servidor temporário e o modelo falso ligado por
  variável de ambiente (`ESTUDOS_AGENTE_FALSO=1` faz `app.state.fabrica_modelo` devolver um `ModeloFalso` de
  demonstração) — screenshot da questão com N2 e de um N4 gravado.
- [ ] **Step 6: Commit** — `feat: painel do assistente nas Listas, em Documentos e no painel geral`

### Task 9: Avaliação do contexto e teste real

**Files:**
- Modify: `estudos/avaliacao/__main__.py` (tipo `contexto`), `pyproject.toml` (marcador `gemini`)
- Create: `estudos/avaliacao/contexto.py`, `tests/test_agente_gemini_real.py`
- Docs: `docs/avaliacoes/2026-10-27-<materia>-contexto.md`

**Interfaces:**
- Produces: `cobertura_do_contexto(con, raiz, perguntas) -> LinhaContexto(total, achadas, por_estilo)` — para cada
  pergunta de estilo `questao`/`duvida`, acha a questão no banco pelo enunciado (normalizado, prefixo de 60
  caracteres) e verifica se alguma resposta aceita (`casa`) está entre os pedaços do contexto inicial; perguntas sem
  questão correspondente ficam fora da conta. `python -m estudos.avaliacao contexto --materia X [--geradas] [--gravar]`.

- [ ] **Step 1: Testes** — `test_cobertura_do_contexto` (cenário com uma questão cuja seção tem teoria: achada),
  `test_gemini_real` com `@pytest.mark.gemini` (pula sem chave; uma pergunta curta, confere `Texto` e `Uso`).
- [ ] **Step 2–4.** **Step 5: Rodar** nas duas matérias e registrar em `docs/avaliacoes/`.
- [ ] **Step 6: Commit** — `test: cobertura do contexto inicial do agente e teste real opcional`
