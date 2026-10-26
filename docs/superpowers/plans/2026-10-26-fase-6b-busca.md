# Fase 6 · Peça B — Busca melhor: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Busca na interface (Ctrl K), ligação documento ↔ seção do livro feita pelo motor e embeddings locais como
candidatos para busca e vínculos, decididos por gabaritos revisados pelo usuário.

**Architecture:** Um pacote `estudos.avaliacao` mede tudo contra gabaritos TOML. `estudos.ia.embeddings` é o único ponto
de troca do provedor (`fastembed`/ONNX). Os vetores ficam no índice derivável (`.indice/indice.db`). A busca ganha os
modos `vetor` e `hibrida` (RRF), e `vinculo.py` ganha uma nota combinada opcional. Tudo começa **desligado**, e só a
avaliação liga.

**Tech Stack:** Python 3.13, FastAPI, SQLite/FTS5, NumPy, fastembed (ONNX Runtime) · Svelte 5, Vite, TypeScript,
Vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-10-26-fase-6b-busca-design.md`

## Global Constraints

- Tudo em português (código, nomes, mensagens, commits), como no resto do projeto.
- Padrões até a avaliação: `embeddings = false`, `busca = "texto"`, `vinculos_com_embeddings = false`,
  `peso_sentido_vinculo = 0.5`.
- Com tudo desligado, busca e vínculos têm resultado **idêntico** ao atual.
- Nenhum teste da suíte padrão (nem do CI) baixa modelo. Testes usam `EmbeddingsFalso`; o teste com o modelo real é
  marcado `modelo` e fica fora da suíte padrão.
- O índice continua derivável e fora do Git. O cache de modelos fica em `_app/.modelos/` (no `.gitignore`).
- RRF com k = 60 fixo; top-50 de cada modo antes da fusão.
- Nada chutado: ligação documento ↔ seção abaixo do limiar vira **sugestão** e nunca é gravada. Ligação existente
  (`secao_id` não nulo) **nunca** é sobrescrita automaticamente.
- Toda escrita no `materia.db` passa por `historico.operacao` (desfazível).
- Commits terminam com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Mensagens vão em arquivo, sem BOM.
- Não commitar `Calculo 2/materia.db` nem as pastas de matéria não versionadas.

## Review Focus

1. **Pergunta vazia, de 1 letra ou só com palavras vazias ("de a o"):** a paleta não chama o motor ou recebe lista
   vazia, sem erro (teste na Task 3; teste do motor na Task 8 para `vetor` e `hibrida`).
2. **`embeddings = true` sem internet na primeira vez:** busca e vínculos caem para texto e regra, com um aviso, e nada
   trava (teste na Task 7).
3. **Documento ligado à mão e depois renomeado:** a ligação manual continua (teste na Task 4).
4. **Índice antigo (versão 1) já no disco:** a primeira busca depois da atualização refaz o índice sem erro na tela
   (teste na Task 7).
5. **Matéria sem livro principal, ou sem nenhum livro:** documento ↔ seção não quebra; sem livro principal, a confiança
   máxima fica abaixo do limiar e só sobra sugestão (teste na Task 4).

---

### Task 1: Pacote de avaliação (gabaritos, métricas, comando)

**Files:**
- Create: `_app/backend/estudos/avaliacao/__init__.py`, `gabarito.py`, `metricas.py`, `busca.py`, `relatorio.py`,
  `__main__.py`
- Modify: `_app/backend/tests/conftest.py` (recebe o fixture `cenario` de `tests/test_rag_busca.py` como
  `cenario_busca`, reaproveitado por `test_rag_busca.py` e pelos testes novos das Tasks 1, 7 e 8)
- Test: `_app/backend/tests/test_avaliacao.py`

**Interfaces:**
- Produces:
  - `gabarito.PerguntaBusca(texto: str, estilo: Literal["exata","parafrase"], aceitas: tuple[str, ...], unidade: int | None)`
  - `gabarito.ler_busca(caminho: Path) -> list[PerguntaBusca]`. Valida `estilo` e o formato de `aceitas`
    (`"secao:<código>"` ou `"documento:<título>"`) e levanta `ValueError` com o número da pergunta.
  - `metricas.acerto_em(posicoes: list[int | None], k: int) -> float`, `metricas.mrr(posicoes, k=10) -> float`
    (posição 1-based ou `None`).
  - `busca.Configuracao(nome: str, modo: str, modelo: str | None)`
  - `busca.avaliar(con, raiz: Path, perguntas, configuracoes, pasta_temp: Path) -> list[LinhaBusca]`. Cada configuração
    roda num **índice temporário** em `pasta_temp` (`sincronizar(con, raiz, caminho_indice_=...)`), nunca no real.
  - `busca.LinhaBusca` tem os campos `nome, acerto5, acerto5_exata, acerto5_parafrase, mrr10, indexacao_s, p50_ms,
    p95_ms, memoria_mb`.
  - `relatorio.tabela_busca(linhas) -> str` (Markdown) e
    `relatorio.gravar(conteudo: str, pasta: Path, tipo: str, hoje: date) -> Path`, que grava
    `docs/avaliacoes/AAAA-MM-DD-<tipo>.md`.
  - CLI: `python -m estudos.avaliacao busca --materia "<nome>" [--gabarito <toml>] [--configs texto,...]`.

- [ ] **Step 1: Write the failing tests**

```python
def test_acerto_e_mrr():
    assert acerto_em([1, 3, None, 6], k=5) == 0.5
    assert mrr([1, 2, None], k=10) == pytest.approx((1 + 0.5 + 0) / 3)

def test_ler_busca_valida_estilo_e_aceitas(tmp_path):
    arq = tmp_path / "g.toml"
    arq.write_text('[[pergunta]]\ntexto = "x"\nestilo = "parafrase"\naceitas = ["secao:15.4"]\n', encoding="utf-8")
    [p] = ler_busca(arq)
    assert p.aceitas == ("secao:15.4",) and p.unidade is None
    arq.write_text('[[pergunta]]\ntexto = "x"\nestilo = "outro"\naceitas = ["secao:1"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="pergunta 1"):
        ler_busca(arq)

def test_avaliar_usa_indice_temporario_e_nao_toca_o_real(con, materia, cenario_busca, tmp_path):
    # cenario_busca = o fixture `cenario` de tests/test_rag_busca.py, movido para conftest.py nesta task
    real = caminho_indice(materia.pasta)
    antes = real.stat().st_mtime if real.exists() else None
    [linha] = avaliar(con, materia.pasta,
                      [PerguntaBusca("integral dupla polares", "exata", ("secao:15.4",), None)],
                      [Configuracao("texto", "texto", None)], tmp_path)
    assert linha.nome == "texto" and 0 <= linha.acerto5 <= 1
    assert (real.stat().st_mtime if real.exists() else None) == antes
```

- [ ] **Step 2: Run** `.venv/Scripts/python.exe -m pytest tests/test_avaliacao.py -q`. Expected: FAIL (módulo não existe).
- [ ] **Step 3: Implement** os módulos acima.
  - A posição de uma pergunta é a 1ª posição em que o resultado casa alguma aceita: `secao:<c>` casa
    `resultado.secao_codigo == c`, e `documento:<t>` casa o título do documento do resultado.
  - Busca com `limite=10`.
  - Latência medida com `time.perf_counter` por pergunta; memória com `tracemalloc` (pico).
- [ ] **Step 4: Run** a suíte do backend. Expected: tudo PASS.
- [ ] **Step 5: Commit** — `feat: avaliação da busca por gabarito (métricas, índice temporário, comando)`

### Task 2: Gabaritos do Cálculo 2 e linha de base (com revisão do usuário)

**Files:**
- Create: `_app/backend/estudos/avaliacao/gabaritos/calculo2_busca.toml`,
  `docs/avaliacoes/<data>-busca.md` (gerado)

**Interfaces:**
- Consumes: `ler_busca`, CLI da Task 1.

- [ ] **Step 1: Rascunhar ~40 perguntas.**
  - Metade `exata`, metade `parafrase`, cobrindo as 3 unidades.
  - Cada uma com `aceitas` (seções do Stewart por código; documentos quando a resposta é um texto). Uma pergunta pode
    aceitar mais de uma seção.
  - Conferir no `materia.db` real (somente leitura) que cada código aceito existe.
- [ ] **Step 2: Apresentar o rascunho ao usuário como tabela** (pergunta · estilo · aceitas) e **parar até ele
  revisar**. Aplicar as correções e as perguntas que ele acrescentar.
- [ ] **Step 3: Run**
  `.venv/Scripts/python.exe -m estudos.avaliacao busca --materia "Calculo 2" --configs texto --gravar`.
  Expected: tabela com a linha `texto` e um arquivo em `docs/avaliacoes/`.
- [ ] **Step 4: Commit** — `test: gabarito de busca do Cálculo 2 e linha de base (BM25)`

### Task 3: Busca na interface (Ctrl K) sobre a busca atual

**Files:**
- Create: `_app/frontend/src/componentes/BuscaMateria.svelte`, `BuscaMateria.test.ts`
- Modify:
  - `src/componentes/Topo.svelte`: campo-gatilho "Buscar na matéria…" com a dica `Ctrl K`;
  - `src/App.svelte`: Ctrl K em `teclado()` abre a paleta nas telas da matéria;
  - `src/estado/pedido.svelte.ts`: pedidos `fonte: {id, pagina} | null` e `ancora: string | null`;
  - `src/rotas/Documentos.svelte`: consome o pedido de fonte e abre o `VisualizadorPdf` com `paginaInicial`;
    consome a âncora;
  - `src/componentes/Markdown.svelte` / `src/markdown.ts`: títulos `##` ganham `id` estável (slug do texto) para a
    âncora;
  - `src/api/tipos.ts`: `ResultadoBusca`.
- Test: `src/componentes/BuscaMateria.test.ts`, `tests/e2e/fluxo.spec.ts`

**Interfaces:**
- Consumes: `GET /api/materias/{uid}/busca?q&unidade&tipo&limite` (existente). A resposta tem `{resultados, sincronizacao}`.
- Produces: `BuscaMateria` com as props `{ uid: string; unidade: number | null; aberta: boolean; onfechar: () => void }`.
  - Tipos por filtro: Livros = `livro`, `gabarito`; Listas e provas = `lista`, `prova`, `slides`;
    Textos = `resumo`, `resolucao`, `anotacao`, `plano`, `contexto`.
  - Abrir: `fonte_id` → `pedido.fonte = {id, pagina}` e vai para Documentos; `documento_id` → `pedido.documento` +
    `pedido.ancora = slug(título do trecho)`.

- [ ] **Step 1: Write the failing tests** (`BuscaMateria.test.ts`, fetch simulado como em `FilaImportacao.test.ts`)

```ts
test('digita, espera e mostra resultados agrupados; Enter abre o PDF na página', ...)
// q="polares" → grupo "Livros" com "15.4 … · p. 406"; ArrowDown + Enter → pedido.fonte = {id: 1, pagina: 406}, location.hash termina em '/documentos'
test('menos de 2 letras ou só palavras vazias não chama o motor', ...)          // Review Focus 1
test('filtro Toda a matéria tira o parâmetro unidade; filtro Textos manda os tipos de texto', ...)
test('nada encontrado oferece buscar na matéria toda', ...)
test('sincronização em andamento mostra "Montando o índice…"', ...)              // sincronizacao.avisos não vazio
test('Esc fecha', ...)
```

- [ ] **Step 2: Run** `npx vitest run src/componentes/BuscaMateria.test.ts`. Expected: FAIL.
- [ ] **Step 3: Implement.**
  - Espera de 200 ms a partir de 2 letras. A paleta reaproveita o padrão de teclado do `Seletor` (setas, Enter, Esc).
  - Trecho com `[` `]` do snippet do FTS vira `<mark>` (escapando o resto).
  - Visual nos tokens do tema e destaque laranja no item ativo.
- [ ] **Step 4: e2e.** Em `fluxo.spec.ts`: Ctrl K, digitar um termo do PDF da fixture, Enter e conferir que o PDF da
  fonte aparece em Documentos.
- [ ] **Step 5: Run** `npm test`, `npm run check`, `npm run build`, `npm run e2e`. Expected: tudo verde.
- [ ] **Step 6: Commit** — `feat: busca na matéria com Ctrl K`

### Task 4: Ligação documento ↔ seção no motor (regras)

**Files:**
- Modify: `_app/backend/estudos/importacao/vinculo.py`, `estudos/repos/documentos.py`, `estudos/modelos.py`,
  `estudos/api/documentos.py`, `estudos/api/esquemas.py`, `estudos/api/respostas.py`
- Test: `_app/backend/tests/test_vinculo_documento.py`, `tests/test_api_documentos.py`

**Interfaces:**
- Produces:
  - `vinculo.SugestaoSecao(secao_id: int, codigo: str, titulo: str, confianca: float, por: str)`, com `por` ∈
    {"questao","codigo","palavras"} nesta task (a Task 9 acrescenta "sentido" e "ambos").
  - `vinculo.secao_do_documento(con, documento: Documento, limiar: float) -> SugestaoSecao | None`, com as regras da
    spec §3.6:
    1. `questao_id` → a seção da lista da questão (`lista_secao`): confiança 1,0, `por="questao"`.
    2. Código no início do título (regex `^\D*?(\d+(?:\.\d+)+)`, que pega "14.7" em "Resolução 14.7-3"):
       - entre as seções com esse código, prefere o livro `papel='principal'`;
       - confiança = `0.5 + 0.5 · similaridade(título sem o código, título da seção)`, com `por="codigo"`;
       - se o único casamento for de livro complementar, multiplica por 0,8.
    3. Sem código: `melhores(título, seções de todos os livros, limiar)`. Confiança = nota; `por="palavras"`.
    4. Devolve `None` sem candidato. Só tipos `resumo`, `resolucao`, `plano`.
  - `documentos.ligar_secao(op, raiz: Path, documento_id: int, secao_id: int | None) -> None`: regrava o
    frontmatter, mantém o corpo e atualiza a linha.
  - `documentos.ligar_sem_secao(op, raiz, limiar_gravar: float) -> int`: para cada documento elegível com
    `secao_id IS NULL`, grava só se `confianca >= limiar_gravar` e devolve quantos gravou.
  - `Documento` (modelo e resposta da API) ganha `secao_codigo: str | None` e `secao_posicao: int | None`. A posição
    vem de `listar` por JOIN: livros ordenados por `papel='principal'` primeiro e depois `fonte_id`; seções por
    `pagina_pdf_ini`, numeradas 1..n.
  - API:
    - `GET /documentos/{id}/sugestao-secao` → `SugestaoSecao | null` (não grava);
    - `PUT /documentos/{id}/secao` com `{secao_id: int | null}` → `Ok` (operação "Ligar documento à seção");
    - `POST /documentos/ligar-secoes` → `{ligados: int}` (operação "Ligar documentos às seções do livro");
    - salvar documento (`PUT` existente) com `secao_id` ausente ou nulo e documento ainda sem seção tenta ligar
      com o mesmo limiar.
  - Limiar de gravar: `settings.limiar_confianca` (0,75).

- [ ] **Step 1: Write the failing tests**

```python
# fixtures locais deste arquivo: `dois_livros` (Stewart principal e Guidorizzi complementar, ambos com uma seção "14.1"
# de títulos diferentes) e `resolucao_com_questao` (lista ligada à seção 15.4, questão e documento resolução)
def test_resolucao_herda_a_secao_da_lista_da_questao(con, resolucao_com_questao): ...  # por == "questao", confianca == 1.0
def test_codigo_prefere_livro_principal(con, dois_livros):                          # Stewart principal "Funções…", Guidorizzi "Derivadas…"
    s = secao_do_documento(con, doc("14.1 Funções de várias variáveis"), 0.35)
    assert s.codigo == "14.1" and s.titulo.startswith("Funções") and s.confianca >= 0.75
def test_codigo_que_bate_so_em_complementar_com_titulo_diferente_nao_grava(...):  # confianca < 0.75
def test_sem_codigo_usa_semelhanca_de_titulo(...):                                 # "Coordenadas polares" → seção de polares, por == "palavras"
def test_sem_candidato_devolve_none(...)
def test_sem_livro_principal_so_sugere(...):                                       # Review Focus 5: confianca < limiar_confianca
def test_ligar_sem_secao_grava_so_confiantes_e_pode_ser_desfeita(...):             # desfazer() devolve secao_id NULL
def test_renomear_documento_ligado_a_mao_mantem_a_secao(...):                      # Review Focus 3
def test_listar_traz_codigo_e_posicao_na_ordem_do_livro(...):                      # 14.1 < 14.2 < 15.4; sem seção → posicao None
```

- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** as interfaces acima.
- [ ] **Step 4: Run** a suíte do backend. Expected: tudo PASS.
- [ ] **Step 5: Regerar os tipos do frontend** com `npm run tipos -- http://127.0.0.1:8793/openapi.json`, apontando para um motor de teste com o código
  novo (`tests/e2e/servidor_e2e.py <pasta temporária> 8793`). A 8790 é o servidor do usuário, com o código antigo e commitar junto.
- [ ] **Step 6: Commit** — `feat: motor liga resumos, resoluções e planos à seção do livro`

### Task 5: Documento ↔ seção na interface

**Files:**
- Modify:
  - `src/componentes/ListaDocumentos.svelte`: ordena por `secao_posicao`, com os sem posição no fim, por nome;
  - `src/apresentacao.ts`: remove `ordenarPeloAssunto`, `documentoDoTopico` e `palavrasChave`, se ficarem sem uso;
  - `src/rotas/Documentos.svelte`: no `mount`, chama `POST ligar-secoes` uma vez e recarrega o painel se `ligados > 0`;
    ao abrir um documento sem seção, busca a sugestão e mostra a faixa "Ligar à seção 14.7 — Valores Máximo e
    Mínimo? [Sim] [Escolher outra]"; o cabeçalho mostra o `Seletor` "Seção do livro" (seções de todos os livros,
    com a opção "Sem seção");
  - `src/componentes/ProximoPasso.svelte`: o resumo do tópico vem de
    `documentos.find(d => d.tipo === 'resumo' && seçõesDoTópico.has(d.secao_id))`, com as seções de
    `vinculos.topicos[topico.id]`.
- Test: `src/componentes/ListaDocumentos.test.ts`, `src/apresentacao.test.ts`, `src/rotas/Painel.test.ts`,
  `src/rotas/Documentos.test.ts` (novo)

- [ ] **Step 1: Write the failing tests**

```ts
test('resumos na ordem do livro; sem seção no fim, por nome', ...)        // posicoes 3,1,null,2 → 1,2,3,null
test('documento sem seção mostra a sugestão e "Sim" liga', ...)           // PUT /documentos/7/secao {secao_id: 42}
test('Escolher outra abre o seletor de seção; "Sem seção" desliga', ...)
test('próximo passo acha o resumo pela seção do tópico', ...)
```
Remover os testes de `ordenarPeloAssunto` e `documentoDoTopico` junto com as funções.

- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `npm test`, `npm run check`, `npm run build`, `npm run e2e`. Expected: tudo verde.
- [ ] **Step 5: Conferir com os dados reais** num servidor só de leitura numa **cópia** do Cálculo 2. O
  `ligar-secoes` grava, então nunca rodar no `materia.db` real. Ordem esperada na 1ª unidade: 14.1, Coordenadas polares
  (se ligada a uma seção de polares), 14.2…
- [ ] **Step 6: Commit** — `feat: documentos na ordem do livro e ligação de seção na interface`

### Task 6: Avaliação dos vínculos e gabarito de vínculos (com revisão do usuário)

**Files:**
- Create: `estudos/avaliacao/vinculos.py`, `estudos/avaliacao/gabaritos/calculo2_vinculos.toml`
- Modify: `estudos/avaliacao/gabarito.py` (`ler_vinculos`), `__main__.py` (subcomando `vinculos`),
  `relatorio.py` (`tabela_vinculos`)
- Test: `tests/test_avaliacao.py`

**Interfaces:**
- Produces:
  - Gabarito em três listas:
    - `[[topico]] titulo, unidade, secao`;
    - `[[lista]] titulo, unidade`;
    - `[[documento]] titulo, secao` (`secao = ""` quando o certo é **não** ligar).
  - `vinculos.avaliar(con, gabarito, configuracoes: list[ConfigVinculo], limiar_gravar: float) -> list[LinhaVinculo]`.
    Usa `melhores`/`secao_do_documento` diretamente sobre o banco lido, sem gravar.
  - `LinhaVinculo(nome, acertos, total, erros_confiantes, para_revisao)`. Erro confiante é a escolha errada com
    `confianca >= limiar_gravar`.
  - `ConfigVinculo(nome: str, semantica: object | None, peso: float)` (na Task 9 `semantica` passa a ser usada).

- [ ] **Step 1: Write the failing tests:** leitura do gabarito; contagem de acertos, erros confiantes e itens para
  revisão com candidatos de mentira (incluindo um caso "não ligar" que vira erro se ligar com confiança alta).
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Rascunhar `calculo2_vinculos.toml`.**
  - Tópicos e listas a partir dos vínculos atuais do banco real (somente leitura).
  - Documentos a partir do código no título e da questão.
  - Casos difíceis obrigatórios: "14.7 Valores máximo e mínimo", "Coordenadas polares" e um "14.1".
  - Apresentar como tabela e **parar até o usuário revisar**.
- [ ] **Step 5: Run** `python -m estudos.avaliacao vinculos --materia "Calculo 2" --configs regra --gravar`.
  Expected: linha `regra` e um arquivo em `docs/avaliacoes/`.
- [ ] **Step 6: Commit** — `feat: avaliação dos vínculos e linha de base`

### Task 7: Provedor de embeddings e vetores no índice

**Files:**
- Create: `_app/backend/estudos/ia/__init__.py`, `estudos/ia/embeddings.py`
- Modify:
  - `estudos/config.py`: `Settings.embeddings: bool = False`, `modelo = "intfloat/multilingual-e5-small"`,
    `busca = "texto"`, `vinculos_com_embeddings = False`, `peso_sentido_vinculo = 0.5`, e a seção `inteligencia` em
    `_MAPA_TOML`;
  - `_app/config.toml`: seção `[inteligencia]` comentada, como na spec §3.7;
  - `.gitignore`: `_app/.modelos/`;
  - `_app/backend/pyproject.toml`: dependências `fastembed`, `numpy`; marcador pytest `modelo` excluído por padrão
    (`addopts = "-m 'not modelo'"`);
  - `estudos/rag/indice.py`: `VERSAO_INDICE = 2`; `trecho.vetor BLOB`; tabela `meta (chave TEXT PRIMARY KEY, valor TEXT)`
    com `modelo` e `dimensao` (a tabela `estado` já é por origem, por isso a tabela nova);
  - `estudos/rag/indexador.py`: `sincronizar(..., embeddings: Embeddings | None = None)` gera vetores dos trechos
    gravados nesta sincronização, em lotes de 64, e preenche `vetor` dos trechos com `vetor IS NULL`. Modelo ou dimensão
    diferente do `meta` limpa todos os vetores e regrava o `meta`.
- Test: `tests/test_embeddings.py`, `tests/test_rag_indexador.py` (ampliar)

**Interfaces:**
- Produces:
  - `Embeddings` (Protocol, como na spec §3.2).
  - `EmbeddingsFalso(dimensao=32)`: soma vetores pseudoaleatórios fixos por radical (`hash` estável → `np.random.default_rng(seed)`)
    e normaliza. Textos com radicais em comum ficam próximos.
  - `FastEmbed(modelo: str, cache: Path)`: prefixos `passage: `/`query: ` quando o nome contém `e5`. O carregamento
    é preguiçoso.
  - `obter_embeddings(settings) -> Embeddings | None`:
    - `None` se `settings.embeddings` for falso;
    - se o carregamento falhar (sem rede, arquivo corrompido, ONNX incompatível), registra um aviso **uma vez** (log
      e `avisos` da próxima sincronização) e devolve `None`;
    - guarda uma instância por processo.
  - `vetores_do_indice(indice) -> tuple[np.ndarray, list[int]]`: matriz e ids dos trechos com vetor, em cache por
    caminho do índice e invalidado pela sincronização.

- [ ] **Step 1: Write the failing tests**

```python
def test_falso_aproxima_textos_com_palavras_em_comum():
    e = EmbeddingsFalso()
    a, b, c = e.de_trechos(["integral dupla polar", "integrais duplas em polares", "regra da cadeia"])
    assert a @ b > a @ c
def test_sincronizar_grava_vetores_e_meta(con, materia, cenario_busca): ...           # todos os trechos com vetor; meta.modelo == e.nome
def test_trocar_de_modelo_refaz_os_vetores(...): ...
def test_sem_embeddings_indice_fica_valido_e_sem_vetores(...): ...
def test_indice_versao_1_e_refeito_sem_erro(...): ...                                  # Review Focus 4
def test_falha_ao_carregar_modelo_devolve_none_e_avisa_uma_vez(monkeypatch): ...      # Review Focus 2
@pytest.mark.modelo
def test_fastembed_real_gera_vetor(): ...                                              # dimensão 384, norma ≈ 1
```

- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Confirmar o catálogo:**
  `python -c "from fastembed import TextEmbedding as T; print([m['model'] for m in T.list_supported_models()])"`.
  - Se `intfloat/multilingual-e5-small` não estiver no catálogo, registrá-lo com
    `TextEmbedding.add_custom_model(...)` a partir do ONNX do Hugging Face.
  - Se nem isso funcionar, usar `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` e registrar a troca no
    ledger e na avaliação.
  - O mesmo vale para o base (`multilingual-e5-base`).
- [ ] **Step 4: Implement.**
- [ ] **Step 5: Run** a suíte do backend (sem `modelo`) e depois `pytest -m modelo -q`. Expected: tudo PASS.
- [ ] **Step 6: Commit** — `feat: embeddings locais (fastembed) e vetores no índice, desligados por padrão`

### Task 8: Busca `vetor` e `hibrida`

**Files:**
- Modify: `estudos/rag/busca.py`, `estudos/api/rag.py`, `estudos/api/respostas.py`,
  `src/componentes/BuscaMateria.svelte` (etiqueta "pelo sentido")
- Test: `tests/test_rag_busca.py` (ampliar), `src/componentes/BuscaMateria.test.ts`

**Interfaces:**
- Consumes: `Embeddings`, `vetores_do_indice` (Task 7).
- Produces:
  - `buscar(..., modo: str = "texto", embeddings: Embeddings | None = None)`. `Resultado` ganha `por: str`
    ("texto" | "sentido" | "ambos").
  - `vetor`: top-50 por cosseno entre os ids que passam pelos filtros (mesmos filtros SQL, sem o MATCH). O trecho
    exibido são os primeiros 240 caracteres.
  - `hibrida`: top-50 de cada modo e `nota = Σ 1/(60 + posição)`. `por` vem de onde o trecho apareceu.
  - Sem `embeddings` ou sem vetores, cai para `texto`, e a função devolve o modo efetivo.
  - `GET /busca?modo=` usa `settings.busca` por padrão; a resposta ganha `modo`.

- [ ] **Step 1: Write the failing tests:**
  - RRF (ordem esperada num caso montado à mão);
  - `vetor` e `hibrida` respeitam unidade, seção e tipo;
  - queda para `texto` sem vetores;
  - pergunta vazia ou só com palavras vazias devolve `[]` nos três modos (Review Focus 1);
  - com tudo desligado, a API devolve o **mesmo** resultado de antes (comparar com o snapshot do modo `texto`);
  - Vitest: resultado com `por: 'sentido'` mostra "pelo sentido".
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** as suítes do backend e do frontend. Expected: tudo verde.
- [ ] **Step 5: Ampliar o comando:** `--configs texto,vetor:small,vetor:base,hibrida:small,hibrida:base` (o nome curto
  mapeia para o modelo confirmado na Task 7).
- [ ] **Step 6: Commit** — `feat: busca por sentido e híbrida (RRF), atrás do config`

### Task 9: Nota combinada nos vínculos

**Files:**
- Modify: `estudos/importacao/vinculo.py`, `estudos/importacao/pipeline.py`, `estudos/avaliacao/vinculos.py`,
  `src/componentes/PropostaLivro.svelte` / `PropostaLista.svelte` / `PropostaPrograma.svelte` (mostrar o motivo)
- Test: `tests/test_importacao_vinculo.py` (ampliar), `tests/test_vinculo_documento.py`

**Interfaces:**
- Consumes: `Embeddings`.
- Produces:
  - `Semantica(embeddings: Embeddings)` com `similaridades(texto: str, titulos: list[str]) -> list[float]`, em
    `(1 + cos) / 2`, guardando em cache os vetores dos títulos por lista.
  - `pontuar(..., semantica: Semantica | None = None, peso: float = 0.5)` e `melhores(...)` com os mesmos parâmetros:
    `nota = (1 − peso) · regra + peso · sentido`.
  - `Vinculo` ganha `por: str`: "palavras" se `sentido < 0.6`; "sentido" se `regra == 0`; senão "ambos".
  - `secao_do_documento(..., semantica=None, peso=0.5)` também combina; `SugestaoSecao.por` pode ser "sentido" ou
    "ambos".
  - `pipeline` passa `Semantica(obter_embeddings(settings))` só quando `settings.vinculos_com_embeddings` e o provedor
    existe.
  - O motivo aparece na proposta da importação: "por palavras", "pelo sentido" ou "pelos dois".

- [ ] **Step 1: Write the failing tests:**
  - com `semantica=None`, `pontuar` e `melhores` devolvem **exatamente** o mesmo de antes (mesmos números);
  - com `EmbeddingsFalso`, um par sem palavras em comum mas com radicais próximos sobe;
  - `por` correto nos três casos;
  - o pipeline sem embeddings não muda o resultado da importação da fixture existente.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** as suítes do backend e do frontend. Expected: tudo verde.
- [ ] **Step 5: Ampliar o comando:** `vinculos --configs regra,sentido:small@0.3,sentido:small@0.5,sentido:small@0.7`.
- [ ] **Step 6: Commit** — `feat: vínculos com nota combinada (regra + sentido), atrás do config`

### Task 10: Rodar as avaliações, decidir e registrar

**Files:**
- Modify: `_app/config.toml` e `estudos/config.py` (padrões, só se as regras mandarem),
  `docs/superpowers/specs/2026-10-26-fase-6b-busca-design.md` (emenda "Resultado da avaliação")
- Create: `docs/avaliacoes/<data>-busca.md`, `docs/avaliacoes/<data>-vinculos.md`

- [ ] **Step 1: Run**
  `python -m estudos.avaliacao busca --materia "Calculo 2" --configs texto,vetor:small,vetor:base,hibrida:small,hibrida:base --gravar`.
  O download do modelo acontece aqui, na primeira vez.
- [ ] **Step 2: Aplicar as regras da spec §4.4 à tabela,** sem mudar as regras. Escrever no relatório qual regra
  passou ou falhou e por quê.
- [ ] **Step 3: Run** `vinculos` com as configurações da Task 9. Aplicar as regras de vínculos. Se os embeddings
  entrarem, recalibrar `limiar_vinculo` e `limiar_confianca` com o mesmo gabarito, minimizando os erros confiantes e
  depois os itens para revisão, e registrar os valores.
- [ ] **Step 4: Mostrar as tabelas e a decisão ao usuário e parar** até ele concordar.
- [ ] **Step 5: Atualizar os padrões** no `config.toml` e no `Settings` (se for o caso). Escrever a emenda na spec com
  os números e as decisões.
- [ ] **Step 6: Run** todas as suítes (backend, `npm test`, `npm run check`, `npm run build`, `npm run e2e`).
  Expected: verde.
- [ ] **Step 7: Commit** — `docs: avaliação da peça B e novos padrões da inteligência`
