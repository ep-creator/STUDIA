# Redesenho minimalista Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Levar o STUDIA inteiro para a linguagem da barra lateral (texto, tipografia, um sinal de estado, sem caixas), com menos texto na visão geral, a IA numa gaveta por cima da página e uma página própria do Assistente.

**Architecture:** Primeiro a base global em `temas/temas.css` (só Editorial, tokens `--fio`/`--leve`, três classes de ação, linha com ações no hover) e a estrutura comum (moldura → linha de cabeçalho, topo). Depois cada tela migra para essas peças, uma tarefa por área. O único backend novo é uma rota que lista as conversas ativas do agente. Uma tarefa final prende as regras globais com um teste que varre o código-fonte.

**Tech Stack:** Svelte 5 (runes) + Vite + TypeScript, Vitest + Testing Library, Playwright (e2e); FastAPI + SQLite, pytest.

**Spec:** `docs/superpowers/specs/2026-10-28-redesenho-minimalista-design.md` (esboços em `.superpowers/brainstorm/700-1793189126/content/`).

## Global Constraints

- Só `editorial-claro` e `editorial-escuro`; nenhuma regra `data-tema^='padrao'` nem `data-tema^='editorial'` sobra em componente.
- Tokens novos em `:root`: `--fio: color-mix(in srgb, var(--texto) 14%, transparent)`, `--leve: color-mix(in srgb, var(--texto) 6%, transparent)`.
- Ações: `.acao-texto` (palavra em `--suave`; hover `--texto` + sublinhado laranja), `.acao-suave` (pílula sem borda, fundo `--leve`), `.acao-forte` (fundo `--texto`, letra `--fundo`; no máximo uma por tela). `.botao` deixa de existir.
- Estado: marca/aba ativa com sublinhado 1,5 px; número marcado com traço 2 px; item ativo de lista vertical com traço laranja 2 px à esquerda + negrito; selos como texto colorido (próxima laranja, vista/pronto verde, revisar amarelo, pendente cinza).
- Sem caixas: `.cartao` sem borda nem fundo; nunca dois fios encostados.
- Ações de linha só aparecem com `:hover` ou `:focus-within` da linha; apagar fica no menu “···”.
- Menos texto: sem parágrafos explicativos fixos; estado vazio é uma frase curta.
- Nunca commitar dados do usuário (`Calculo 2/`, `Geometria Analítica/`, `calculo 1(teste)/`, `.claude/`, `_app/.locks.lnk`); conferência visual só em cópia temporária; não matar o processo na porta 8790; não chamar a API real do Gemini.
- Commits terminam com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; mensagem escrita em `$TEMP/msg.txt`.
- Comandos: frontend `cd _app/frontend && npx vitest run <arquivo>`, `npm run check`; backend `cd _app/backend && .venv/Scripts/python -m pytest <arquivo> -q`.

## Review Focus

1. Teclado: o que aparece no hover (ações de linha, “···”) também aparece e funciona com Tab/Enter — testes em Tasks 4 e 5 focam o botão e acionam por teclado.
2. Desmarcar: clicar na marca já ativa desmarca; clicar numa marca diferente troca (não desmarca) — Task 2.
3. Gaveta: Esc fecha, o foco volta ao botão “IA ›”, e a página por baixo não muda de largura — Task 9.
4. Preferência antiga `{"identidade":"padrao",…}` no `localStorage` não quebra e vira Editorial — Task 1.
5. Rota de conversas: conversa sem mensagem não aparece; alvo de questão/seção apagada não derruba a lista (rótulo cai para o próprio alvo) — Task 7.

---

### Task 1: Base global — tema único, tokens, ações e seletor de tema

**Files:**
- Modify: `_app/frontend/src/temas/temas.css`, `_app/frontend/src/estado/tema.svelte.ts`, `_app/frontend/src/componentes/SeletorTema.svelte`
- Modify (remover condicionais de tema, mantendo o estilo Editorial como único): `componentes/Abertura.svelte`, `BarraLateral.svelte`, `CartaoMateria.svelte`, `ListaDocumentos.svelte`, `Marca.svelte`, `MolduraEditorial.svelte`
- Test: `_app/frontend/src/estado/tema.test.ts`, Create `_app/frontend/src/componentes/SeletorTema.test.ts`

**Interfaces:**
- Produces: `tema: { modo: Modo }`, `escolherModo(modo: Modo): void`, `temaEfetivo(): 'editorial-claro' | 'editorial-escuro'`, `aplicarTema(): void` (em `estado/tema.svelte.ts`; `Identidade` e `escolherTema` deixam de existir). Classes globais `.acao-texto`, `.acao-suave`, `.acao-forte`, `.linha-acoes` (contêiner da linha) + `.acoes-linha` (grupo que só aparece no hover/foco), tokens `--fio`, `--leve`.

- [ ] **Step 0: Commitar os ajustes pendentes do painel da questão** (N1–N4 curtos, sem “Abrir o livro”, sem “Copiar o contexto”, caixa “API key”, painel lateral mais largo — já testados, 142 verdes):

```bash
git add _app/frontend/src/App.svelte _app/frontend/src/componentes/ConfigurarChave.svelte _app/frontend/src/componentes/DetalheQuestao.svelte _app/frontend/src/componentes/DetalheQuestao.test.ts _app/frontend/src/componentes/PainelIA.svelte _app/frontend/src/componentes/PainelIA.test.ts _app/frontend/src/estado/ia.svelte.ts
git commit -F $TEMP/msg.txt   # "fix: painel da questão mais enxuto (N1–N4 curtos, só Ver no livro, só a caixa da API key)"
```

- [ ] **Step 1: Testes que falham**

Em `tema.test.ts`, trocar os testes que usam identidade por:

```ts
test('preferência antiga com identidade padrão vira editorial', async () => {
  localStorage.setItem('estudos.tema', JSON.stringify({ identidade: 'padrao', modo: 'escuro' }))
  const { tema, temaEfetivo } = await import('./tema.svelte')
  expect(tema.modo).toBe('escuro')
  expect(temaEfetivo()).toBe('editorial-escuro')
})
test('escolherModo salva só o modo', async () => {
  const { escolherModo } = await import('./tema.svelte')
  escolherModo('claro')
  expect(JSON.parse(localStorage.getItem('estudos.tema')!)).toEqual({ modo: 'claro' })
})
```

(mantém os de sistema escuro e `localStorage` indisponível, adaptados para `modo`).

`SeletorTema.test.ts`:

```ts
test('três opções em texto, a ativa marcada, e clicar troca o modo', async () => {
  render(SeletorTema)
  const grupo = screen.getByRole('group', { name: 'Tema' })
  expect(within(grupo).getAllByRole('button').map((b) => b.textContent)).toEqual(['Claro', 'Escuro', 'Sistema'])
  await userEvent.click(within(grupo).getByRole('button', { name: 'Escuro' }))
  expect(within(grupo).getByRole('button', { name: 'Escuro' })).toHaveAttribute('aria-pressed', 'true')
})
```

- [ ] **Step 2: Rodar e ver falhar** — `npx vitest run src/estado/tema.test.ts src/componentes/SeletorTema.test.ts` → FAIL (`escolherModo` não existe; seletor ainda é `Seletor`).

- [ ] **Step 3: Implementar**
  - `tema.svelte.ts`: lê `{modo}` ignorando qualquer `identidade` salva; padrão `sistema`.
  - `temas.css`: apagar os blocos `padrao-claro`/`padrao-escuro` e o `:root` com valores do Padrão (o `:root` passa a ter os valores do editorial-claro); `--fonte-titulo` Fraunces e `--raio: 4px` globais; adicionar `--fio`, `--leve`, as três `.acao-*`, `.linha-acoes .acoes-linha { opacity: 0 }` e `.linha-acoes:hover .acoes-linha, .linha-acoes:focus-within .acoes-linha { opacity: 1 }`; `.cartao` vira `background: transparent; border: 0; padding: 0`. Manter `.botao` por enquanto (sai na Task 10).
  - Componentes listados: a regra que hoje vale só sob `data-tema^='editorial'` vira a regra normal; a de `padrao` é apagada.
  - `SeletorTema.svelte`: `<div role="group" aria-label="Tema">` com três `button.acao-texto` `aria-pressed`; o ativo com sublinhado laranja (§3.3 da spec). Mantém a prop `posicao`.

- [ ] **Step 4: Rodar e ver passar** — os dois arquivos + `npx vitest run` inteiro + `npm run check` → verde, 0 erros.

- [ ] **Step 5: Commit** — `feat: só o tema Editorial, tokens e classes de ação`.

---

### Task 2: Estrutura comum, topo e Listas

**Files:**
- Modify: `componentes/MolduraEditorial.svelte` (vira a linha de cabeçalho), `componentes/Topo.svelte`, `App.svelte` (botões Desfazer/IA), `componentes/GradeQuestoes.svelte`, `componentes/DetalheQuestao.svelte`, `componentes/PainelIA.svelte`, `componentes/ConfigurarChave.svelte`
- Test: `componentes/DetalheQuestao.test.ts`, `componentes/PainelIA.test.ts`, `componentes/GradeQuestoes.test.ts`

**Interfaces:**
- Consumes: classes e tokens da Task 1.
- Produces: `MolduraEditorial` com as mesmas props de hoje, renderizando `<div class="cabecalho-materia">` (rótulo da matéria à esquerda, da unidade à direita, fio embaixo) antes do conteúdo; `PainelIA` com `<div role="group" aria-label="Nível de ajuda">` para os atalhos N1–N4 e um botão `aria-label="Mais ações"` que abre um menu com “Recomeçar”. Novo componente `componentes/MenuMais.svelte`: props `{ rotulo: string; itens: { rotulo: string; acao: () => void; perigo?: boolean }[] }`, botão “···” (`aria-label={rotulo}`, `aria-expanded`), lista `role="menu"` com `role="menuitem"`, fecha com Esc e clique fora (usado também nas Tasks 4–5).

- [ ] **Step 1: Testes que falham**

`DetalheQuestao.test.ts`:

```ts
test('sem Limpar: clicar na marca ativa desmarca, clicar em outra troca', async () => {
  const onmarcar = vi.fn()
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: 'ok', secao: null, onmarcar })
  expect(screen.queryByRole('button', { name: /Limpar/ })).toBeNull()
  await userEvent.click(screen.getByRole('button', { name: /Acertei/ }))
  expect(onmarcar).toHaveBeenLastCalledWith(q.id, null)
  await userEvent.click(screen.getByRole('button', { name: /Errei/ }))
  expect(onmarcar).toHaveBeenLastCalledWith(q.id, 'err')
})
test('ver a resolução não recolhe mais a IA', async () => { /* ia.aberta = true; clicar Ver resolução; expect(ia.aberta).toBe(true) */ })
```

(substitui o teste antigo “abrir a resolução recolhe a área de IA”.)

`PainelIA.test.ts`:

```ts
test('N1–N4 num grupo só e Recomeçar dentro do ···', async () => {
  motor({ respostas: [RESPOSTA] })
  abrir()
  const grupo = await screen.findByRole('group', { name: 'Nível de ajuda' })
  expect(within(grupo).getAllByRole('button')).toHaveLength(4)
  expect(screen.queryByRole('button', { name: 'Recomeçar' })).toBeNull()
  await userEvent.click(screen.getByRole('button', { name: 'Mais ações' }))
  expect(screen.getByRole('menuitem', { name: 'Recomeçar' })).toBeInTheDocument()
})
test('menu ··· fecha com Esc e devolve o foco ao botão', async () => { /* abre, keyboard('{Escape}'), menu some, foco no botão Mais ações */ })
```

- [ ] **Step 2: Rodar e ver falhar** — os dois arquivos → FAIL nos testes novos.

- [ ] **Step 3: Implementar**
  - `MolduraEditorial`: sem borda nem etiquetas absolutas; a linha de cabeçalho com `.rotulo` dos dois lados e `border-bottom: 1px solid var(--fio)`; o primeiro bloco da página logo depois não tem fio próprio.
  - `Topo`: unidades como abas em linha (Fraunces, ativa com sublinhado laranja, sem pílula); busca como campo `--leve` arredondado; em `App.svelte`, Desfazer e “IA ›” viram `.acao-texto`.
  - `GradeQuestoes`: número solto; `ok/err/dub` com cor e `border-bottom: 2px`; selecionada em negrito `--texto`. Teclado e aria-labels não mudam (os testes atuais continuam valendo).
  - `DetalheQuestao`: sem botão Limpar; `onclick` da marca chama `onmarcar(id, marca === m ? null : m)`; marcas como texto (§3.3); Ver no livro/Ver resolução `.acao-suave`; tira `ia.aberta = false` de `mostrarResolucao`; o cartão vira bloco sem caixa separado da lista por `border-left: 1px solid var(--fio)` (em `rotas/Listas.svelte`).
  - `PainelIA`: atalhos dentro do grupo (pílula `--leve` única, o último usado com fundo um pouco mais forte); Recomeçar em `MenuMais`; bolha do usuário `--leve`; campo com fundo `--leve` sem borda; “Enviar ↵” como `.acao-texto` laranja; gravado com “abrir”/“desfazer” como `.acao-texto`. `ConfigurarChave`: input com o estilo de campo da §3.4.

- [ ] **Step 4: Rodar e ver passar** — os três arquivos, a suíte inteira e `npm run check`.

- [ ] **Step 5: Commit** — `feat: cabeçalho sem moldura, topo e Listas no estilo novo`.

---

### Task 3: Painel em duas faixas

**Files:**
- Modify: `rotas/Painel.svelte`, `componentes/ContagemProva.svelte`, `componentes/ProgressoTopicos.svelte`, `componentes/ParaRevisar.svelte`, `componentes/DesempenhoListas.svelte`
- Create: `componentes/ProximaAula.svelte`
- Delete: `componentes/ProximoPasso.svelte`, `componentes/SemanaPainel.svelte` (só o Painel os usa)
- Test: `rotas/Painel.test.ts`

**Interfaces:**
- Produces: `ProximaAula` com props `{ topicos: Topico[]; documentos: Documento[]; vinculos: Record<string, SecaoVinculada[]>; hrefDocumentos: string }`; escolhe o tópico com a mesma regra do `ProximoPasso` atual (`status === 'proxima'`, senão o primeiro `pendente`) e o resumo pela seção do tópico; não renderiza nada sem tópico.

- [ ] **Step 1: Testes que falham** (em `Painel.test.ts`; os testes “semana mostra os próximos sete dias…” e “próximo passo acha o resumo…” saem, e o segundo vira o da próxima aula):

```ts
test('faixa de cima: prova, próxima aula com ler o resumo, tópicos vistos', async () => {
  // painel com um tópico 'proxima' ligado a uma seção que tem resumo
  expect(screen.getByRole('region', { name: 'Próxima aula' })).toHaveTextContent('Sem aula — pré-requisitos')
  await userEvent.click(screen.getByRole('link', { name: 'ler o resumo' }))
  expect(pedido.documento).toBe(RESUMO_ID)
  expect(screen.queryByRole('region', { name: 'Semana' })).toBeNull()
  expect(screen.queryByText(/Próximo passo/)).toBeNull()
})
test('prova que já passou mostra feita e a data', () => { /* hoje depois da data_prova → texto 'feita' e 'seg 14/09' */ })
test('sem tópico pendente, a próxima aula some', () => { /* todos 'visto' → queryByRole('region', {name:'Próxima aula'}) null */ })
test('para revisar agrupa por lista e mostra só os números', () => {
  // marcações err em L1 #46 e #50 → grupo 'L1 título' com links '46' e '50'; sem enunciado na tela
  expect(screen.getByText('Para revisar · 2')).toBeInTheDocument()
  expect(screen.queryByText(/mapa de contorno/i)).toBeNull()
})
test('sem marcação: Nada para revisar ainda. e acerto —', () => { /* textos exatos */ })
```

- [ ] **Step 2: Rodar e ver falhar** — `npx vitest run src/rotas/Painel.test.ts` → FAIL.

- [ ] **Step 3: Implementar**
  - `Painel.svelte`: faixa 1 em grade `11rem 17rem 1fr` (Prova | `ProximaAula` | `ProgressoTopicos`), faixa 2 em duas colunas (`ParaRevisar` | `DesempenhoListas`), separadas por um fio; sem `ProximoPasso`/`SemanaPainel`. O aviso de importações pendentes vira `.acao-texto`.
  - `ContagemProva`: número grande (“33 dias”) + data; prova passada → “feita” + data.
  - `ProgressoTopicos`: `x/y` grande, fio de progresso, tópicos em colunas com ✓ verde (visto), → laranja (o da próxima aula), ○ cinza (pendente); sem referências de livro.
  - `ParaRevisar`: rótulo “Para revisar · N”; por lista, título serifado e só os números (estilo da grade), cada um link para a questão como hoje; vazio “Nada para revisar ainda.”.
  - `DesempenhoListas`: “% feito” e “% de acerto” grandes (“—” sem marcação); linha por lista com nome, `feitas/total` e fio verde/vermelho.
  - `ProximaAula`: `<section aria-label="Próxima aula">`, rótulo, título em Fraunces, “ler o resumo” `.acao-texto` (`pedido.documento = resumo.id`).

- [ ] **Step 4: Rodar e ver passar** — arquivo, suíte inteira, `npm run check`.

- [ ] **Step 5: Commit** — `feat: painel em duas faixas, com a próxima aula`.

---

### Task 4: Tópicos com ações no hover

**Files:**
- Modify: `componentes/ArvoreTopicos.svelte`, `rotas/Topicos.svelte`
- Test: `componentes/ArvoreTopicos.test.ts`

**Interfaces:**
- Consumes: `MenuMais` (Task 2), `.linha-acoes`/`.acoes-linha` (Task 1).

- [ ] **Step 1: Testes que falham**

```ts
test('apagar fica no menu ··· da linha, alcançável por teclado', async () => {
  render(ArvoreTopicos, PROPS)
  expect(screen.queryByRole('button', { name: /^Apagar / })).toBeNull()
  const mais = screen.getByRole('button', { name: `Mais ações de ${T1.titulo}` })
  mais.focus(); await userEvent.keyboard('{Enter}')
  await userEvent.click(screen.getByRole('menuitem', { name: 'Apagar' }))
  // espera a chamada DELETE do tópico, como no teste atual de apagar
})
test('novo tópico: Enter adiciona, sem botão Adicionar', async () => {
  expect(screen.queryByRole('button', { name: /Adicionar/ })).toBeNull()
  await userEvent.type(screen.getByRole('textbox', { name: 'Novo tópico' }), 'Revisão{Enter}')
  // espera o POST com titulo 'Revisão'
})
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar** — cada linha `class="linha-acoes"`; status como selo de texto (continua clicável, ciclo pendente → próxima → visto do teste atual); seções do livro como links pequenos `--suave`; `.acoes-linha` com ↑ ↓ ✎ e `MenuMais rotulo={`Mais ações de ${t.titulo}`}` contendo Apagar (`perigo`); campo novo tópico só sublinhado, submit no Enter.

- [ ] **Step 4: Rodar e ver passar** — arquivo, suíte, check.

- [ ] **Step 5: Commit** — `feat: tópicos com selos em texto e ações no hover`.

---

### Task 5: Cronograma e Formulário

**Files:**
- Modify: `rotas/Cronograma.svelte`, `componentes/LinhaDoTempo.svelte`, `rotas/Formulario.svelte`, `componentes/CartaoFormula.svelte`, `componentes/EditorSessao.svelte`, `componentes/EditorFormula.svelte`
- Test: Create `componentes/CartaoFormula.test.ts`, `componentes/LinhaDoTempo.test.ts`

**Interfaces:**
- Consumes: `MenuMais`, `.linha-acoes`, `.acao-*`.

- [ ] **Step 1: Testes que falham**

```ts
// CartaoFormula.test.ts
test('editar visível no foco e apagar dentro do ···', async () => {
  const onapagar = vi.fn(); render(CartaoFormula, { formula: F, oneditar: vi.fn(), onapagar })
  expect(screen.getByRole('button', { name: `Editar ${F.titulo}` }).closest('.acoes-linha')).not.toBeNull()
  await userEvent.click(screen.getByRole('button', { name: `Mais ações de ${F.titulo}` }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Apagar' }))
  expect(onapagar).toHaveBeenCalled()
})
// LinhaDoTempo.test.ts
test('foco da sessão em uma linha e feito como selo de texto', () => {
  // sessão S1 feita com foco_md de duas linhas → só a primeira linha aparece; texto 'feita' com classe de selo verde
})
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar** — linhas sem caixa separadas por fio; data `--suave`; ✎ e marcar feito em `.acoes-linha`; “+ sessão”, “+ fórmula” e “folha para imprimir” como `.acao-texto` ao lado do título; título da fórmula como `.rotulo`; editores com `.acao-forte` em Salvar e `.acao-texto` em Cancelar.

- [ ] **Step 4: Rodar e ver passar** — arquivos, suíte, check.

- [ ] **Step 5: Commit** — `feat: cronograma e formulário no estilo novo`.

---

### Task 6: Documentos, Importar e Histórico

**Files:**
- Modify: `rotas/Documentos.svelte`, `componentes/ListaDocumentos.svelte`, `componentes/EditorMarkdown.svelte`, `rotas/Importacao.svelte`, `componentes/AreaSoltar.svelte`, `componentes/FilaImportacao.svelte`, `componentes/PropostaLivro.svelte`, `componentes/SeloConfianca.svelte`, `rotas/Historico.svelte`, `componentes/ItemHistorico.svelte`, `componentes/EstadoVazio.svelte`, `componentes/Avisos.svelte`, `componentes/BuscaMateria.svelte`, `rotas/Materias.svelte`
- Test: `componentes/FilaImportacao.test.ts`, `rotas/Documentos.test.ts`, Create `componentes/ItemHistorico.test.ts`

- [ ] **Step 1: Testes que falham**

```ts
// ItemHistorico.test.ts
test('desfazer só na mais recente, detalhes como ação de linha', () => {
  render(ItemHistorico, { grupo: G, ultimo: false, ondesfazer: vi.fn() })
  expect(screen.queryByRole('button', { name: /desfazer/i })).toBeNull()
  expect(screen.getByRole('button', { name: 'detalhes' }).closest('.acoes-linha')).not.toBeNull()
})
// FilaImportacao.test.ts — o estado de cada arquivo é texto: 'pronto', 'revisar 2', 'lendo…'
// Documentos.test.ts — '+ novo documento' é ação de texto; 'Resumir a seção' continua abrindo o resumidor
```

Em `Importacao` (no teste de fila ou num novo `rotas/Importacao.test.ts`): o parágrafo “Pode mandar tudo de uma vez…” não existe; a área diz “Solte os PDFs aqui ou escolha arquivos”; com proposta aberta, “Confirmar” tem `.acao-forte` e “descartar” `.acao-texto`.

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar** conforme §4.7–4.9 da spec. Títulos: “Importar” (era “Importar arquivos”), Histórico com “Ctrl+Z desfaz a última” pequeno no canto. Os textos explicativos fixos dessas telas saem. `SeloConfianca` passa o “porquê” para o `title` do “conferir”.

- [ ] **Step 4: Rodar e ver passar** — arquivos, suíte, check.

- [ ] **Step 5: Commit** — `feat: documentos, importar e histórico enxutos`.

---

### Task 7: Rota das conversas do agente

**Files:**
- Modify: `_app/backend/estudos/agente/conversas.py`, `_app/backend/estudos/api/agente.py`, `_app/backend/estudos/api/respostas.py`
- Test: `_app/backend/tests/test_agente_conversas.py`, `_app/backend/tests/test_api_agente.py`
- Regenerate: `_app/frontend/src/api/tipos.gerados.ts` (`npm run tipos`), export em `api/tipos.ts`

**Interfaces:**
- Produces: `conversas.ativas(con) -> list[ResumoConversa]` com `ResumoConversa(id: int, alvo: str, papel: str, rotulo: str, atualizada_em: str)`; `GET /api/materias/{uid}/agente/conversas` → `list[ConversaResumo]` (TypedDict com os mesmos campos), mais recentes primeiro. Tipo TS `ConversaResumo`.

- [ ] **Step 1: Testes que falham**

```python
def test_ativas_lista_so_conversas_com_mensagem_mais_recentes_primeiro(con):
    # geral com mensagem (ontem), questao:<id da 14.1 #22> com mensagem (hoje), secao:<id> sem mensagem
    r = conversas.ativas(con)
    assert [c.rotulo for c in r] == ["14.1 #22", "Geral"]

def test_rotulo_de_alvo_apagado_cai_para_o_alvo(con):
    # conversa em questao:999 (não existe) com mensagem
    assert conversas.ativas(con)[0].rotulo == "questao:999"

def test_conversa_recomecada_some_da_lista_ate_ter_mensagem(con): ...

def test_rota_de_conversas(api):
    r = api.get(f"/api/materias/{UID}/agente/conversas")
    assert r.status_code == 200 and r.json()[0].keys() == {"id", "alvo", "papel", "rotulo", "atualizada_em"}
```

Rótulos: `geral` → “Geral”; `questao:<id>` → “<código da lista> #<rótulo>”; `secao:<id>` → “<código> <título>”.

- [ ] **Step 2: Rodar e ver falhar** — `pytest tests/test_agente_conversas.py tests/test_api_agente.py -q`.

- [ ] **Step 3: Implementar** — uma consulta: conversas `ativa = 1` com `MAX(mensagem.criada_em)` (INNER JOIN, então sem mensagem fica de fora), ordenada desc; rótulo resolvido por alvo com consultas a `questao`/`lista` e `secao`; alvo sem linha correspondente usa o próprio alvo.

- [ ] **Step 4: Rodar e ver passar** — os arquivos e a suíte backend inteira; `npm run tipos` e `npm run check`.

- [ ] **Step 5: Commit** — `feat: rota com as conversas ativas do assistente`.

---

### Task 8: Página do Assistente

**Files:**
- Modify: `rotas/rota.ts` (tela `assistente`), `App.svelte`, `componentes/BarraLateral.svelte`, `estado/ia.svelte.ts`
- Create: `rotas/Assistente.svelte`
- Test: `rotas/rota.test.ts`, Create `rotas/Assistente.test.ts`

**Interfaces:**
- Consumes: `GET …/agente/conversas` e `ConversaResumo` (Task 7); `PainelIA` (Task 2).
- Produces: rota `{ tela: 'assistente'; uid: string }` ↔ `#/m/<uid>/assistente`; `abrirNaPagina(alvo: string, papel: string): void` em `estado/ia.svelte.ts` (guarda alvo/papel e navega para a página; usado pela gaveta na Task 9).

- [ ] **Step 1: Testes que falham**

```ts
// rota.test.ts
test('rota do assistente', () => {
  expect(analisarRota('#/m/u1/assistente')).toEqual({ tela: 'assistente', uid: 'u1' })
  expect(montarHash({ tela: 'assistente', uid: 'u1' })).toBe('#/m/u1/assistente')
})
// Assistente.test.ts
test('lista as conversas agrupadas e abre a escolhida', async () => {
  // stub: conversas [{alvo:'geral',rotulo:'Geral'},{alvo:'questao:5',papel:'tutor',rotulo:'14.1 #22'},{alvo:'secao:3',papel:'resumidor',rotulo:'15.4 Integrais duplas'}]
  render(Assistente, { uid: 'u1' })
  expect(await screen.findByText('Questões')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: /14.1 #22/ }))
  expect(screen.getByRole('button', { name: /14.1 #22/ })).toHaveAttribute('aria-current', 'true')
  // o PainelIA pediu /agente/conversa?alvo=questao%3A5&papel=tutor
})
test('sem conversas, abre a geral do estrategista', async () => { /* lista vazia → PainelIA com alvo geral */ })
test('não há + nova conversa', () => { /* queryByText(/nova conversa/) null */ })
```

E em algum teste de `BarraLateral` (ou `App`): link “Assistente” presente num grupo próprio, com `aria-current` na página.

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar** — `Assistente.svelte`: duas colunas (16 rem | resto); grupos Geral/Questões/Seções pelo prefixo do alvo; cada item `button` com rótulo e data relativa (hoje/ontem/dd/mm), o ativo com traço laranja e `aria-current`; à direita `PainelIA` com o alvo/papel escolhido (papel da geral: `estrategista`; atalhos como em `App.svelte`). `BarraLateral`: item “Assistente” entre as áreas da matéria e Importar/Histórico, com `<hr>` dos dois lados.

- [ ] **Step 4: Rodar e ver passar** — arquivos, suíte, check.

- [ ] **Step 5: Commit** — `feat: página do Assistente com as conversas da matéria`.

---

### Task 9: IA em gaveta por cima da página

**Files:**
- Modify: `App.svelte`, `componentes/PainelIA.svelte` (prop opcional `naGaveta`)
- Create: `componentes/GavetaIA.svelte`
- Test: Create `componentes/GavetaIA.test.ts`

**Interfaces:**
- Consumes: `abrirNaPagina` (Task 8), `ia` (`aberta`, `alvo`, `papel`).
- Produces: `GavetaIA` com props `{ uid: string; onfechar: () => void }`; renderiza véu (`button aria-label="Fechar o assistente"` cobrindo a página) + `<aside role="dialog" aria-label="Assistente" aria-modal="true">`.

- [ ] **Step 1: Testes que falham**

```ts
test('Esc fecha e o foco volta para quem abriu', async () => { /* render App-like wrapper com botão IA ›; abre; keyboard Escape; onfechar chamado; document.activeElement é o botão */ })
test('clicar no véu fecha', async () => { ... })
test('ao abrir, o foco vai para o campo de mensagem', async () => { /* textbox 'Mensagem para o assistente' tem foco */ })
test('abrir em página leva para a página do Assistente com a mesma conversa', async () => {
  await userEvent.click(screen.getByRole('link', { name: /abrir em página/ }))
  expect(location.hash).toBe('#/m/u1/assistente'); expect(ia.alvo).toBe('geral')
})
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar** — `GavetaIA`: `position: fixed; top: 0; right: 0; bottom: 0; width: 24rem`, fundo `--lateral`, sombra à esquerda; véu `position: fixed; inset: 0` com `rgb(10 9 8 / 45%)`; foco inicial no campo; Tab preso dentro da gaveta; Esc e véu chamam `onfechar`. `App.svelte`: o `<div class="ia">` sai do fluxo do `.app`; “IA ›” só abre/fecha (`ia.aberta`), e a gaveta não aparece na página do Assistente. Cabeçalho: “Assistente”, `.acao-texto` “abrir em página ↗”, ✕.

- [ ] **Step 4: Rodar e ver passar** — arquivo, suíte, check.

- [ ] **Step 5: Commit** — `feat: assistente em gaveta por cima da página`.

---

### Task 10: Fechamento — regras presas por teste, e2e e conferência visual

**Files:**
- Create: `_app/frontend/scripts/estilo.test.ts`
- Modify: `temas/temas.css` (apagar `.botao`), `tests/e2e/fluxo.spec.ts`, qualquer componente que o teste novo acusar

- [ ] **Step 1: Teste que falha** — varre `src/**/*.svelte` e `src/**/*.css`:

```ts
test('nenhum .botao, nenhum tema Padrão, nenhum condicional de identidade', () => {
  for (const [arquivo, texto] of fontes()) {
    expect(texto, arquivo).not.toMatch(/class="[^"]*\bbotao\b/)
    expect(texto, arquivo).not.toMatch(/data-tema\^='(padrao|editorial)'/)
    expect(texto, arquivo).not.toMatch(/padrao-(claro|escuro)/)
  }
})
test('no máximo uma acao-forte por arquivo de tela', () => { /* rotas/*.svelte: contagem de 'acao-forte' <= 1 */ })
```

- [ ] **Step 2: Rodar e ver falhar** — `npx vitest run scripts/estilo.test.ts` lista o que sobrou.

- [ ] **Step 3: Implementar** — migrar o que sobrou para `.acao-*`; apagar `.botao` de `temas.css`; atualizar `fluxo.spec.ts` (seletores de tema “Identidade visual”/“Claro ou escuro” → grupo “Tema”; “＋ Novo documento” → “+ novo documento”; “Importar arquivos” → “Importar”).

- [ ] **Step 4: Verificação completa**
  - `npx vitest run`, `npm run check` (0/0), `npm run e2e`, backend `pytest -q` → tudo verde.
  - Conferência visual numa cópia temporária (`$TEMP/b2/app` + `$TEMP/b2/ws`, servidor na porta 8796, frontend buildado com `--outDir $TEMP/b2/app/frontend/dist`), Editorial claro e escuro: Listas, Painel (1ª e 3ª unidade), Tópicos, Cronograma, Formulário, Documentos, Importar, Histórico, gaveta da IA e página do Assistente, comparando com os esboços; Tab passa por todas as ações de linha.

- [ ] **Step 5: Commit** — `chore: regras do estilo presas por teste e e2e atualizado`.
