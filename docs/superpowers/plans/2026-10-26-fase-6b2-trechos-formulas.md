# Peça B2 — Trechos por parte do livro e texto limpo das fórmulas · Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** separar no índice a teoria, os exercícios e as respostas dos livros e limpar o texto das fórmulas, medindo
cada passo na avaliação v3.

**Architecture:** um módulo novo de corte (`rag/corte.py`) recebe o texto contínuo das páginas do livro e as seções
e devolve trechos marcados com `parte` e `numero`. O índice passa para v4. A busca filtra por parte e a API devolve
dois grupos. Depois, `importacao/pdf.py` ganha uma leitura por fonte e posição (`ler_paginas_limpas`) com tabelas por
fonte (`importacao/fontes_matematicas.py`), usada só pelo indexador.

**Tech Stack:** Python 3.13, PyMuPDF, SQLite FTS5, FastAPI, pytest; Svelte 5 + TS, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-26-fase-6b2-trechos-formulas-design.md`

## Global Constraints

- Os PDFs, os `.md` e o `materia.db` do usuário não são alterados; só o índice derivado (`.indice/`) é refeito.
- Nunca commitar `Calculo 2/`, `Geometria Analítica/`, `calculo 1(teste)/`, `.claude/` nem
  `docs/superpowers/specs/2026-10-22-sugestao-antigravity-fase-6-embeddings-ia.md`.
- Testes não dependem dos PDFs do usuário: amostras vão como JSON em `tests/fixtures/paginas/`.
- A leitura nova (`ler_paginas_limpas`) só é usada pelo indexador; a importação de livros e listas não muda.
- Partes do trecho: exatamente `teoria`, `exercicio`, `resposta`.
- Versão do índice: a spec diz v4; como o texto muda de novo na Task 6 sem mudar a assinatura das fontes, a Task 6
  sobe para v5 (refeito sozinho, sem efeito para o usuário além de uma reindexação).
- Limite de teoria candidato: 800, 1.200 e 1.600 caracteres; exercícios com menos de 200 caracteres se juntam ao
  seguinte; o grupo de exercícios da busca traz os 3 melhores.
- Critério do passo 1: acerto@5 da teoria sobe em pelo menos uma matéria (base: Cálculo 2 77%, Geometria 75%) sem cair
  na outra, e links não pioram. Passo 2: não baixa o acerto do passo 1 e as páginas de amostra passam.
- Backend: `cd _app/backend && .venv/Scripts/python -m pytest -q`. Frontend: `cd _app/frontend && npm test` e
  `npm run check`. Tipos da API: `npm run tipos -- http://127.0.0.1:<porta>/openapi.json` com um servidor sobre uma
  pasta temporária (nunca o 8790 do usuário).
- Mensagens de commit gravadas em arquivo e terminadas em `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. Título da seção que não aparece no texto (OCR ruim, título abreviado no livro): o corte cai para o limite de
   página, como hoje, sem perder texto — teste `test_titulo_ausente_cai_para_a_pagina` (Task 1).
2. Linha numerada que não é exercício ("1. As Homeworks Hints…" antes do exercício 1 real; "2." dentro de uma
   conta): não abre exercício fora de sequência e não perde o exercício real — `test_numeracao_reinicia_e_ignora_fora_de_sequencia` (Task 1).
3. Gabarito com seção do livro que não existe no banco ou sem gabarito cadastrado: respostas dessa seção ficam fora,
   o resto do livro indexa — `test_gabarito_com_codigo_desconhecido` (Task 1).
4. PDF em que a leitura detalhada levanta erro numa página: só essa página usa a leitura atual —
   `test_pagina_com_erro_usa_a_leitura_atual` (Task 5).
5. "Ver no livro" numa questão cujo rótulo não é número (`22a`, `R1`) ou cuja lista não tem seção: o botão não
   aparece e nada quebra — `test_exercicio_inexistente_404` e `DetalheQuestao` "sem exercício no índice" (Task 4).

---

### Task 1: Corte do livro em teoria, exercícios e respostas

**Files:**
- Create: `_app/backend/estudos/rag/corte.py`
- Modify: `_app/backend/estudos/rag/trechos.py` (`TrechoNovo`)
- Test: `_app/backend/tests/test_rag_corte.py`

**Interfaces:**
- Produces:
  - `TrechoNovo` ganha `parte: str = "teoria"`, `numero: int | None = None`, `secao_id: int | None = None`.
  - `@dataclass(frozen=True) class SecaoCorte: id: int; codigo: str; titulo: str; pagina_ini: int; pagina_fim: int`
  - `cortar_livro(paginas: list[tuple[int, str]], secoes: list[SecaoCorte], limite: int) -> list[TrechoNovo]`
    — `secoes` são as folhas (sem subseções), em ordem de página; cada trecho sai com `secao_id`, `parte` e,
    nos exercícios, `numero`; título do trecho = `f"{codigo} {titulo}"`.
  - `cortar_gabarito(paginas: list[tuple[int, str]], codigos: dict[str, int], limite: int) -> list[TrechoNovo]`
    — `codigos` = código da seção → `secao_id`; trechos `parte="resposta"`, com `secao_id` e `numero`;
    título `f"Respostas {codigo}"`.

Regras (do spec §3.1, com o achado da leitura do Stewart): o texto das páginas é tratado como **um fluxo contínuo**;
cada seção começa na linha do seu título dentro do fluxo, a partir da sua `pagina_ini` — uma linha (ou duas linhas
seguidas) cujo texto normalizado (`sem_acento`, minúsculas, espaços colapsados) começa pelo código e contém o título,
ou é igual ao título. O texto antes do título, na primeira página, pertence à seção anterior. Título não achado: a
seção começa no início da sua `pagina_ini` (comportamento de hoje). Dentro da seção, a linha que começa com
`Exercícios` (seguida ou não do código, na mesma linha ou na seguinte) separa teoria de exercícios. Exercícios
começam em linhas `^\d{1,3}\.\s` com número = anterior + 1; um `1.` reinicia a contagem (o que veio antes vira
prefixo do exercício 1); trechos de exercício com menos de 200 caracteres se juntam ao seguinte e ficam com o
número do primeiro. Teoria usa `_agrupar` de `trechos.py` com `limite`. No gabarito, uma linha que é só um código
conhecido em `codigos` abre a seção; as linhas `N.` abrem as respostas.

- [ ] **Step 1: Escrever os testes**

```python
SECOES = [SecaoCorte(1, "10.3", "Coordenadas polares", 1, 2), SecaoCorte(2, "10.4", "Áreas em coordenadas polares", 2, 3)]
PAGINAS = [
    (1, "10.3 Coordenadas polares\nTeoria das polares, r e theta."),
    (2, "Exercícios\n10.3\n1. As Homeworks Hints estão disponíveis\n1. Esboce r = 2.\n2. Esboce a cardioide r = 1 + cos t, "
        "com bastante texto para passar de duzentos caracteres " + "x" * 200 + "\n"
        "10.4\nÁreas em coordenadas polares\nNesta seção deduziremos a fórmula da área."),
    (3, "Mais teoria da área.\nExercícios 10.4\n1. Calcule a área " + "y" * 220 + "\n5. termo solto\n2. Ache a área 2. de dentro " + "z" * 220),
]

def test_secao_comeca_no_titulo_e_sobra_vai_para_a_anterior():
    ts = cortar_livro(PAGINAS, SECOES, 1600)
    teoria_104 = [t for t in ts if t.secao_id == 2 and t.parte == "teoria"]
    assert teoria_104[0].texto.startswith("10.4") and "Nesta seção" in teoria_104[0].texto
    assert all("Esboce" not in t.texto for t in teoria_104)

def test_numeracao_reinicia_e_ignora_fora_de_sequencia():
    ts = cortar_livro(PAGINAS, SECOES, 1600)
    ex103 = [t for t in ts if t.secao_id == 1 and t.parte == "exercicio"]
    # "1. As Homeworks…" é prefixo; o "1." seguinte reinicia; o exercício 1 (< 200) se junta ao 2 e o trecho fica com 1
    assert [t.numero for t in ex103] == [1]
    assert "Homeworks" in ex103[0].texto and "Esboce r = 2" in ex103[0].texto and "cardioide" in ex103[0].texto
    ex104 = [t for t in ts if t.secao_id == 2 and t.parte == "exercicio"]
    assert [t.numero for t in ex104] == [1, 2]
    assert "5. termo solto" in ex104[0].texto and "2. de dentro" in ex104[1].texto   # fora de sequência não abre

def test_titulo_ausente_cai_para_a_pagina():
    secoes = [SecaoCorte(1, "10.3", "Coordenadas polares", 1, 1), SecaoCorte(2, "10.4", "Título que não está no texto", 2, 3)]
    ts = cortar_livro(PAGINAS, secoes, 1600)
    assert any(t.secao_id == 2 and t.pagina == 2 for t in ts)
    assert "".join(t.texto for t in ts).count("Mais teoria") == 1   # nada perdido nem repetido

def test_secao_sem_exercicios_e_toda_teoria(): ...   # só teoria; nenhum trecho exercicio

def test_gabarito_liga_resposta_ao_exercicio():
    ts = cortar_gabarito([(9, "10.3\n1. r = 2 é um círculo\n3. cardioide\n10.4\n1. π/2")], {"10.3": 1, "10.4": 2}, 1600)
    assert [(t.secao_id, t.numero, t.parte) for t in ts] == [(1, 1, "resposta"), (1, 3, "resposta"), (2, 1, "resposta")]

def test_gabarito_com_codigo_desconhecido():
    ts = cortar_gabarito([(9, "99.9\n1. nada\n10.4\n1. π/2")], {"10.4": 2}, 1600)
    assert [(t.secao_id, t.numero) for t in ts] == [(2, 1)]
```

`test_secao_sem_exercicios_e_toda_teoria`: uma seção de uma página sem `Exercícios` → só trechos `teoria`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_rag_corte.py -q`
Expected: FAIL com `ModuleNotFoundError: estudos.rag.corte`

- [ ] **Step 3: Implementar `corte.py` e os campos novos de `TrechoNovo`**

- [ ] **Step 4: Rodar e ver passar; depois a suíte do RAG**

Run: `.venv/Scripts/python -m pytest tests/test_rag_corte.py tests/test_rag_trechos.py -q`
Expected: PASS

- [ ] **Step 5: Commit** — `feat: corte do livro em teoria, exercícios e respostas`

### Task 2: Índice v4 e busca por parte

**Files:**
- Modify: `_app/backend/estudos/rag/indice.py`, `estudos/rag/indexador.py` (`_inserir`, `_indexar_livro`,
  `sincronizar`), `estudos/rag/busca.py` (`Resultado`, `_filtros`, `buscar`, `buscar_modo`, `_por_sentido`)
- Test: `tests/test_rag_indice.py`, `tests/test_rag_indexador.py`, `tests/test_rag_busca.py`

**Interfaces:**
- Consumes: `cortar_livro`, `cortar_gabarito`, `SecaoCorte` (Task 1).
- Produces:
  - `VERSAO_INDICE = 4`; `trecho.parte TEXT NOT NULL DEFAULT 'teoria'`, `trecho.numero INTEGER`,
    índice `idx_trecho_parte ON trecho (parte)`.
  - `LIMITE_TEORIA = 1600` em `rag/corte.py` (valor final escolhido na Task 3).
  - `sincronizar(..., limite_teoria: int | None = None)` — `None` usa `LIMITE_TEORIA`; repassado até `_indexar_livro`.
  - `Resultado` ganha `parte: str = "teoria"` e `numero: int | None = None`.
  - `buscar(..., partes: list[str] | None = None)` e `buscar_modo(..., partes: list[str] | None = None)`; `None` = todas.
  - `resposta_de(indice, secao_id: int, numero: int) -> Resultado | None` em `busca.py` (trecho `resposta` com a
    mesma seção e número; texto inteiro no campo `trecho`).
  - `exercicio_de(indice, secao_id: int, numero: int) -> Resultado | None` (trecho `exercicio` cujo `numero` é o
    pedido; se o pedido caiu num trecho juntado, o trecho de maior `numero` ≤ pedido na seção, texto inteiro).

`_indexar_livro` com seções: passa as folhas (`SecaoCorte`, das seções sem filhas, em ordem de `pagina_pdf_ini`) e as
páginas de `min(pagina_ini)` a `max(pagina_fim)` para `cortar_livro`; o gabarito vai para `cortar_gabarito` com
`{codigo: id}` de todas as seções; `tipo` continua `"livro"` e `"gabarito"`. Livro sem seções: igual a hoje.

- [ ] **Step 1: Testes**
  - `test_rag_indice.py::test_indice_v3_e_refeito_como_v4` (cria um índice com `PRAGMA user_version = 3` e confere
    que abrir refaz e traz a coluna `parte`), e o teste de versão existente passa a esperar 4.
  - `test_rag_indexador.py::test_livro_com_secoes_grava_partes` (no `cenario_busca`, páginas com `Exercícios 1.1` e
    um gabarito com `1.1\n1. resposta`): existem trechos com `parte` `teoria`, `exercicio` e `resposta`, e a
    resposta tem `secao_id == s11`.
  - `test_rag_indexador.py::test_livro_sem_secoes_igual_a_hoje`: todos `teoria`, mesma contagem de `dividir_paginas`.
  - `test_rag_busca.py::test_filtro_por_parte` (`partes=["teoria"]` não traz exercício; `None` traz os dois) e
    `test_resposta_e_exercicio_de` (acha pelo par seção/número; número inexistente → `None`).
  - Ajustar `PAGINAS_LIVRO` em `conftest.py` se preciso para conter `Exercícios 1.1`, mantendo os testes existentes.
- [ ] **Step 2: Rodar e ver falhar** — `pytest tests/test_rag_indice.py tests/test_rag_indexador.py tests/test_rag_busca.py -q`; Expected: FAIL nos testes novos.
- [ ] **Step 3: Implementar** schema v4, `_inserir` com `parte`/`numero`/`secao_id` do trecho (o `secao_id` do trecho
  vence o `ids`), `_indexar_livro` com o corte, filtro `t.parte IN (...)` em `_filtros`, campos no `Resultado`,
  `resposta_de`/`exercicio_de`.
- [ ] **Step 4: Suíte inteira do backend** — Expected: tudo PASS.
- [ ] **Step 5: Commit** — `feat: índice v4 com parte e número; busca filtra por parte`

### Task 3: Avaliação do passo 1 e escolha do limite

**Files:**
- Modify: `estudos/avaliacao/busca.py` (`_medir`, `LinhaBusca`, `avaliar`), `estudos/avaliacao/relatorio.py`
  (`tabela_busca`), `estudos/avaliacao/__main__.py` (opção `--limite-teoria`)
- Test: `tests/test_avaliacao.py`
- Docs: `docs/avaliacoes/2026-10-26-calculo2-busca.md`, `…-geometriaanalitica-busca.md` (seção "B2 · passo 1")

**Interfaces:**
- Consumes: `buscar_modo(..., partes=)`, `sincronizar(..., limite_teoria=)` (Task 2).
- Produces: `LinhaBusca.acerto20: float`; `avaliar(..., limite_teoria: int | None = None)`; as perguntas buscam com
  `partes=["teoria"]`; a tabela ganha a coluna `acerto@20`.

- [ ] **Step 1: Testes** — `test_avaliacao.py::test_mede_so_a_teoria` (uma pergunta cuja resposta aceita só existe como
  exercício não acerta) e `test_acerto20` (posição 12 conta em @20 e não em @5); `test_tabela_tem_acerto20`.
- [ ] **Step 2: Ver falhar**; **Step 3: Implementar**; **Step 4: Ver passar + suíte.**
- [ ] **Step 5: Rodar a avaliação** nas duas matérias com `--limite-teoria 800`, `1200`, `1600` (configuração `texto`,
  `--gravar` só na rodada final; as matérias são só lidas, índice temporário):
  `.venv/Scripts/python -m estudos.avaliacao busca --materia "Calculo 2" --limite-teoria 1200`
  e o mesmo para `"Geometria Analítica"`. Expected: tabela impressa para cada uma.
- [ ] **Step 6: Escolher o limite pelo critério** (Global Constraints) com o maior acerto somado; gravar em
  `LIMITE_TEORIA`. Nenhum cumpre: manter 1.600 com as partes (o corte em si) se ao menos não piorar, senão registrar
  no ledger e parar para perguntar ao usuário (o passo não entra).
- [ ] **Step 7: Registrar** nos dois relatórios a seção "B2 · passo 1" (tabela dos três limites e o escolhido).
- [ ] **Step 8: Commit** — `test: avaliação do passo 1 da B2 (teoria separada) e limite escolhido`

### Task 4: Dois grupos na busca e "Ver no livro"

**Files:**
- Modify: `estudos/api/rag.py`, `estudos/api/respostas.py` (`ResultadoBusca`, `ExercicioLivro`),
  `frontend/src/componentes/BuscaMateria.svelte`, `frontend/src/componentes/DetalheQuestao.svelte`,
  `frontend/src/api/tipos.gerados.ts` (regenerado)
- Test: `tests/test_api_rag.py`, `frontend/src/componentes/BuscaMateria.test.ts`, `DetalheQuestao.test.ts`

**Interfaces:**
- Consumes: `buscar_modo(..., partes=)`, `resposta_de`, `exercicio_de` (Task 2).
- Produces:
  - `GET /busca` → `ResultadoBusca` com `resultados` (só `teoria`, como hoje) e
    `exercicios: list[ExercicioLivro]` (até 3, `partes=["exercicio"]`), onde
    `ExercicioLivro(TypedDict): exercicio: Resultado; resposta: Resultado | None`.
  - `GET /api/materias/{uid}/secoes/{secao_id}/exercicios/{numero}` → `ExercicioLivro`; 404 (`NaoEncontrado`)
    quando `exercicio_de` dá `None`.

- [ ] **Step 1: Testes**
  - `test_api_rag.py::test_busca_devolve_teoria_e_exercicios` (resultados sem exercício; `exercicios[0].resposta`
    preenchida quando há resposta, `None` quando não há).
  - `test_api_rag.py::test_exercicio_do_livro` e `test_exercicio_inexistente_404`.
  - `BuscaMateria.test.ts`: grupo "Exercícios do livro" aparece com a resposta; clicar abre a fonte na página do
    exercício (`pedido.fonte`); sem exercícios, o grupo não aparece.
  - `DetalheQuestao.test.ts`: lista `14.1`, questão `22`, seção ligada → pede `/secoes/<id>/exercicios/22`; com 200
    mostra "Ver no livro" e, ao clicar, o texto do exercício e a resposta; com 404 o botão não aparece; rótulo
    `22a` ou sem seção → nenhum pedido.
- [ ] **Step 2: Ver falhar** (pytest e `npx vitest run` dos arquivos).
- [ ] **Step 3: Implementar** a API; regenerar `tipos.gerados.ts`; na paleta, um grupo "Exercícios do livro" depois
  dos grupos atuais, cada item com a resposta logo abaixo (texto curto, sem destaque) e entrando na navegação por
  teclado; em `DetalheQuestao`, o pedido só quando `secao` existe, `lista.codigo === secao.codigo` e
  `/^\d+$/.test(questao.rotulo)`; o botão mostra o exercício (`Markdown`, texto simples) e a resposta, e um link
  "Abrir no livro" que usa `pedido.fonte`.
- [ ] **Step 4: Suítes** — backend inteira; `npm test`; `npm run check` com 0 erros.
- [ ] **Step 5: Conferir na tela** com um servidor sobre uma **cópia** do Cálculo 2 numa pasta temporária: Ctrl K
  "área polar" mostra os dois grupos; Listas → 14.1 #22 → "Ver no livro". Screenshot.
- [ ] **Step 6: Commit** — `feat: exercícios do livro na busca e "Ver no livro" na questão`

### Task 5: Leitura por fonte e posição

**Files:**
- Modify: `_app/backend/estudos/importacao/pdf.py`
- Create: `_app/backend/tests/fixtures/paginas/` (JSON das amostras + `esperado/*.txt`), `tests/test_pdf_leitura_limpa.py`
- Create (ferramenta de desenvolvimento): `_app/backend/estudos/avaliacao/amostras.py`

**Interfaces:**
- Produces:
  - `ler_paginas_limpas(caminho: Path, tabelas: dict[str, dict[str, str]] | None = None) -> tuple[list[PaginaPdf], int]`
    — páginas com texto limpo e o total de caracteres de uso privado retirados sem tradução; `tabelas=None` usa
    `TABELAS` de `fontes_matematicas` (Task 6; até lá, `{}`).
  - `montar_texto(spans: list[dict], largura: float, altura: float, tabelas) -> tuple[str, int]` — a parte pura,
    testada com os JSON; cada span: `{"font", "size", "bbox": [x0,y0,x1,y1], "text"}`.
  - `python -m estudos.avaliacao.amostras <pdf> <pagina> <saida.json>` grava os spans de uma página (só leitura).

Algoritmo de `montar_texto`: tirar o prefixo de subconjunto do nome da fonte (`ABCDEF+`); traduzir cada caractere pela
tabela da fonte; colunas = agrupamento dos spans por intervalo horizontal (um vão vertical livre de spans com mais de
5% da largura separa colunas; a coluna mais larga primeiro, as de margem depois); em cada coluna, linhas = spans cuja
faixa vertical se sobrepõe em mais de 50% da altura do menor, ordenados por `x0`; span com `size` < 80% da linha e
centro fora da faixa central vira expoente/índice e gruda sem espaço; espaço entre spans quando o vão horizontal
passa de 15% do `size`; as linhas saem em ordem de posição, então cabeçalho e número de página ficam na borda do
texto e `ler_paginas_limpas` aplica a `remover_repetidos` existente sobre todas as páginas (como `abrir_pdf`), que
os retira; caracteres U+E000–U+F8FF que sobrarem são retirados e contados.
`ler_paginas_limpas` usa `page.get_text("dict")`; erro numa página → aquela página com `limpar_texto(page.get_text())`.

- [ ] **Step 1: Gerar as amostras** (só leitura dos PDFs do usuário): 10 páginas do Stewart (incluir a 1ª da 10.4,
  uma com integrais, uma com a coluna de margem, uma de exercícios, uma do gabarito) e 5 dos slides da Geometria
  (incluir a Aula 11 com ⟨u, v⟩ e ℝⁿ); conferir cada uma contra a página renderizada (`page.get_pixmap`) e escrever à
  mão o `esperado/<nome>.txt` — as linhas da coluna principal na ordem de leitura, com os símbolos certos.
- [ ] **Step 2: Testes** — `test_frases_inteiras_nos_slides` (o esperado da Aula 11 contém
  "a norma de um vetor u do ℝn é definida por" numa linha só), `test_coluna_de_margem_separada`,
  `test_cabecalho_fora` (as 5 amostras do Stewart montadas e passadas por `remover_repetidos`: nenhuma linha
  "CÁLCULO"), `test_sem_uso_privado` e
  `test_pagina_com_erro_usa_a_leitura_atual` (span inválido simulado → texto da leitura atual). Comparação por linhas
  normalizadas (espaços colapsados); para o Stewart sem tabelas, a comparação ignora os símbolos ainda trocados
  (os testes de símbolo são da Task 6).
- [ ] **Step 3: Ver falhar**; **Step 4: Implementar**; **Step 5: Ver passar + suíte.**
- [ ] **Step 6: Commit** — `feat: leitura do PDF por fonte e posição (só para o índice)`

### Task 6: Tabelas das fontes de matemática e indexador com a leitura limpa

**Files:**
- Create: `_app/backend/estudos/importacao/fontes_matematicas.py`
- Modify: `estudos/rag/indexador.py` (`indexar_fonte` usa `ler_paginas_limpas`; aviso), `estudos/rag/busca.py`
  (consulta sem uso privado), `estudos/rag/indice.py` (`VERSAO_INDICE = 5`, para refazer com o texto limpo)
- Test: `tests/test_pdf_leitura_limpa.py`, `tests/test_rag_indexador.py`

**Interfaces:**
- Consumes: `ler_paginas_limpas`, `montar_texto` (Task 5).
- Produces: `TABELAS: dict[str, dict[str, str]]` (nome da fonte sem prefixo → caractere → texto Unicode); aviso
  `"{caminho}: {n} símbolos sem tradução"` em `ResumoSincronizacao.avisos` quando `n > 0`.

- [ ] **Step 1: Montar as tabelas** para cada fonte com caracteres trocados nas amostras e nos PDFs do Cálculo 2 e
  da Geometria (no mínimo `LTSGreek-Italic`, `TECHMath-Mix`, `MathematicalPi-One/Three/Five`, `Symbol`, `MATH`):
  listar os caracteres distintos por fonte e recortar a imagem de cada um (`get_pixmap(clip=bbox)`), conferindo um a
  um. Valores conhecidos: `LTSGreek-Italic` `u`→`θ`, `p`→`π`; `TECHMath-Mix` `¨`→`θ`.
- [ ] **Step 2: Testes** — `test_simbolos_traduzidos` (o esperado da 1ª página da 10.4 contém "θ" e "π" e não contém
  " u, a medida"), `test_fonte_sem_tabela_passa_como_esta`, `test_indexador_avisa_simbolos_sem_traducao`,
  `test_consulta_ignora_uso_privado`, e os esperados de todas as amostras passam agora com os símbolos.
- [ ] **Step 3: Ver falhar**; **Step 4: Implementar**; **Step 5: Ver passar + suíte.**
- [ ] **Step 6: Commit** — `feat: tabelas das fontes de matemática; índice com texto limpo (v5)`

### Task 7: Avaliação do passo 2 e decisão do passo 3

**Files:**
- Docs: os dois relatórios de `docs/avaliacoes/` (seção "B2 · passo 2") e a spec da B2 (nova §9, "Resultado")

- [ ] **Step 1: Rodar** a avaliação nas duas matérias com o limite escolhido e `--gravar`. Expected: acerto da teoria
  ≥ o do passo 1 nas duas.
- [ ] **Step 2: Se cair**, investigar com superpowers:systematic-debugging antes de qualquer decisão; não registrar
  número de um índice errado.
- [ ] **Step 3: Decisão do reordenador** — contar, nas perguntas que erram no top 5, quantas têm a resposta no top 20.
  Maioria → recomendar spec própria do reordenador; senão, listar os erros que sobraram por tipo.
- [ ] **Step 4: Registrar** na spec (§9) a tabela dos dois passos, a decisão e os achados; commit
  `docs: resultado da B2 e decisão sobre o reordenador`.
