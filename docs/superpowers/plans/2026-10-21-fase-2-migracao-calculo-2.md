# Fase 2 — Migração de Cálculo 2: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Levar todo o conteúdo do app legado de Cálculo 2 para o `materia.db` + `conteudo/` + `fontes/` do motor novo, por regras determinísticas, sem perder nada e sem quebrar o app legado, com um relatório que prove que as contagens batem.

**Architecture:** Pacote `estudos.migracao` em três camadas puras + uma de orquestração: `legado.py` lê e valida os arquivos antigos em dataclasses; `conversao.py` tem as conversões de texto (HTML→Markdown, datas curtas, referências a exercícios, nota); `regras.py` decide cada mapeamento ambíguo com uma regra explícita; `executar.py` grava tudo pelos repositórios numa única operação e produz o `Relatorio`. Os arquivos (PDFs, figuras) entram por **hardlink** (cópia como fallback): o legado continua lendo os seus caminhos até o corte (Fase 5).

**Tech Stack:** o mesmo da Fase 1 (Python 3.13, sqlite3, FastAPI, pytest) + GitHub Actions para CI.

**Spec:** `docs/superpowers/specs/2026-10-20-refatoracao-plataforma-design.md` (§3 layout, §5 modelo, §11 Fase 2). A Task 10 emenda a spec com as decisões desta fase.

## Global Constraints

- **O legado é somente leitura.** Nada em `Calculo 2/_app/`, `resumos/`, `resolucoes/`, `exercicios/`, `disciplina/`, `livros/`, `status.json`, `*.md` da raiz da matéria é alterado, movido ou apagado nesta fase.
- **Toda decisão de mapeamento vem de uma regra desta lista ou de um dado explícito do legado.** Sem prefixo de arquivo, sem mapa fixo de seções, sem "chute". O que nenhuma regra resolve vai para o relatório como "não resolvido" (e o dado bruto é preservado numa anotação).
- **Re-executável:** a migração reconstrói `materia.db`, `conteudo/`, `fontes/`, `figuras/` e `.versoes/` do zero a cada execução, preservando o `uid` da matéria. Se o banco tiver ações do usuário (algum grupo no histórico), recusa sem `--forcar`.
- Dados migrados recebem `origem='migrado'`. A gravação acontece numa única `operacao("Migração do app legado")` cujo grupo é apagado no fim (a migração é a linha de base, não uma ação desfazível).
- Identificadores em português, `snake_case`. Testes: `.venv/Scripts/python -m pytest` a partir de `_app/backend`.
- Ano das datas curtas (`dd/mm`) = ano do período da matéria (`2026.2` → 2026).

## Regras de mapeamento (o coração da fase)

| Legado | Novo | Regra |
|---|---|---|
| `curso.subtituloGeral` "UFPE · 2026.2" | `materia.instituicao`, `materia.periodo` | partes separadas por `·`; período = `\d{4}\.\d`; o resto = instituição |
| `curso.unidades[N]` | `unidade(numero=N, titulo=tituloItalico)` | 1:1 |
| `unidades[N].dataProva` | `evento(tipo='prova', data, unidade)` | 1:1, sem hora (o calendário da Fase 3 completa) |
| tag `Nota: 8,0` | `nota_avaliacao(8.0)` | regex `^Nota:\s*(\d+(?:[.,]\d+)?)$`; "Nota ainda não saiu" não casa |
| demais tags, `subtitulo`, `eyebrow`, `ondeEstamosSubtitulo` | anotação `conteudo/anotacoes/legado-unidade-N.md` | preservação sem perda |
| `ondeEstamos` com `status='prova'` | — | já representado pelo evento `prova`; registrado no relatório |
| demais `ondeEstamos` | `topico` | `seen→visto`, `next→proxima`, `later→pendente`; `detalhe_md` = `detalhe`; `lv` que não seja "Visto" vira a linha `Previsto: <lv>` no início de `detalhe_md` |
| `ondeEstamos.where` | `topico_secao` | cada código `\d+\.\d+` que existe como `secao_livro` do livro principal → vínculo `confianca=1, confirmado=1` |
| `ondeEstamos.secoes` | `lista_topico` | cada código que existe como `lista.codigo` → vínculo |
| `curso.livros[i]` | `fonte(tipo='livro')` + `livro` | `papel='principal'` para i=0, `complementar` para os demais; `offset_pagina=offsetPdf`; `gabaritoPdf→gabarito_pdf_ini/fim` |
| `livros[i].secoes[cod]` | `secao_livro` | `nivel = cod.count('.') + 1`; `pagina_pdf_fim = pgFimPdf`, ou início da próxima seção do mesmo livro − 1, ou `pgPdf` |
| `secoes[cod].corresp` "14.1" ou "14.1, 14.2" | `secao_equivalente` | cada código casado com uma seção do livro principal |
| PDFs em `livros/` sem entrada em `curso.livros` | `fonte(tipo='livro')` + `livro(papel='complementar')` sem seções | a Fase 3 detecta o sumário |
| PDF citado em `exercicios.json[].pdf` fora de `livros/` | `fonte(tipo='lista')` + `lista.fonte_id` | referência explícita |
| demais PDFs de `disciplina/` | `fonte(tipo='outro')` em `fontes/documentos/` | a Fase 3 classifica |
| `exercicios.json[]` | `lista(codigo=sec, titulo=nome, unidade=un)` | 1:1 |
| `exercicios.json[].sec` igual a uma seção do livro principal | `lista_secao` | vínculo explícito |
| `locked` | `liberacao` | `'auto'` se a regra automática (spec §5) já dá o mesmo estado que o legado; senão `'travada'` (locked) / `'aberta'` (não locked) — **o estado visível nunca muda** |
| item `[num, pede, expr, img]` em `l1`/`l2` | `questao(rotulo=str(num), linha, enunciado_md, expressao, figura, chave_legada="sec-num")` | mesmo rótulo nas duas linhas (14.7 #33, #35; 14.8 #31) = **uma** questão, `linha=1`; registrado no relatório |
| HTML em `pede` | Markdown | `<b>/<strong>→**`, `<i>/<em>→*`, `<br>→\n`, `palavra<sub>x</sub>→$palavra_{x}$`; tag desconhecida → texto mantido e aviso no relatório |
| `status.json` `"sec-num": estado` | `marcacao` | via `chave_legada`; chave sem questão → relatório |
| fase com ≥ 50% das linhas com `d` no formato data curta | `sessao_estudo` | `codigo=s`, `data` ISO (ou `None` + texto original em `foco_md`), `foco_md = t` (HTML→MD) + `\n\nExercícios: <x unidos por ' · '>`, `feito` |
| referências em `x` com seção explícita (`14.6: 4, 8`, `L5 #1, #2, ⭐#4`) | `sessao_questao` | só referências `(<código>)[:\s]+#?rótulo` que casam com `questao`; o texto continua em `foco_md` |
| demais fases (tabelas "Blocos", "Ordem de corte") | tabela Markdown em `legado-unidade-N.md` | preservação sem perda |
| `formulario[]` | `formula(titulo, corpo_tex=fml, notas_md)` | `notas` vira lista Markdown (`- `) |
| `resumos/*.md` | `documento(tipo='resumo')` em `conteudo/resumos/` | unidade por regra, em ordem: (1) marcador `Nª unidade`/`unidade: N` nos 400 primeiros caracteres; (2) código `\d+\.\d+` ou `L\d+` do H1 que exista em `exercicios.json` (usa o `un` da seção); (3) nenhum → `unidade_id=None` + relatório |
| `curso.resumosExtraUnidade[key]` | `documento_unidade_extra` | 1:1 |
| `resolucoes/<a>-<b>-<rest>.md` | `documento(tipo='resolucao', questao_id)` | chave `a.b-rest` → `questao.chave_legada`; unidade = da lista; sem questão → relatório |
| `curso.documentos[]` (`src` existente) | `documento` | `plano-estudos-*` → `plano`; demais → `anotacao`; `unidades` com 1 item → `unidade_id`; com vários → `unidade_id=None` (vale para todas) |
| `SKILL-DISCIPLINA.md` | `documento(tipo='contexto')` em `conteudo/contexto.md` | conteúdo integral |
| `exercicios/STATUS.md` | — | espelho gerado; não migra |
| `_app/img/*.png` | `figuras/*.png` | hardlink; `questao.figura` = nome do arquivo sem extensão |
| `rag.db`, `.historico_undo.json`, `.historico_telemetria.json`, `.config.json` | — | não migram (o índice é refeito na Fase 4; histórico novo começa vazio; a chave fica onde está até a Fase 6) |

## Review Focus

1. **Rodar a migração duas vezes seguidas** → o mesmo resultado, o mesmo `uid`, nenhum arquivo duplicado em `fontes/`. Teste na Task 8.
2. **Rodar depois de uma ação feita no app novo** (há grupo no histórico) → recusa com mensagem clara; com `forcar=True`, reconstrói. Teste na Task 8.
3. **Hardlink impossível** (outro volume, sistema sem suporte) → cai para cópia e o relatório registra. Teste na Task 7 com `os.link` substituído para falhar.
4. **Texto legado com caracteres especiais** (`∬`, `θ`, `⭐`, `—`, `≤`, acentos) chega intacto ao Markdown e ao banco. Teste na Task 5.
5. **Questão marcada que existe nas duas linhas** (ex.: `14.7-33`) → a marcação vai para a única questão resultante. Teste na Task 8.

---

## Mapa de arquivos

```text
.github/workflows/testes.yml                         # Task 1
_app/backend/estudos/
├── db/migracoes/0003_complementos_migracao.sql      # Task 2
├── repos/topicos.py documentos.py                   # Task 2 (modificados)
├── repos/fontes.py livros.py                        # Task 3
├── api/painel.py                                    # Task 2 (documentos extras da unidade)
├── workspace.py                                     # Task 4 (inicializar_materia)
└── migracao/
    ├── __init__.py  __main__.py                     # Task 9
    ├── legado.py                                    # Task 5
    ├── conversao.py                                 # Task 5
    ├── regras.py                                    # Task 6
    ├── arquivos.py                                  # Task 7
    ├── executar.py                                  # Task 8
    └── relatorio.py                                 # Task 8
_app/backend/tests/
├── fixtures/legado_minimo/ (curso.json, exercicios.json, status.json, resumos/, resolucoes/, disciplina/, livros/, _app/img/)  # Task 5
├── test_migracao_conversao.py  test_migracao_regras.py  test_migracao_arquivos.py  test_migracao_executar.py
└── test_migracao_calculo2_real.py                   # Task 9 (pula se a pasta real não existir)
```

---

### Task 1: CI no GitHub Actions

**Files:**
- Create: `.github/workflows/testes.yml`

**Interfaces:** nenhuma.

- [ ] **Step 1: Criar o workflow** — `on: [push, pull_request]` (push só em `main`); job `testes` em `windows-latest` (o app roda em Windows; caminhos com acento são parte do que se testa), `actions/setup-python@v5` com `python-version: "3.13"`, `working-directory: _app/backend`, `pip install -e ".[dev]"`, `python -m pytest -q`.
- [ ] **Step 2: Verificação** — `python -m pytest -q` local → todos PASS (o workflow em si é verificado no PR).
- [ ] **Step 3: Commit** — `ci: roda a suíte do backend em cada PR`

---

### Task 2: Complementos de schema para a migração

**Files:**
- Create: `_app/backend/estudos/db/migracoes/0003_complementos_migracao.sql`, `_app/backend/tests/test_schema_0003.py`
- Modify: `estudos/repos/topicos.py`, `estudos/repos/documentos.py`, `estudos/modelos.py`, `estudos/api/painel.py`, `estudos/repos/_base.py` (`TABELAS_PERMITIDAS`)

**Interfaces:**
- Produces:
  - SQL: `ALTER TABLE topico ADD COLUMN detalhe_md TEXT NOT NULL DEFAULT ''`;
    `CREATE TABLE documento_unidade_extra (documento_id REFERENCES documento ON DELETE CASCADE, unidade_id REFERENCES unidade ON DELETE CASCADE, PRIMARY KEY (documento_id, unidade_id))`;
    `CREATE TABLE secao_equivalente (secao_id REFERENCES secao_livro ON DELETE CASCADE, equivalente_id REFERENCES secao_livro ON DELETE CASCADE, PRIMARY KEY (secao_id, equivalente_id), CHECK (secao_id <> equivalente_id))`.
  - `Topico` ganha `detalhe_md: str`; `topicos.criar(op, unidade_id, titulo, pai_id=None, ordem=None, origem="manual", detalhe_md="") -> int`.
  - `documentos.adicionar_unidade_extra(op, documento_id: int, unidade_id: int) -> None`;
    `documentos.listar(con, tipo=None, unidade_id=None)` passa a devolver, quando `unidade_id` é dado, os documentos com `unidade_id = u` **ou** com extra `u` **ou** com `unidade_id IS NULL` (globais), nessa ordem de caminho.
  - `TABELAS_PERMITIDAS` inclui `documento_unidade_extra` e `secao_equivalente`.

- [ ] **Step 1: Testes** — `test_topico_detalhe_md_persiste`; `test_documento_extra_aparece_na_outra_unidade` (resumo da U1 com extra U3 → `listar(unidade_id=u3)` contém ele); `test_documento_global_aparece_em_todas`; `test_secao_equivalente_nao_aceita_ela_mesma` (IntegrityError); `test_desfazer_remove_extra` (via histórico).
- [ ] **Step 2: Rodar** → FAIL. **Step 3: Implementar.** **Step 4: Rodar** → PASS, suíte inteira verde.
- [ ] **Step 5: Commit** — `feat(backend): complementos de schema para a migração`

---

### Task 3: Repositórios de fontes e livros

**Files:**
- Create: `estudos/repos/fontes.py`, `estudos/repos/livros.py`, `tests/test_repos_fontes_livros.py`
- Modify: `estudos/modelos.py`

**Interfaces:**
- Produces:
  ```python
  TIPOS_FONTE = ("programa", "calendario", "turma", "livro", "lista", "slides", "prova", "anotacao", "outro")
  PAPEIS_LIVRO = ("principal", "complementar")
  Fonte(id, tipo, caminho, sha256, titulo, paginas, importada_em, origem)
  Livro(fonte_id, papel, autor, titulo_obra, edicao, offset_pagina, gabarito_pdf_ini, gabarito_pdf_fim)
  SecaoLivro(id, livro_id, codigo, titulo, nivel, pagina_pdf_ini, pagina_pdf_fim, origem, confianca)

  # repos/fontes.py
  def sha256_arquivo(caminho: Path) -> str                      # leitura em blocos de 1 MiB
  def registrar(op, tipo: str, caminho_rel: str, titulo: str = "", paginas: int | None = None,
                origem: str = "manual") -> int                   # exige op.raiz; calcula sha256; sha repetido → DadoInvalido citando a fonte existente
  def obter_por_caminho(con, caminho_rel: str) -> Fonte | None
  def listar(con, tipo: str | None = None) -> list[Fonte]
  # repos/livros.py
  def criar(op, fonte_id: int, papel: str, autor: str = "", titulo_obra: str = "", edicao: str = "",
            offset_pagina: int = 0, gabarito_pdf_ini: int | None = None, gabarito_pdf_fim: int | None = None) -> None
  def principal(con) -> Livro | None
  def criar_secao(op, livro_id: int, codigo: str, titulo: str, pagina_pdf_ini: int, pagina_pdf_fim: int,
                  nivel: int | None = None, origem: str = "manual", confianca: float | None = None) -> int
      # nivel None → codigo.count('.') + 1; fim < ini → DadoInvalido
  def secao_por_codigo(con, livro_id: int, codigo: str) -> SecaoLivro | None
  def listar_secoes(con, livro_id: int) -> list[SecaoLivro]     # ordem por pagina_pdf_ini
  def vincular_equivalente(op, secao_id: int, equivalente_id: int) -> None   # grava os dois sentidos
  def vincular_topico(op, topico_id: int, secao_id: int, confianca: float | None = None, confirmado: bool = False) -> None
  ```

- [ ] **Step 1: Testes** — `test_registrar_fonte_calcula_sha` (arquivo de 3 bytes, sha conhecido); `test_fonte_duplicada` (mesmo conteúdo em outro caminho → DadoInvalido); `test_livro_principal`; `test_secao_nivel_automatico` ("15.4"→2, "8"→1); `test_secao_fim_antes_do_inicio`; `test_equivalencia_nos_dois_sentidos`; `test_vinculo_topico_secao_abre_lista_auto` (integra com a regra de `listas.SQL_ABERTA`).
- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): repositórios de fontes e livros`

---

### Task 4: Inicializar matéria numa pasta existente

**Files:**
- Modify: `estudos/workspace.py`, `tests/test_workspace.py`

**Interfaces:**
- Produces: `def inicializar_materia(pasta: Path, nome: str, periodo: str | None = None, uid: str | None = None) -> MateriaRef` — cria `SUBPASTAS` que faltarem (sem tocar no resto da pasta), aplica migrações, insere a linha `materia` (uid informado ou novo). Banco já existente → `DadoInvalido`. `criar_materia` passa a validar o nome, recusar pasta existente e delegar a `inicializar_materia`.

- [ ] **Step 1: Testes** — `test_inicializar_em_pasta_com_conteudo_legado` (pasta com `resumos/x.md` → continua lá, `materia.db` criado, descoberta acha); `test_inicializar_com_uid_informado`; `test_inicializar_duas_vezes` (DadoInvalido).
- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): inicializar matéria em pasta existente`

---

### Task 5: Leitura do legado e conversões de texto

**Files:**
- Create: `estudos/migracao/__init__.py`, `estudos/migracao/legado.py`, `estudos/migracao/conversao.py`, `tests/fixtures/legado_minimo/…`, `tests/test_migracao_conversao.py`, `tests/test_migracao_legado.py`

**Interfaces:**
- Produces:
  ```python
  # legado.py — espelho tipado dos arquivos antigos; nenhuma regra de negócio aqui
  @dataclass(frozen=True) class ItemLegado: numero: str; pede: str; expressao: str | None; figura: str | None; linha: int
  @dataclass(frozen=True) class SecaoLegado: sec: str; un: int; nome: str; pdf: str | None; locked: bool; itens: tuple[ItemLegado, ...]
  @dataclass(frozen=True) class Legado:
      pasta: Path
      curso: dict            # curso.json validado (chaves usadas presentes)
      secoes: tuple[SecaoLegado, ...]
      marcacoes: dict[str, str]
      resumos: tuple[Path, ...]       # resumos/*.md ordenados
      resolucoes: tuple[Path, ...]    # resolucoes/*.md ordenados
      pdfs: tuple[Path, ...]          # disciplina/**/*.pdf e livros/*.pdf, relativos à pasta
      figuras: tuple[Path, ...]       # _app/img/*.png
  class LegadoInvalido(ValueError): ...
  def carregar(pasta: Path) -> Legado    # JSON inválido ou chave obrigatória ausente → LegadoInvalido com arquivo e chave

  # conversao.py — funções puras
  def html_para_md(texto: str) -> tuple[str, list[str]]       # (markdown, avisos de tags desconhecidas)
  def data_curta_para_iso(texto: str, ano: int) -> str | None # "sáb 05/09" → "2026-09-05"; "Bloco 1" → None
  def referencias_exercicios(texto: str) -> list[tuple[str, str]]
      # "14.6: 4, 8, 12" → [("14.6","4"),("14.6","8"),("14.6","12")]; "L5 #1, #2, ⭐#4" → [("L5","1"),("L5","2"),("L5","4")];
      # "68 (pendente) + 20, 26" → [] (sem código de seção); "6(a)" preservado como rótulo
  def nota_de_tags(tags: list[str]) -> float | None           # "Nota: 8,0" → 8.0
  def periodo_e_instituicao(subtitulo: str) -> tuple[str | None, str | None]   # "UFPE · 2026.2" → ("2026.2", "UFPE")
  def tabela_markdown(colunas: list[str], linhas: list[list[str]]) -> str
  ```
  Fixture `legado_minimo`: 2 unidades, 1 livro (2 seções, uma com `corresp`), 3 seções de exercício (uma `L1` com pdf de lista, uma com rótulo repetido nas duas linhas, uma travada), 4 marcações (uma na questão repetida, uma com chave órfã), 3 resumos (com marcador, com seção no H1, sem nada), 2 resoluções (uma órfã), 1 documento de config com 1 unidade e 1 com várias, 1 figura, PDFs falsos (bytes distintos) e uma fase "Ordem de corte".

- [ ] **Step 1: Testes** — conversões com os textos reais: `html_para_md("Máximo <b>absolutos</b> em <b>D = {(x, y) : x² + y² ≤ 1}</b>")`, `"f<sub>xy</sub> = f<sub>yx</sub>"` → `"$f_{xy}$ = $f_{yx}$"`, `"<i>Dica</i>"`, tag `<span>` → aviso; datas `"seg 31/08"`, `"Qua 04/11"`, `"06 e 11/11"` → `None` (duas datas não são uma); referências dos exemplos acima e `"15.4: 11, 29 | L5 #6(a), #7"`; `nota_de_tags(["Nota ainda não saiu"]) is None`; caracteres `∬ θ ⭐ — ≤` intactos (Review Focus 4). Legado: `carregar(fixture)` devolve 3 seções e 4 marcações; `curso.json` sem `unidades` → `LegadoInvalido` citando a chave.
- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(migracao): leitura tipada do legado e conversões de texto`

---

### Task 6: Regras de decisão

**Files:**
- Create: `estudos/migracao/regras.py`, `tests/test_migracao_regras.py`

**Interfaces:**
- Consumes: `Legado`, `SecaoLegado` (Task 5).
- Produces:
  ```python
  @dataclass(frozen=True) class Decisao: valor: object; regra: str     # regra = texto curto citado no relatório
  def mapa_secao_unidade(legado: Legado) -> dict[str, int]              # só de exercicios.json (sec → un)
  def unidade_do_resumo(texto: str, mapa: dict[str, int]) -> Decisao     # valor int | None; regras (1)(2)(3) da tabela
  def status_topico(status_legado: str) -> str | None                   # 'prova' → None
  def fase_eh_cronograma(fase: dict, ano: int) -> bool                  # ≥ 50% das linhas com data curta válida
  def liberacao(locked: bool, aberta_pela_regra_auto: bool) -> str      # 'auto' | 'aberta' | 'travada'
  def unificar_itens(secao: SecaoLegado) -> tuple[list[ItemLegado], list[str]]   # remove rótulo repetido (fica a linha 1); avisos
  def tipo_documento_config(src: str) -> str                            # 'plano' se o nome começa com 'plano-estudos-', senão 'anotacao'
  ```

- [ ] **Step 1: Testes** — `unidade_do_resumo` para os 12 cabeçalhos reais (copiados como string no teste: "# 14.1 Funções…", "> Stewart 10.3 e 10.4 · pré-requisito da 1ª unidade", "# 15.4 …\n\n> Referência · 3ª unidade …") com o mapa real (14.x→1/2, 15.x→2/3) e um sem nada → `None` com regra "sem marcador nem seção conhecida"; `liberacao` nas 4 combinações; `fase_eh_cronograma` nas 3 fases reais da U3; `unificar_itens` da 14.7 (33 e 35 viram linha 1, 2 avisos).
- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(migracao): regras explícitas de mapeamento`

---

### Task 7: Arquivos — hardlink com fallback e destino por tipo

**Files:**
- Create: `estudos/migracao/arquivos.py`, `tests/test_migracao_arquivos.py`

**Interfaces:**
- Produces:
  ```python
  PASTA_FONTE_POR_TIPO = {"livro": "fontes/livros", "lista": "fontes/listas", "outro": "fontes/documentos"}
  def vincular_arquivo(origem: Path, destino: Path) -> str   # 'hardlink' | 'copia' | 'existente' (mesmo sha256 já no destino)
      # cria pastas; nunca sobrescreve destino com conteúdo diferente → DadoInvalido
  ```

- [ ] **Step 1: Testes** — `test_hardlink_mesmo_inode` (`os.stat(a).st_ino == os.stat(b).st_ino` quando suportado; senão `pytest.skip`); `test_fallback_copia` (monkeypatch `os.link` levantando `OSError` → `'copia'`, conteúdo igual — Review Focus 3); `test_existente_igual`; `test_destino_diferente_recusa`.
- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(migracao): vínculo de arquivos por hardlink com fallback`

---

### Task 8: Orquestração e relatório

**Files:**
- Create: `estudos/migracao/executar.py`, `estudos/migracao/relatorio.py`, `tests/test_migracao_executar.py`

**Interfaces:**
- Consumes: Tasks 2–7 e os repositórios da Fase 1.
- Produces:
  ```python
  # relatorio.py
  @dataclass
  class Relatorio:
      contagens: dict[str, tuple[int, int]]     # chave → (legado, novo): unidades, topicos, livros, secoes_livro, listas,
                                                # questoes, marcacoes, sessoes, formulas, resumos, resolucoes, documentos, figuras, fontes
      decisoes: list[str]                       # uma linha por decisão não trivial (regra aplicada)
      nao_resolvidos: list[str]                 # o que nenhuma regra resolveu
      avisos: list[str]
      arquivos: dict[str, int]                  # {'hardlink': n, 'copia': n, 'existente': n}
      def bate(self) -> bool                    # toda contagem legado == novo, descontadas as diferenças explicadas em `decisoes`
      def markdown(self) -> str
  # executar.py
  class MigracaoRecusada(RuntimeError): ...
  def migrar(origem: Path, destino: Path, forcar: bool = False) -> Relatorio
      # origem = pasta legada (somente leitura); destino = pasta da matéria no workspace (pode ser a mesma)
      # 1. carrega o legado; 2. se destino/materia.db existe: lê uid; histórico não vazio e não forcar → MigracaoRecusada;
      #    apaga materia.db(+wal/shm), conteudo/, fontes/, figuras/, .versoes/; 3. inicializar_materia(uid preservado);
      # 4. numa operacao: matéria → unidades/eventos/nota → livros/seções/equivalências → fontes → listas/questões/vínculos
      #    → marcações → tópicos/vínculos → sessões → fórmulas → documentos/extras/contexto → anotações legado-unidade-N;
      # 5. apaga o grupo de histórico da migração; 6. grava destino/.migracao/relatorio.md e devolve o Relatorio
  ```
  Diferenças esperadas e explicadas: `questoes` (legado conta itens; rótulos repetidos unificados) e `topicos` (itens `prova` viram evento).

- [ ] **Step 1: Testes** (sobre `fixtures/legado_minimo` copiada para `tmp_path`):
  ```python
  def test_contagens_batem(tmp_path): r = migrar(origem, destino); assert r.bate()
  def test_marcacao_da_questao_repetida(tmp_path): ...      # Review Focus 5
  def test_estado_das_listas_preservado(tmp_path): ...      # aberta/travada iguais ao legado para cada seção
  def test_resumo_sem_regra_fica_sem_unidade_e_no_relatorio(tmp_path): ...
  def test_resolucao_orfa_no_relatorio(tmp_path): ...
  def test_legado_intocado(tmp_path): ...                   # hash de todos os arquivos da origem antes == depois
  def test_reexecucao_idempotente(tmp_path): ...            # 2 execuções: mesmo uid, mesmas contagens, fontes sem duplicatas (Review Focus 1)
  def test_recusa_com_historico(tmp_path): ...              # ação via repos após migrar → MigracaoRecusada; forcar=True reconstrói (Review Focus 2)
  def test_historico_vazio_apos_migrar(tmp_path): ...
  def test_relatorio_gravado(tmp_path): ...                 # destino/.migracao/relatorio.md existe e cita as decisões
  ```
- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(migracao): orquestração e relatório da migração`

---

### Task 9: CLI e migração real de Cálculo 2

**Files:**
- Create: `estudos/migracao/__main__.py`, `tests/test_migracao_calculo2_real.py`
- Modify: `.gitignore` (`.migracao/` **não** é ignorada: o relatório fica versionado junto dos dados)

**Interfaces:**
- Produces: `python -m estudos.migracao "<pasta legada>" [--destino <pasta>] [--forcar]` → imprime `relatorio.markdown()`; código de saída 0 se `bate()`, 1 se não, 2 se recusada.
- Teste real (pula se `Calculo 2/_app/dados/curso.json` não existir): migra a pasta real para `tmp_path/"Calculo 2"` e verifica, **calculando o esperado a partir dos próprios arquivos legados** (não números fixos no teste): `r.bate()`, 3 unidades, nota 8.0 na U1, 12 marcações migradas, 21 resoluções todas com `questao_id`, 12 resumos com unidade definida, L5 aberta e 15.4 travada (estado atual do legado).

- [ ] **Step 1: Teste real** → FAIL (módulo inexistente).
- [ ] **Step 2: Implementar o CLI** → teste PASS.
- [ ] **Step 3: Rodar de verdade** — `python -m estudos.migracao "../../Calculo 2"` → saída 0; ler `Calculo 2/.migracao/relatorio.md` inteiro e conferir cada "decisão" e "não resolvido".
- [ ] **Step 4: Verificação manual** — subir o motor novo (`_app/abrir-novo.bat`) e o legado (`abrir.bat`) juntos; `GET /api/materias` lista "Cálculo 2"; `GET /api/materias/{uid}/painel?unidade=3` traz as listas L5/L6 e 15.x com os mesmos estados de trava do legado; `?unidade=1` traz as 12 marcações (todas de 14.1 e 14.2); o legado continua abrindo e marcando normalmente.
- [ ] **Step 5: Commit** — `feat(migracao): CLI e migração inicial de Cálculo 2` (inclui `Calculo 2/materia.db`, `conteudo/`, `fontes/`, `figuras/`, `.migracao/relatorio.md`)

---

### Task 10: Emendas na spec e no README

**Files:**
- Modify: `docs/superpowers/specs/2026-10-20-refatoracao-plataforma-design.md`, `README.md`

- [ ] **Step 1: Spec** — §3: até o corte (Fase 5) matéria nova e pastas legadas convivem na mesma pasta; arquivos entram por hardlink; `legado/` só no corte. §5: `topico.detalhe_md`, `documento_unidade_extra`, `secao_equivalente`. §11 Fase 2: critério de pronto = `relatorio.bate()` + teste real verde; "legado congelado" passa para a Fase 5.
- [ ] **Step 2: README** — seção "Migrar de novo antes do corte": `python -m estudos.migracao "Calculo 2"` (reconstrói a partir do legado; recusa se houver ações feitas no app novo).
- [ ] **Step 3: Suíte completa** → todos PASS. **Step 4: Commit** — `docs: emendas da Fase 2 na spec e no README`

---

## Pronto quando

- Suíte verde localmente e no GitHub Actions.
- `Calculo 2/.migracao/relatorio.md` com `bate() == True` e lista de "não resolvidos" lida e aceita por você.
- Legado intacto (teste `test_legado_intocado` + uso real) e motor novo mostrando os mesmos dados.
