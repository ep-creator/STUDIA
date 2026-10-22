# Fase 5 — Frontend Novo: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o uso diário do app antigo por um app Svelte servido pelo motor, com criar matéria só com cliques,
quatro temas e espaços reservados para a IA.

**Architecture:** O motor FastAPI ganha rotas aditivas (resumo, painel completo, fontes, detalhe do histórico, conflito ao
salvar documento), respostas tipadas no OpenAPI e passa a servir `_app/frontend/dist`. O frontend é um SPA Svelte 5 + Vite
+ TS, com roteador por hash próprio, estado em runes (`*.svelte.ts`) e um único cliente de API com tipos gerados do
OpenAPI.

**Tech Stack:**
- Python 3.13, FastAPI, Pydantic v2, pytest;
- Node 24, Svelte 5, Vite, TypeScript, openapi-typescript, markdown-it, KaTeX, DOMPurify, `@fontsource-variable/inter`
  e `@fontsource-variable/fraunces`;
- Vitest, `@testing-library/svelte` e jsdom; `@playwright/test`.

**Spec:** `docs/superpowers/specs/2026-10-22-fase-5-frontend-design.md` (e §10/§11 de
`2026-10-20-refatoracao-plataforma-design.md`).

## Global Constraints

- Nenhuma rota existente muda de formato de resposta; mudanças no motor são aditivas.
- O frontend nunca chama `fetch` fora de `src/api/cliente.ts`; nenhum caminho de pasta no frontend (arquivos só por
  `/arquivos/<uid>/<caminho>`).
- Dados sempre da API; no navegador só preferências: chave `estudos.tema` e `estudos.ultima-materia`, ambas em
  `localStorage` dentro de try/catch.
- Funciona offline: fontes e KaTeX empacotados, sem CDN nem Google Fonts.
- Textos de apresentação montados pela tela a partir do número ("1ª unidade", "Cronograma da 1ª unidade"), nunca
  guardados.
- Status de tópico: `pendente`, `proxima`, `visto` (rótulos "pendente", "próxima", "visto").
- Marcas: `ok` ✓, `err` ✗, `dub` ?, e `null` (vazio). Ciclo do clique: vazio → ok → err → dub → vazio.
- Temas:
  - Padrão claro: fundo `#fafaf7`, lateral `#f2f1ec`, texto `#1f2328`, destaque `#3b82f6`;
  - Padrão escuro: `#15171c` / `#1b1e24` / `#e6e6e6` / `#7c9cff`, cartões `#1e2128`, bordas `#2a2d35`;
  - Editorial claro: `#f3ece0` / texto `#141413` / destaque `#d9572b`;
  - Editorial escuro: `#191714` / `#efe6d6` / `#f07a45`, moldura em creme a 65%;
  - Editorial é a identidade padrão, e o modo padrão é "sistema".
- Selo de confiança:
  - verde quando o item não tem `revisar: true` (o motor marca com o `limiar_confianca`, 0,75 no `config.toml`);
  - amarelo quando tem `revisar: true`;
  - vermelho quando não há palpite (`numero`, `fonte_id` ou valor `null`).
- O `OrigemLocalMiddleware` não ganha exceções; o proxy do Vite reescreve `Origin` para `http://127.0.0.1:8790`.
- Fora do escopo: renomear/apagar matéria, refazer, anotação por questão, IA, layout de celular, online.
- Commits terminam com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Não commitar
  `Calculo 2/_app/dados/rag.db` nem as pastas de teste do usuário (`Cálculo 1 (Teste)/`, `calculo 1(teste)/`).

## Review Focus

1. Matéria recém-criada, sem unidades nem eventos (painel com `unidade: null`): todas as telas mostram o estado vazio
   que leva à Importação, sem erro. Teste: Task 6.
2. Motor desligado ou reiniciando: a faixa "Motor desligado: abra o abrir-novo.bat" aparece, a tela não quebra, e some
   quando o motor volta. Teste: Task 5.
3. Cliques rápidos seguidos na mesma questão: a marca final na tela é a do último clique e coincide com o banco
   (requisições serializadas por questão). Teste: Task 7.
4. Envio de arquivo que não é PDF ou acima do limite (422/413): aviso com a mensagem do motor, e a fila segue usável.
   Teste: Task 10.
5. Markdown com HTML/JS malicioso ou LaTeX inválido: o script não executa e a fórmula inválida aparece como erro
   inline, sem derrubar o leitor. Teste: Task 9.

---

### Task 1: Motor — resumo das matérias e painel completo

**Files:**
- Create: `_app/backend/estudos/resumo.py`
- Modify: `_app/backend/estudos/api/materias.py`, `_app/backend/estudos/api/painel.py`
- Test: `_app/backend/tests/test_api_painel_completo.py`

**Interfaces:**
- Produces:
  - `resumo.proxima_prova(con, hoje: date) -> dict | None`, com
    `{"data": str, "hora_inicio": str | None, "unidade": int | None}`: menor evento `tipo='prova'` com `data >= hoje`;
  - `resumo.importacoes_pendentes(con) -> int`: `count(*)` de `importacao` com `estado='proposta'`;
  - `resumo.vinculos(con, unidade_id: int) -> dict`, com
    `{"topicos": {str(topico_id): [SecaoVinculada]}, "listas": {str(lista_id): {"topicos": [int], "secao": SecaoVinculada | None}}}`,
    em que `SecaoVinculada = {"secao_id", "codigo", "titulo", "fonte_id", "caminho", "pagina_pdf_ini"}`;
  - `GET /api/materias`: itens `{"uid", "nome", "periodo", "unidades": int, "proxima_prova", "importacoes_pendentes"}`;
  - `GET …/painel`: o formato atual + `"eventos": [Evento]` (da unidade exibida + `unidade_id IS NULL`, ordenados por
    data e hora), `"vinculos"` e `"importacoes_pendentes"`. Com `unidade` nula: `eventos` só os gerais, `vinculos`
    `{"topicos": {}, "listas": {}}`.

- [ ] **Step 1: Write the failing tests** (cliente como em `tests/test_api_crud.py`: `TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")`; dados criados via repos dentro de `historico.operacao`)

```python
def test_lista_de_materias_traz_resumo(cliente, dados):            # dados: matéria com 2 unidades, prova em 2099-05-10 14:30 na un. 2, 1 importação pendente
    [m] = cliente.get("/api/materias").json()
    assert m["unidades"] == 2 and m["importacoes_pendentes"] == 1
    assert m["proxima_prova"] == {"data": "2099-05-10", "hora_inicio": "14:30", "unidade": 2}

def test_materia_vazia_no_resumo_e_no_painel(cliente):
    uid = cliente.post("/api/materias", json={"nome": "Nova"}).json()["uid"]
    assert cliente.get("/api/materias").json()[0]["proxima_prova"] is None
    p = cliente.get(f"/api/materias/{uid}/painel").json()
    assert p["unidade"] is None and p["eventos"] == [] and p["vinculos"] == {"topicos": {}, "listas": {}}

def test_painel_traz_eventos_da_unidade_e_gerais(cliente, dados):
    p = cliente.get(f"/api/materias/{dados.uid}/painel?unidade=2").json()
    assert [e["tipo"] for e in p["eventos"]] == ["aula", "prova", "exame_final"]   # aula da un.2, prova da un.2, exame geral; aula da un.1 fica de fora

def test_painel_traz_vinculos_de_topico_e_lista(cliente, dados):   # tópico ligado à seção 15.4 (p. 431) e lista 15.4 ligada à mesma seção
    v = cliente.get(f"/api/materias/{dados.uid}/painel?unidade=2").json()["vinculos"]
    [s] = v["topicos"][str(dados.topico_id)]
    assert (s["codigo"], s["pagina_pdf_ini"], s["caminho"]) == ("15.4", 431, "fontes/livros/stewart.pdf")
    assert v["listas"][str(dados.lista_id)]["secao"]["codigo"] == "15.4"
```

- [ ] **Step 2: Run** `.venv\Scripts\python.exe -m pytest tests/test_api_painel_completo.py -q` — Expected: FAIL (chaves ausentes).
- [ ] **Step 3: Implement** `resumo.py` (SQL direto, joins `topico_secao`/`lista_topico`/`lista_secao`/`secao_livro`/`fonte`), use-o em `materias.listar` (abre cada `materia.db` com `conectar` e fecha) e em `painel.painel`.
- [ ] **Step 4: Run** a suíte inteira `.venv\Scripts\python.exe -m pytest -q` — Expected: tudo verde.
- [ ] **Step 5: Commit** `feat(api): resumo das matérias e painel com eventos, vínculos e pendências`.

### Task 2: Motor — fontes, sumário do livro e detalhe do histórico

**Files:**
- Create: `_app/backend/estudos/api/fontes.py`
- Modify: `_app/backend/estudos/historico.py`, `_app/backend/estudos/api/historico.py`, `_app/backend/estudos/main.py` (`ROUTERS`)
- Test: `_app/backend/tests/test_api_fontes_historico.py`

**Interfaces:**
- Produces:
  - `GET …/fontes?tipo=` → `[{"id", "tipo", "titulo", "caminho", "paginas"}]`;
  - `GET …/fontes/{id}/secoes` → `[SecaoLivro]` (404 se a fonte não é livro);
  - `historico.detalhar(con, raiz: Path, grupo_id: int) -> dict`, com
    `{"grupo": GrupoHistorico, "mudancas": [{"tabela", "chave", "antes", "depois"}], "arquivos": [{"caminho", "antes": str | None, "depois": str | None}]}`:
    - `antes` = conteúdo de `versao_arquivo` (ou `None`);
    - `depois` = `versao_arquivo` da próxima mudança do mesmo arquivo em grupo posterior; senão, o arquivo atual (ou
      `None` se não existe);
  - `GET …/historico/{grupo_id}` → `detalhar(...)` (404 se não existe).

- [ ] **Step 1: Write the failing tests**

```python
def test_fontes_e_sumario(cliente, livro):            # livro com seções 14.1 e 14.2 registradas
    fontes = cliente.get(f"/api/materias/{livro.uid}/fontes?tipo=livro").json()
    assert [f["caminho"] for f in fontes] == ["fontes/livros/stewart.pdf"]
    secoes = cliente.get(f"/api/materias/{livro.uid}/fontes/{fontes[0]['id']}/secoes").json()
    assert [s["codigo"] for s in secoes] == ["14.1", "14.2"]

def test_sumario_de_fonte_que_nao_e_livro_da_404(cliente, livro):
    assert cliente.get(f"/api/materias/{livro.uid}/fontes/{livro.fonte_lista_id}/secoes").status_code == 404

def test_diferenca_de_documento_editado_duas_vezes(cliente, uid):
    doc = {"tipo": "resumo", "nome_arquivo": "a.md", "titulo": "A", "corpo": "v1"}
    cliente.put(f"/api/materias/{uid}/documentos", json=doc)
    cliente.put(f"/api/materias/{uid}/documentos", json={**doc, "corpo": "v2"})
    cliente.put(f"/api/materias/{uid}/documentos", json={**doc, "corpo": "v3"})
    grupos = cliente.get(f"/api/materias/{uid}/historico").json()       # mais recente primeiro
    meio = cliente.get(f"/api/materias/{uid}/historico/{grupos[1]['id']}").json()
    [arq] = meio["arquivos"]
    assert "v1" in arq["antes"] and "v2" in arq["depois"]
    criacao = cliente.get(f"/api/materias/{uid}/historico/{grupos[2]['id']}").json()
    assert criacao["arquivos"][0]["antes"] is None
```

- [ ] **Step 2: Run** `.venv\Scripts\python.exe -m pytest tests/test_api_fontes_historico.py -q` — Expected: FAIL (404).
- [ ] **Step 3: Implement** `fontes.py` (usa `fontes.listar` e `livros.listar_secoes`), `historico.detalhar` e a rota.
- [ ] **Step 4: Run** `.venv\Scripts\python.exe -m pytest -q` — Expected: verde.
- [ ] **Step 5: Commit** `feat(api): fontes, sumário do livro e diferença no histórico`.

### Task 3: Motor — conflito ao salvar documento e servir o app

**Files:**
- Modify: `_app/backend/estudos/api/documentos.py`, `_app/backend/estudos/api/esquemas.py` (`DocumentoSalvar`), `_app/backend/estudos/main.py`, `_app/backend/estudos/__main__.py`
- Create: `_app/backend/estudos/api/app_web.py`
- Test: `_app/backend/tests/test_api_documento_conflito.py`, `_app/backend/tests/test_api_app_web.py`

**Interfaces:**
- Produces:
  - `GET …/documentos/{id}` ganha `"versao": str`, o sha256 dos bytes do `.md` atual;
  - `DocumentoSalvar.versao_esperada: str | None = None`. Se informada e o arquivo do mesmo caminho existe com sha256
    diferente: `Conflito("O documento mudou desde que foi aberto; recarregue para ver a versão atual.")` → 409;
  - `app_web.registrar(app: FastAPI, dist: Path) -> None`: registrada **por último** em `create_app` com
    `settings.app_dir / "frontend" / "dist"`;
  - `GET /{caminho:path}` fora de `api/` e `arquivos/`: arquivo de `dist` se existir (com `caminho_seguro`), senão
    `index.html`. Sem `dist/index.html`: HTML 200 com "Frontend ainda não compilado: rode o abrir-novo.bat (ou npm run
    build em _app/frontend).";
  - `python -m estudos` abre `http://{host}:{porta}/` (não mais `/docs`).

- [ ] **Step 1: Write the failing tests**

```python
def test_salvar_com_versao_antiga_da_conflito(cliente, uid, materia_pasta):
    doc = {"tipo": "resumo", "nome_arquivo": "a.md", "titulo": "A", "corpo": "v1"}
    did = cliente.put(f"/api/materias/{uid}/documentos", json=doc).json()["id"]
    aberto = cliente.get(f"/api/materias/{uid}/documentos/{did}").json()
    versao = aberto["versao"]
    (materia_pasta / aberto["caminho"]).write_text("mudado por fora", encoding="utf-8")
    r = cliente.put(f"/api/materias/{uid}/documentos", json={**doc, "corpo": "v2", "versao_esperada": versao})
    assert r.status_code == 409 and "mudou" in r.json()["erro"]

def test_salvar_com_versao_atual_funciona(cliente, uid): ...   # mesma sequência sem a edição por fora → 200

def test_app_servido_e_api_intacta(tmp_path):                      # cria tmp_path/_app/frontend/dist/index.html e assets/app.js
    c = cliente_com_dist(tmp_path)
    assert "<div id=\"app\">" in c.get("/").text and "<div id=\"app\">" in c.get("/qualquer/rota").text
    assert c.get("/assets/app.js").text == "console.log(1)"
    assert c.get("/api/materias").json() == [] and c.get("/api/nao-existe").status_code == 404

def test_sem_build_mostra_instrucao(tmp_path):
    assert "Frontend ainda não compilado" in cliente_sem_dist(tmp_path).get("/").text
```

- [ ] **Step 2: Run** `.venv\Scripts\python.exe -m pytest tests/test_api_documento_conflito.py tests/test_api_app_web.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement**: a comparação de versão fica em `api/documentos.salvar` antes de `ctx.acao`; o caminho vem de `documentos._caminho(tipo, nome_arquivo)` (promover para `caminho_documento` público); `app_web.registrar` com `FileResponse`/`HTMLResponse`.
- [ ] **Step 4: Run** `.venv\Scripts\python.exe -m pytest -q` — Expected: verde.
- [ ] **Step 5: Commit** `feat(api): conflito ao salvar documento e app servido pelo motor`.

### Task 4: Motor — respostas tipadas no OpenAPI

**Files:**
- Create: `_app/backend/estudos/api/respostas.py` (TypedDicts das respostas compostas)
- Modify: as rotas usadas pelo frontend (`materias`, `painel`, `marcacoes`, `historico`, `documentos`, `fontes`, `importacoes`, `rag`, `unidades`, `topicos`, `listas`, `cronograma`, `formulas`) — só a anotação de retorno
- Test: `_app/backend/tests/test_openapi_tipado.py`

**Interfaces:**
- Produces: anotações de retorno (`-> Painel`, `-> list[Topico]`, `-> Criado`…) que o FastAPI transforma em
  `response_model`, com dataclasses de `estudos.modelos` onde a resposta já é `asdict(modelo)` e TypedDicts em
  `respostas.py` para:
  - `ResumoMateria`, `Painel`, `Vinculos`, `SecaoVinculada`;
  - `ImportacaoSaida`: `proposta: dict[str, Any]`; a proposta continua livre e é tipada no frontend (Task 10);
  - `DetalheHistorico`, `DocumentoComCorpo`, `Criado` (`{"id": int}`), `Ok`, `Placar`, `ResultadoBusca`.

- [ ] **Step 1: Write the failing test**

```python
ROTAS_DO_FRONTEND = [("get", "/api/materias"), ("get", "/api/materias/{materia_uid}/painel"),
                     ("get", "/api/materias/{materia_uid}/importacoes"), ("get", "/api/materias/{materia_uid}/historico/{grupo_id}"),
                     ("get", "/api/materias/{materia_uid}/documentos/{documento_id}"), ("get", "/api/materias/{materia_uid}/fontes"),
                     ("put", "/api/materias/{materia_uid}/marcacoes/{questao_id}"), ("get", "/api/materias/{materia_uid}/busca")]

@pytest.mark.parametrize("metodo,rota", ROTAS_DO_FRONTEND)
def test_resposta_tem_esquema(cliente, metodo, rota):
    esquema = cliente.get("/openapi.json").json()["paths"][rota][metodo]["responses"]["200"]["content"]["application/json"]["schema"]
    assert esquema not in ({}, {"type": "object"}, {"additionalProperties": True, "type": "object"})

def test_painel_documenta_os_blocos(cliente):
    comp = cliente.get("/openapi.json").json()["components"]["schemas"]["Painel"]["properties"]
    assert {"topicos", "listas", "marcacoes", "eventos", "vinculos", "importacoes_pendentes", "placar"} <= comp.keys()
```

- [ ] **Step 2: Run** `.venv\Scripts\python.exe -m pytest tests/test_openapi_tipado.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement** as anotações; nenhuma rota muda o JSON devolvido.
- [ ] **Step 4: Run** `.venv\Scripts\python.exe -m pytest -q` — Expected: verde (prova que os formatos não mudaram).
- [ ] **Step 5: Commit** `feat(api): respostas tipadas no OpenAPI para o frontend`.

### Task 5: Frontend — projeto, cliente da API, roteador e estado

**Files:**
- Create: `_app/frontend/package.json`, `vite.config.ts`, `tsconfig.json`, `svelte.config.js`, `index.html`, `src/main.ts`, `src/App.svelte`
- Create: `src/api/cliente.ts`, `src/api/tipos.gerados.ts` (gerado), `scripts/gerar-tipos.mjs`
- Create: `src/rotas/rota.ts`, `src/estado/materia.svelte.ts`, `src/estado/conexao.svelte.ts`, `src/estado/avisos.svelte.ts`
- Modify: `.gitignore` (`_app/frontend/node_modules/`, `_app/frontend/dist/`, `_app/frontend/test-results/`, `_app/frontend/playwright-report/`)
- Test: `src/api/cliente.test.ts`, `src/rotas/rota.test.ts`, `src/estado/conexao.test.ts`

**Interfaces:**
- Produces:
  - scripts npm: `dev`, `build`, `check` (svelte-check), `test` (vitest run), `tipos` (openapi-typescript de
    `http://127.0.0.1:8790/openapi.json` → `src/api/tipos.gerados.ts`), `e2e`;
  - `vite.config.ts`: proxy de `/api` e `/arquivos` → `http://127.0.0.1:8790` (`changeOrigin: true`) e
    `proxyReq.setHeader("origin", "http://127.0.0.1:8790")`;
  - `cliente.ts`:
    - `class ErroApi extends Error { status: number }`;
    - `class MotorDesligado extends Error`;
    - `requisitar<T>(metodo: "GET" | "POST" | "PUT" | "PATCH" | "DELETE", caminho: string, corpo?: unknown | FormData): Promise<T>`;
    - `urlArquivo(uid: string, caminho: string, pagina?: number): string` (`/arquivos/<uid>/<caminho>#page=N`);
    - `API_BASE = import.meta.env.VITE_API_BASE ?? ""`;
    - erro de rede → `MotorDesligado`; resposta não-2xx → `ErroApi(json.erro ?? statusText)`;
  - `rota.ts`:
    - `type Area = "painel" | "topicos" | "listas" | "cronograma" | "documentos" | "formulario"`;
    - `type Rota = { tela: "materias" } | { tela: "materia"; uid: string; unidade: number | null; area: Area } | { tela: "importar" | "historico"; uid: string }`;
    - `analisarRota(hash: string): Rota`, `montarHash(r: Rota): string`; padrões `#/`, `#/m/<uid>`,
      `#/m/<uid>/u/<n>/<area>`, `#/m/<uid>/importar`, `#/m/<uid>/historico`; inválido → `{tela: "materias"}`;
  - `materia.svelte.ts`: `estadoMateria` com `uid`, `unidade`, `painel: Painel | null`, `carregando`; funções
    `carregarPainel(uid, unidade?)` e `recarregar()`;
  - `conexao.svelte.ts`: `conexao.motorLigado: boolean`; `verificarMotor()` faz polling de `GET /api/materias` a cada
    3 s enquanto desligado;
  - `avisos.svelte.ts`: `avisar(texto: string, acao?: { rotulo: string; executar: () => void })`, `erro(e: unknown)`.

- [ ] **Step 1: Scaffold** com `npm create vite@latest frontend -- --template svelte-ts` em `_app/`, e instale as dependências da Tech Stack com `npm install`.
- [ ] **Step 2: Write the failing tests**

```ts
test("erro do motor vira ErroApi com a mensagem", async () => {
  fetchMock(422, { erro: "Dados inválidos — nome: obrigatório" });
  await expect(requisitar("POST", "/api/materias", {})).rejects.toMatchObject({ status: 422, message: "Dados inválidos — nome: obrigatório" });
});
test("falha de rede vira MotorDesligado", async () => { fetchRejeita(); await expect(requisitar("GET", "/api/materias")).rejects.toBeInstanceOf(MotorDesligado); });
test("urlArquivo com página", () => expect(urlArquivo("ab", "fontes/livros/s t.pdf", 433)).toBe("/arquivos/ab/fontes/livros/s%20t.pdf#page=433"));
test.each([["#/", { tela: "materias" }], ["#/m/ab/u/2/listas", { tela: "materia", uid: "ab", unidade: 2, area: "listas" }],
           ["#/m/ab", { tela: "materia", uid: "ab", unidade: null, area: "painel" }], ["#/m/ab/importar", { tela: "importar", uid: "ab" }],
           ["#/lixo", { tela: "materias" }]])("analisarRota(%s)", (h, r) => { expect(analisarRota(h)).toEqual(r); expect(analisarRota(montarHash(r))).toEqual(r); });
test("motor volta depois de desligado", async () => { /* 1ª chamada rejeita, 2ª responde [] → motorLigado false e depois true */ });
```

- [ ] **Step 3: Run** `npm test` em `_app/frontend` — Expected: FAIL.
- [ ] **Step 4: Implement** os módulos; com o motor rodando, gere os tipos (`npm run tipos`) e commite `tipos.gerados.ts`.
- [ ] **Step 5: Run** `npm test && npm run check && npm run build` — Expected: verde, `dist/index.html` gerado.
- [ ] **Step 6: Commit** `feat(frontend): projeto Svelte, cliente da API, roteador e estado`.

### Task 6: Frontend — temas, estrutura fixa, Matérias e Painel

**Files:**
- Create: `src/temas/temas.css` (4 paletas em `:root[data-tema="padrao-claro" | "padrao-escuro" | "editorial-claro" | "editorial-escuro"]`, tokens `--fundo`, `--lateral`, `--cartao`, `--borda`, `--texto`, `--suave`, `--destaque`, `--ok`, `--err`, `--dub`), `src/estado/tema.svelte.ts`
- Create: `src/componentes/{BarraLateral,Topo,SeletorUnidade,EspacoIA,Aviso,FaixaMotor,EstadoVazio,MolduraEditorial}.svelte`
- Create: `src/rotas/Materias.svelte`, `src/rotas/Painel.svelte`, `src/componentes/{CartaoMateria,ContagemProva,ProgressoTopicos,AgendaCurta}.svelte`, `src/apresentacao.ts`
- Test: `src/apresentacao.test.ts`, `src/estado/tema.test.ts`, `src/rotas/Painel.test.ts`

**Interfaces:**
- Consumes: `cliente.ts`, `rota.ts`, `estadoMateria`, `conexao`, `avisos` (Task 5); `Painel` e `ResumoMateria` de
  `tipos.gerados.ts`.
- Produces:
  - `apresentacao.ts`:
    - `ordinal(n: number): string` ("1ª");
    - `nomeUnidade(n)` ("1ª unidade");
    - `diasAte(data: string, hoje: Date): number`;
    - `textoContagem(prova: { data: string; hora_inicio: string | null } | null, hoje: Date): string`: "hoje", "amanhã",
      "N dias", "sem data de prova";
    - `rotuloStatus(s)`;
  - `tema.svelte.ts`:
    - `tema.identidade: "padrao" | "editorial"` (padrão `"editorial"`);
    - `tema.modo: "sistema" | "claro" | "escuro"` (padrão `"sistema"`);
    - `aplicarTema()` define `document.documentElement.dataset.tema` e reage a `prefers-color-scheme`;
    - persiste em `estudos.tema`;
  - `EspacoIA.svelte`: props `{ contexto: string }`; mostra "Chega na Fase 6"; usado no `Topo` (faixa) e no
    `DetalheQuestao` (Task 7);
  - `EstadoVazio.svelte`: props `{ texto: string; acao?: { rotulo: string; href: string } }`.

- [ ] **Step 1: Write the failing tests**

```ts
test("ordinal e unidade", () => { expect(ordinal(1)).toBe("1ª"); expect(nomeUnidade(3)).toBe("3ª unidade"); });
test.each([["2026-10-22", "hoje"], ["2026-10-23", "amanhã"], ["2026-11-03", "12 dias"]])("contagem %s", (d, t) =>
  expect(textoContagem({ data: d, hora_inicio: null }, new Date(2026, 9, 22))).toBe(t));
test("sem prova", () => expect(textoContagem(null, new Date())).toBe("sem data de prova"));
test("tema padrão é editorial seguindo o sistema", () => { localStorage.clear(); expect([tema.identidade, tema.modo]).toEqual(["editorial", "sistema"]); });
test("localStorage indisponível não quebra o tema", () => { quebrarLocalStorage(); expect(() => aplicarTema()).not.toThrow(); });
test("painel de matéria vazia leva à importação", async () => {   // Review Focus 1
  render(Painel, { painel: painelVazio });   // unidade null, sem tópicos/eventos
  expect(screen.getByText(/Envie o programa/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Importar/ })).toHaveAttribute("href", "#/m/ab/importar");
});
```

- [ ] **Step 2: Run** `npm test` — Expected: FAIL.
- [ ] **Step 3: Implement**: layout da spec §4 (barra lateral, topo com unidades, contagem e ↩, faixa `EspacoIA` recolhível); `Materias` com `CartaoMateria` e "＋ Nova matéria" (`POST /api/materias` → `#/m/<uid>/importar`); `Painel` com contagem, progresso, agenda (sessões + eventos dos próximos 7 dias) e pendências; moldura com rótulos nas bordas só no Editorial; fontes via `@fontsource-variable/inter` e `@fontsource-variable/fraunces`.
- [ ] **Step 4: Run** `npm test && npm run check` — Expected: verde.
- [ ] **Step 5: Commit** `feat(frontend): temas, estrutura, matérias e painel`.

### Task 7: Frontend — Listas (grade + detalhe)

**Files:**
- Create: `src/rotas/Listas.svelte`, `src/componentes/{GradeQuestoes,DetalheQuestao,Placar}.svelte`, `src/estado/marcacoes.svelte.ts`
- Test: `src/estado/marcacoes.test.ts`, `src/componentes/GradeQuestoes.test.ts`

**Interfaces:**
- Consumes: `estadoMateria.painel` (`listas`, `marcacoes`, `vinculos.listas`), `urlArquivo`, `EspacoIA`.
- Produces:
  - `marcacoes.svelte.ts`:
    - `proximaMarca(m: Marca): Marca` (vazio → ok → err → dub → vazio);
    - `marcar(questaoId: number, marca: Marca): Promise<void>`: otimista; fila por questão (a próxima requisição da
      mesma questão só sai depois da anterior); em erro, reverte para a última marca confirmada e chama
      `avisos.erro`; atualiza o placar com o `placar` da resposta;
  - `type Marca = "ok" | "err" | "dub" | null`.

- [ ] **Step 1: Write the failing tests**

```ts
test("ciclo da marca", () => expect([null, "ok", "err", "dub"].map(proximaMarca)).toEqual(["ok", "err", "dub", null]));
test("falha do motor reverte a marca", async () => { putFalha(422); await marcar(7, "ok"); expect(marcaDe(7)).toBe(null); });
test("cliques rápidos terminam na última marca e na ordem", async () => {   // Review Focus 3
  const ordem = putLento();                       // registra a ordem das requisições
  marcar(7, "ok"); marcar(7, "err"); await marcar(7, "dub");
  expect(ordem()).toEqual(["ok", "err", "dub"]); expect(marcaDe(7)).toBe("dub");
});
test("teclado: setas navegam e 1/2/3 marcam", async () => {
  render(GradeQuestoes, { listas: [lista154] });
  await userEvent.keyboard("{ArrowRight}2");       // foca a 2ª questão e marca ✗
  expect(marcarSpy).toHaveBeenCalledWith(lista154.questoes[1].id, "err");
});
```

- [ ] **Step 2: Run** `npm test` — Expected: FAIL.
- [ ] **Step 3: Implement**:
  - grade por lista (linha 1/linha 2 nas listas por seção) com placar;
  - `DetalheQuestao` com enunciado (componente `Markdown` da Task 9; até lá, texto puro), atalho "abrir o livro" com
    `urlArquivo(uid, secao.caminho, questao.pagina_pdf ?? secao.pagina_pdf_ini)` e `EspacoIA contexto="tutor"`;
  - aviso "Questão 15.4 #11 marcada ✗ · Desfazer".
- [ ] **Step 4: Run** `npm test && npm run check` — Expected: verde.
- [ ] **Step 5: Commit** `feat(frontend): listas com grade, detalhe e marcação otimista`.

### Task 8: Frontend — Tópicos, Cronograma e Formulário

**Files:**
- Create: `src/rotas/{Topicos,Cronograma,Formulario}.svelte`, `src/componentes/{ArvoreTopicos,SeloStatus,LinhaDoTempo,EditorSessao,CartaoFormula,EditorFormula}.svelte`, `src/cronograma.ts`
- Test: `src/cronograma.test.ts`, `src/componentes/ArvoreTopicos.test.ts`

**Interfaces:**
- Consumes: `estadoMateria`, `requisitar`, `Markdown`/KaTeX (Task 9: `EditorFormula` usa `renderizarLatex`).
- Produces:
  - `cronograma.ts`: `type ItemLinha = { data: string | null; tipo: "sessao" | Evento["tipo"]; ... }`;
    `montarLinhaDoTempo(sessoes: Sessao[], eventos: Evento[]): ItemLinha[]` ordenada por data (sessões sem data no fim,
    pela `ordem`) e hora;
  - rotas usadas: `PATCH/POST/DELETE …/topicos`, `…/sessoes`, `…/formulas` (existentes); depois de cada escrita,
    `estadoMateria.recarregar()`.

- [ ] **Step 1: Write the failing tests**

```ts
test("linha do tempo mistura sessões e eventos por data e hora", () => {
  const l = montarLinhaDoTempo([sessao("2026-09-09"), sessao(null)], [evento("prova", "2026-09-14", "14:30"), evento("aula", "2026-09-09", null)]);
  expect(l.map(i => [i.data, i.tipo])).toEqual([["2026-09-09", "aula"], ["2026-09-09", "sessao"], ["2026-09-14", "prova"], [null, "sessao"]]);
});
test("clique no status avança pendente → próxima → visto → pendente", async () => {
  render(ArvoreTopicos, { topicos: [topico("pendente")] });
  await userEvent.click(screen.getByRole("button", { name: "pendente" }));
  expect(patchSpy).toHaveBeenCalledWith(expect.stringMatching(/topicos\/1$/), { status: "proxima" });
});
```

- [ ] **Step 2: Run** `npm test` — Expected: FAIL.
- [ ] **Step 3: Implement**:
  - **Tópicos:** árvore com `pai_id`, seção do livro via `vinculos.topicos` com atalho, listas ligadas; criar,
    renomear, reordenar (setas ↑/↓, que mudam `ordem`) e apagar com confirmação.
  - **Cronograma:** linha do tempo, criar/editar sessão, marcar como feita.
  - **Formulário:** agrupado por tópico, prévia ao digitar e modo imprimir (`@media print` + botão `window.print()`).
- [ ] **Step 4: Run** `npm test && npm run check` — Expected: verde.
- [ ] **Step 5: Commit** `feat(frontend): tópicos, cronograma e formulário`.

### Task 9: Frontend — Documentos e leitor

**Files:**
- Create: `src/markdown.ts`, `src/rotas/Documentos.svelte`, `src/componentes/{ListaDocumentos,Markdown,EditorMarkdown,VisualizadorPdf}.svelte`
- Test: `src/markdown.test.ts`, `src/componentes/EditorMarkdown.test.ts`

**Interfaces:**
- Consumes: `GET …/documentos?unidade_id=`, `GET/PUT …/documentos/{id}` (com `versao` e `versao_esperada`, Task 3),
  `GET …/fontes`, `GET …/fontes/{id}/secoes` (Task 2), `urlArquivo`.
- Produces:
  - `renderizarMarkdown(md: string): string`: markdown-it com `$…$` e `$$…$$` via KaTeX
    (`throwOnError: false`, `output: "html"`), saída sempre por `DOMPurify.sanitize`;
  - `renderizarLatex(tex: string, bloco = false): string`;
  - `Markdown.svelte`: props `{ texto: string }`.

- [ ] **Step 1: Write the failing tests**

```ts
test("fórmula vira KaTeX", () => expect(renderizarMarkdown("$x^2$")).toContain("katex"));
test("script e handlers são removidos", () => {   // Review Focus 5
  const html = renderizarMarkdown('<img src=x onerror="alert(1)"><script>alert(2)</script>ok');
  expect(html).not.toMatch(/onerror|<script/); expect(html).toContain("ok");
});
test("LaTeX inválido não derruba o texto", () => { const h = renderizarMarkdown("antes $\\frac{1}{$ depois"); expect(h).toContain("antes"); expect(h).toContain("depois"); });
test("conflito ao salvar oferece ver a versão atual", async () => {
  putFalha(409, { erro: "O documento mudou desde que foi aberto; recarregue para ver a versão atual." });
  render(EditorMarkdown, { documento: doc }); await userEvent.click(screen.getByRole("button", { name: "Salvar" }));
  expect(screen.getByRole("button", { name: "Ver versão atual" })).toBeInTheDocument();
  expect(screen.getByRole("textbox")).toHaveValue(doc.corpo + " editado");   // o texto digitado não se perde
});
```

- [ ] **Step 2: Run** `npm test` — Expected: FAIL.
- [ ] **Step 3: Implement**:
  - lista à esquerda: documentos da unidade, mais livros e PDFs de `/fontes`;
  - leitor;
  - editor com prévia lado a lado (textarea + `Markdown`), salvando com `versao_esperada`;
  - `VisualizadorPdf` como `<iframe src={urlArquivo(...)}>`, com o sumário do livro para escolher a seção.
  - Trocar o texto puro do `DetalheQuestao` (Task 7) por `Markdown`.
- [ ] **Step 4: Run** `npm test && npm run check` — Expected: verde.
- [ ] **Step 5: Commit** `feat(frontend): documentos, leitor com KaTeX e PDF na página`.

### Task 10: Frontend — Importação

**Files:**
- Create: `src/api/proposta.ts`, `src/rotas/Importacao.svelte`, `src/componentes/{AreaSoltar,FilaImportacao,SeloConfianca,PropostaPrograma,PropostaCalendario,PropostaTurma,PropostaLivro,PropostaLista}.svelte`, `src/confianca.ts`
- Test: `src/confianca.test.ts`, `src/componentes/FilaImportacao.test.ts`

**Interfaces:**
- Consumes:
  - `POST …/importacoes` (multipart `arquivo`);
  - `GET …/importacoes?estado=proposta`;
  - `GET/PUT …/importacoes/{id}`;
  - `POST …/importacoes/{id}/confirmar`, `…/tipo` (`{"tipo"}`) e `…/descartar`;
  - o selo decide pela flag `revisar` que o motor já calcula com o `limiar_confianca` do `config.toml`; o frontend não
    repete o limiar.
- Produces:
  - `proposta.ts`: tipos TS das propostas por tipo, conforme `estudos/importacao/pipeline.py`. Principais campos:
    - `unidades[].topicos[].secoes[]`;
    - `listas[].unidade{numero, confianca, revisar, manual?}`;
    - `listas[].topicos[]{topico_id, titulo, unidade, confianca, aceito, revisar, manual?}`;
    - `secoes[]`, `topicos[]` e `equivalencias[]` do livro;
    - `referencias[]` da turma;
    - `classificacao{tipo, confianca, revisar}`; `avisos[]`; `editada` não existe mais;
  - `confianca.ts`:
    - `corDoSelo(item: { confianca?: number; revisar?: boolean; numero?: number | null }): "certo" | "revisar" | "sem-palpite"`;
    - `explicarUnidadeLista(item: PropostaListaItem): string`: monta o "por quê?" a partir dos `topicos` e da
      `confianca` ("Unidade 1 com confiança 0,30: Limite e Continuidade apontam para a unidade 1; …").

- [ ] **Step 1: Write the failing tests**

```ts
test.each([[{ confianca: 0.82, revisar: false }, "certo"], [{ confianca: 0.3, revisar: true }, "revisar"], [{ numero: null, revisar: true }, "sem-palpite"]])
  ("selo %j", (i, c) => expect(corDoSelo(i)).toBe(c));
test("por quê da unidade cita os tópicos", () => expect(explicarUnidadeLista(itemL1)).toMatch(/Limite.*Continuidade/));
test("arquivo recusado avisa e a fila continua usável", async () => {   // Review Focus 4
  postFalha(422, { erro: "Por enquanto só PDFs podem ser importados." });
  render(FilaImportacao, { uid: "ab" }); await soltar(arquivo("nota.txt"));
  expect(avisoSpy).toHaveBeenCalledWith(expect.objectContaining({ message: "Por enquanto só PDFs podem ser importados." }));
  await soltar(arquivo("Programa.pdf")); expect(postSpy).toHaveBeenCalledTimes(2);
});
test("confirmar todos só confirma os sem pendências", async () => { /* fila com pendencias [0, 2, 0] → confirmar chamado para o 1º e o 3º */ });
```

- [ ] **Step 2: Run** `npm test` — Expected: FAIL.
- [ ] **Step 3: Implement**:
  - área de soltar (vários arquivos; envio um por vez, com progresso);
  - fila com tipo e pendências;
  - proposta do selecionado por tipo, com selos e "por quê?";
  - edições (unidade da lista, aceitar/recusar vínculo, papel do livro) via `PUT` com a proposta inteira;
  - confirmar, trocar tipo, descartar e "confirmar todos sem pendências";
  - "indexando…" depois de confirmar livro, até `POST …/busca/sincronizar` responder;
  - relê a fila depois de cada confirmação; `estadoMateria.recarregar()`;
  - selo de pendências na `BarraLateral`.
- [ ] **Step 4: Run** `npm test && npm run check` — Expected: verde.
- [ ] **Step 5: Commit** `feat(frontend): importação com fila, propostas e confiança`.

### Task 11: Frontend — Histórico e desfazer global

**Files:**
- Create: `src/rotas/Historico.svelte`, `src/componentes/{ItemHistorico,Diferenca}.svelte`, `src/estado/desfazer.ts`, `src/diferenca.ts`
- Modify: `src/App.svelte` (Ctrl+Z), `src/componentes/Topo.svelte` (botão ↩)
- Test: `src/diferenca.test.ts`, `src/estado/desfazer.test.ts`

**Interfaces:**
- Consumes: `GET …/historico`, `GET …/historico/{grupo}` (Task 2), `POST …/historico/desfazer`.
- Produces:
  - `desfazer(): Promise<void>`: chama o motor, `estadoMateria.recarregar()` e avisa
    "Desfeito: <descricao>" (ou "Nada para desfazer");
  - `atalhoDesfazer(e: KeyboardEvent): boolean`: Ctrl+Z (ou Cmd+Z), exceto com foco em `input`, `textarea` ou
    `[contenteditable]`;
  - `diferencaLinhas(antes: string | null, depois: string | null): { tipo: "igual" | "removida" | "adicionada"; texto: string }[]`
    (LCS por linha).

- [ ] **Step 1: Write the failing tests**

```ts
test("diferença por linhas", () => expect(diferencaLinhas("a\nb", "a\nc")).toEqual([
  { tipo: "igual", texto: "a" }, { tipo: "removida", texto: "b" }, { tipo: "adicionada", texto: "c" }]));
test("ctrl+z não age dentro do editor", () => {
  expect(atalhoDesfazer(tecla("z", { ctrlKey: true }, document.body))).toBe(true);
  expect(atalhoDesfazer(tecla("z", { ctrlKey: true }, document.createElement("textarea")))).toBe(false);
});
test("desfazer avisa o que foi desfeito", async () => { postResponde({ desfeito: { descricao: "Importar Stewart vol. 2" } }); await desfazer(); expect(avisoSpy).toHaveBeenCalledWith("Desfeito: Importar Stewart vol. 2"); });
```

- [ ] **Step 2: Run** `npm test` — Expected: FAIL.
- [ ] **Step 3: Implement**: lista de grupos (descrição, horário, marca de desfeito), "↩ desfazer" na última ação e "ver diferença" para grupos com `arquivos`.
- [ ] **Step 4: Run** `npm test && npm run check` — Expected: verde.
- [ ] **Step 5: Commit** `feat(frontend): histórico com diferença e desfazer global`.

### Task 12: Ponta a ponta, integração contínua e abertura

**Files:**
- Create: `_app/frontend/playwright.config.ts`, `_app/frontend/tests/e2e/servidor_e2e.py`, `_app/frontend/tests/e2e/{importar,marcar,documento,temas}.spec.ts`, `_app/frontend/scripts/build-se-preciso.mjs`
- Modify: `_app/abrir-novo.bat`, `.github/workflows/testes.yml`, `README.md`

**Interfaces:**
- Consumes: tudo acima.
- Produces:
  - `servidor_e2e.py <workspace> <porta>`: sobe `create_app(carregar_settings(...))` com a porta informada (como
    `uvicorn`);
  - `playwright.config.ts`: `webServer` com `.venv` do backend, workspace temporário e porta 8792, `baseURL`
    `http://127.0.0.1:8792`;
  - PDFs de `Calculo 2/disciplina` e `Calculo 2/livros`; testes que dependem do livro usam `test.skip` se ele não
    existir;
  - `build-se-preciso.mjs`: compila se algum arquivo de `src/`, `index.html`, `package-lock.json` ou
    `vite.config.ts` for mais novo que `dist/index.html`;
  - `abrir-novo.bat`:
    - se existir `node`: `npm ci` quando faltar `node_modules`, depois `node scripts/build-se-preciso.mjs`;
    - sem Node: avisa ("Instale o Node.js para compilar a interface") e segue (o motor mostra a instrução da Task 3);
  - workflow:
    - job `frontend` (windows-latest, Node 24): `npm ci`, `npm run check`, `npm test`, `npm run build`;
    - job `e2e` (Python 3.13 + Node 24): `npx playwright install chromium` e `npm run e2e`.

- [ ] **Step 1: Write the e2e tests** (spec §8)

```ts
test("matéria nova só com cliques", async ({ page }) => {
  await page.goto("/"); await page.getByRole("button", { name: "＋ Nova matéria" }).click();
  await page.getByLabel("Nome").fill("Cálculo E2E"); await page.getByRole("button", { name: "Criar" }).click();
  await page.setInputFiles("input[type=file]", [PROGRAMA, CALENDARIO, LISTA1, LISTA3]);
  await page.getByText("Lista1_2026-1.pdf").click();
  await page.getByLabel("Unidade da lista L1").selectOption("1");
  await page.getByRole("button", { name: /Confirmar todos sem pendências/ }).click();
  await page.getByRole("button", { name: "Confirmar" }).click();          // a L1 editada
  await page.getByRole("link", { name: "Painel" }).click();
  await expect(page.getByText(/\d+ dias|hoje|amanhã/)).toBeVisible(); await expect(page.getByText(/tópicos/i)).toBeVisible();
});
test("marcar e desfazer", async ({ page }) => { /* abre Listas, clica 2× na 1ª questão (✗), tecla 3 na 2ª (?), confere placar, Ctrl+Z volta a 2ª */ });
test("editar resumo e ver diferença", async ({ page }) => { /* cria resumo, edita, salva, Histórico → ver diferença mostra linha adicionada */ });
test("quatro temas persistem", async ({ page }) => { /* para cada tema: escolhe, recarrega, confere html[data-tema] */ });
```

- [ ] **Step 2: Run** `npm run e2e` em `_app/frontend` — Expected: verde (ajuste os seletores aos rótulos acessíveis criados nas Tasks 6–11, sem mudar o fluxo).
- [ ] **Step 3: Update** `abrir-novo.bat`, o workflow e o `README.md` (como abrir, `npm run dev`, `npm run tipos`, temas).
- [ ] **Step 4: Run** `.venv\Scripts\python.exe -m pytest -q`, `npm test`, `npm run check`, `npm run build`, `npm run e2e` e abra `_app/abrir-novo.bat` com `dist/` apagado — Expected: tudo verde e o app abre em `http://127.0.0.1:8790/`.
- [ ] **Step 5: Commit** `feat: testes de ponta a ponta, CI do frontend e abertura pelo abrir-novo.bat`.
