# Fase 1 — Fundação do Backend: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o novo motor em `_app/backend` (config, segurança, workspace multi-matéria, SQLite com migrações, repositórios com histórico/desfazer e API FastAPI básica), rodando ao lado do app legado sem tocá-lo.

**Architecture:** Pacote Python `estudos` em camadas: `api → repos → db`. Cada matéria é uma pasta do workspace com `materia.db`; toda escrita passa por `historico.operacao()`, que abre uma transação e registra antes/depois de cada linha ou arquivo para desfazer. A API identifica a matéria por `uid` e aceita só requisições locais.

**Tech Stack:** Python 3.13, FastAPI ≥0.115, Pydantic ≥2.9, Uvicorn ≥0.32, sqlite3 (stdlib, FTS5), pytest ≥8.3, httpx ≥0.27.

**Spec:** `docs/superpowers/specs/2026-10-20-refatoracao-plataforma-design.md` (§3, §4, §5, §7, §9 são os relevantes nesta fase).

## Global Constraints

- Python `>=3.13`; dependências só as listadas no `pyproject.toml` da Task 1.
- Identificadores em português, `snake_case` (funções, módulos, colunas), como o código atual.
- Nenhum valor específico de disciplina no código (sem códigos de seção, nomes de livros, número fixo de unidades).
- Defaults de configuração existem em **um** lugar: `estudos/config.py` (`Settings`). Porta padrão do novo servidor: `8790` (o legado usa `8780`).
- Workspace padrão = pasta-pai de `_app/` (`Refatoração Site Estudos/`). Matéria = subpasta que contém `materia.db`.
- O app legado (`Calculo 2/_app/`) **não é alterado** nesta fase.
- Todos os comandos rodam a partir de `_app/backend/` com o venv: `.venv/Scripts/python -m pytest …` (Windows).
- Toda escrita de domínio acontece dentro de `historico.operacao(...)`; nenhum repo faz `commit` por conta própria.

## Review Focus

1. **Nome de pasta com acentos/espaços** ("Cálculo 2", "Física 1") → criar e descobrir funcionam; caracteres proibidos no Windows (`<>:"/\|?*`) e nomes reservados (`CON`, `NUL`) → `ValueError` claro. Teste na Task 5.
2. **Duas escritas simultâneas** (duas conexões, threads) → ambas concluem graças a `busy_timeout`; nenhuma `database is locked`. Teste na Task 3.
3. **Reimportar lista removendo uma questão marcada e depois desfazer** → questão e marcação voltam. Teste na Task 8.
4. **POST vindo de outra origem ou com `Content-Type: text/plain`** → 403. Teste na Task 2.
5. **Caminhos maliciosos**: `../Calculo 2 - backup/x`, absoluto `C:\x`, `\\servidor\x`, `..\\x` → `CaminhoInvalido`. Teste na Task 2.

---

## Mapa de arquivos

```text
_app/
├── config.toml                         # Task 1
├── abrir-novo.bat                      # Task 12
└── backend/
    ├── pyproject.toml                  # Task 1
    ├── estudos/
    │   ├── __init__.py                 # Task 1
    │   ├── config.py                   # Task 1
    │   ├── seguranca.py                # Task 2
    │   ├── erros.py                    # Task 3  (NaoEncontrado, DadoInvalido)
    │   ├── db/conexao.py               # Task 3
    │   ├── db/migracoes/0001_inicial.sql  # Task 4
    │   ├── workspace.py                # Task 5
    │   ├── historico.py                # Task 6
    │   ├── repos/_base.py              # Task 6
    │   ├── repos/materia.py unidades.py eventos.py topicos.py   # Task 7
    │   ├── repos/listas.py marcacoes.py                         # Task 8
    │   ├── conteudo.py                                          # Task 9
    │   ├── repos/cronograma.py formulas.py documentos.py        # Task 9
    │   ├── modelos.py                  # Tasks 7–9 (dataclasses de leitura) e 10 (Pydantic de API)
    │   ├── main.py                     # Task 10
    │   └── api/deps.py materias.py painel.py marcacoes.py historico.py   # Task 10
    │       api/unidades.py topicos.py listas.py cronograma.py formulas.py documentos.py  # Task 11
    └── tests/ (um test_<modulo>.py por módulo + conftest.py)
```

---

### Task 1: Esqueleto do pacote e configuração

**Files:**
- Create: `_app/backend/pyproject.toml`, `_app/backend/estudos/__init__.py`, `_app/backend/estudos/config.py`, `_app/config.toml`, `_app/backend/tests/conftest.py`, `_app/backend/tests/test_config.py`
- Modify: `.gitignore` (adicionar `_app/backend/.venv/` e `*.egg-info/`; WAL/SHM já estão ignorados; `.versoes/` **continua versionado**, porque são dados do usuário)

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Settings:
      workspace: Path
      app_dir: Path
      host: str = "127.0.0.1"
      porta: int = 8790
      limiar_confianca: float = 0.75
      limiar_vinculo: float = 0.35
      historico_max_grupos: int = 500
  def carregar_settings(app_dir: Path, workspace: Path | None = None) -> Settings
  ```
  `config.toml` (lido com `tomllib`): `[servidor] host, porta`; `[importacao] limiar_confianca, limiar_vinculo`; `[historico] max_grupos`. Chave ausente → default do dataclass. `workspace=None` → `app_dir.parent`.

- [ ] **Step 1: Criar venv e `pyproject.toml`**

  `pyproject.toml`: `name="estudos"`, `requires-python=">=3.13"`, dependencies `fastapi>=0.115`, `uvicorn[standard]>=0.32`, `pydantic>=2.9`; optional `dev = ["pytest>=8.3", "httpx>=0.27"]`; `[tool.pytest.ini_options] testpaths=["tests"]`.

  Run: `py -3.13 -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"`
  Expected: instalação sem erro.

- [ ] **Step 2: Escrever os testes**

  ```python
  def test_defaults_sem_arquivo(tmp_path):
      s = carregar_settings(tmp_path / "_app")
      assert s.porta == 8790 and s.host == "127.0.0.1"
      assert s.workspace == tmp_path

  def test_config_toml_sobrescreve(tmp_path):
      app = tmp_path / "_app"; app.mkdir()
      (app / "config.toml").write_text("[servidor]\nporta = 9001\n[historico]\nmax_grupos = 10\n", encoding="utf-8")
      s = carregar_settings(app)
      assert s.porta == 9001 and s.historico_max_grupos == 10 and s.limiar_vinculo == 0.35

  def test_workspace_explicito(tmp_path):
      assert carregar_settings(tmp_path / "_app", tmp_path / "ws").workspace == tmp_path / "ws"
  ```

- [ ] **Step 3: Rodar e ver falhar** — `.venv/Scripts/python -m pytest tests/test_config.py -v` → FAIL (`ModuleNotFoundError`).
- [ ] **Step 4: Implementar `carregar_settings` em `estudos/config.py`** e criar `_app/config.toml` com os valores padrão comentados.
- [ ] **Step 5: Rodar** → PASS.
- [ ] **Step 6: Commit** — `git commit -m "feat(backend): esqueleto do pacote estudos e configuração"`

---

### Task 2: Segurança — caminhos e origem local

**Files:**
- Create: `_app/backend/estudos/seguranca.py`, `_app/backend/tests/test_seguranca.py`

**Interfaces:**
- Produces:
  ```python
  class CaminhoInvalido(ValueError): ...
  def caminho_seguro(base: Path, relativo: str) -> Path   # resolve e exige is_relative_to(base.resolve())
  class OrigemLocalMiddleware:                              # ASGI puro
      def __init__(self, app, porta: int) -> None
  ```
  Regras do middleware (só `http`): (1) hostname do `Host` ∈ {`127.0.0.1`, `localhost`} senão 403; (2) métodos `POST/PUT/PATCH/DELETE`: se houver `Origin`, deve ser `http://127.0.0.1:{porta}` ou `http://localhost:{porta}` senão 403; `Content-Type` deve começar com `application/json` ou `multipart/form-data` senão 403 (exceto corpo vazio). Resposta 403: `{"erro": "requisição não permitida"}`.

- [ ] **Step 1: Escrever os testes**

  ```python
  @pytest.mark.parametrize("rel", ["../Calculo 2 - backup/x.pdf", "..\\x", "C:\\Windows\\x", "\\\\srv\\x", "/etc/passwd", "a/../../b"])
  def test_caminho_seguro_rejeita(tmp_path, rel):
      base = tmp_path / "Calculo 2"; base.mkdir()
      with pytest.raises(CaminhoInvalido):
          caminho_seguro(base, rel)

  def test_caminho_seguro_aceita_subpasta(tmp_path):
      assert caminho_seguro(tmp_path, "fontes/livros/a b.pdf") == (tmp_path / "fontes/livros/a b.pdf").resolve()

  # app mínimo FastAPI com GET/POST "/x" envolto no middleware, porta=8790, TestClient(base_url="http://127.0.0.1:8790")
  def test_post_origem_estrangeira_bloqueado(cliente):
      r = cliente.post("/x", json={}, headers={"Origin": "https://malicioso.com"})
      assert r.status_code == 403
  def test_post_text_plain_bloqueado(cliente):
      assert cliente.post("/x", content=b"{}", headers={"Content-Type": "text/plain"}).status_code == 403
  def test_host_estrangeiro_bloqueado(cliente):
      assert cliente.get("/x", headers={"Host": "evil.com"}).status_code == 403
  def test_post_local_json_permitido(cliente):
      assert cliente.post("/x", json={}, headers={"Origin": "http://127.0.0.1:8790"}).status_code == 200
  ```

- [ ] **Step 2: Rodar** → FAIL.
- [ ] **Step 3: Implementar** `caminho_seguro` (rejeitar antes de resolver: `PureWindowsPath(rel).is_absolute()`, `drive`, prefixo `\\`) e `OrigemLocalMiddleware`.
- [ ] **Step 4: Rodar** → PASS.
- [ ] **Step 5: Commit** — `feat(backend): validação de caminhos e middleware de origem local`

---

### Task 3: Conexão SQLite, transações e runner de migrações

**Files:**
- Create: `_app/backend/estudos/erros.py`, `_app/backend/estudos/db/__init__.py`, `_app/backend/estudos/db/conexao.py`, `_app/backend/estudos/db/migracoes/` (vazia por enquanto, com `0000_teste.sql` só nos testes via `tmp_path`), `_app/backend/tests/test_conexao.py`

**Interfaces:**
- Produces:
  ```python
  # erros.py
  class NaoEncontrado(LookupError): ...
  class DadoInvalido(ValueError): ...
  # db/conexao.py
  PASTA_MIGRACOES: Path
  def conectar(caminho: Path) -> sqlite3.Connection
      # isolation_level=None, row_factory=sqlite3.Row, check_same_thread=False,
      # PRAGMA foreign_keys=ON, journal_mode=WAL, busy_timeout=5000
  @contextmanager
  def transacao(con: sqlite3.Connection) -> Iterator[sqlite3.Connection]
      # fora de transação: BEGIN IMMEDIATE/COMMIT/ROLLBACK; já dentro (con.in_transaction): SAVEPOINT
  def aplicar_migracoes(con: sqlite3.Connection, pasta: Path = PASTA_MIGRACOES) -> int
      # arquivos NNNN_nome.sql em ordem; cada um em transação; grava schema_versao; retorna versão final
  ```

- [ ] **Step 1: Escrever os testes**

  ```python
  def test_pragmas(tmp_path):
      con = conectar(tmp_path / "m.db")
      assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
      assert con.execute("PRAGMA journal_mode").fetchone()[0] == "wal"

  def test_transacao_rollback(tmp_path):
      con = conectar(tmp_path / "m.db"); con.execute("CREATE TABLE t(x)")
      with pytest.raises(RuntimeError):
          with transacao(con):
              con.execute("INSERT INTO t VALUES (1)"); raise RuntimeError
      assert con.execute("SELECT count(*) FROM t").fetchone()[0] == 0

  def test_transacao_aninhada_savepoint(tmp_path): ...  # interna falha, externa confirma; só a linha externa persiste

  def test_migracoes_em_ordem_e_idempotentes(tmp_path):
      pasta = tmp_path / "mig"; pasta.mkdir()
      (pasta / "0001_a.sql").write_text("CREATE TABLE a(x);"); (pasta / "0002_b.sql").write_text("CREATE TABLE b(x);")
      con = conectar(tmp_path / "m.db")
      assert aplicar_migracoes(con, pasta) == 2
      assert aplicar_migracoes(con, pasta) == 2   # segunda vez não reaplica

  def test_escritas_concorrentes(tmp_path):
      # cria tabela; 2 threads, cada uma com sua conexão, 50 INSERTs em transacao() cada → count == 100, sem exceção
  ```

- [ ] **Step 2: Rodar** → FAIL.
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Rodar** → PASS.
- [ ] **Step 5: Commit** — `feat(backend): conexão sqlite, transações e migrações`

---

### Task 4: Schema inicial (migração 0001)

**Files:**
- Create: `_app/backend/estudos/db/migracoes/0001_inicial.sql`, `_app/backend/tests/test_schema.py`

**Interfaces:**
- Produces: todas as tabelas da spec §5, exatamente com os nomes de colunas de lá, **exceto** `chunk`/`chunk_fts`/`importacao` (Fases 3–4 criam em migrações próprias). Restrições obrigatórias:
  - `CHECK` em todo campo enumerado (`origem`, `evento.tipo`, `topico.status`, `fonte.tipo`, `livro.papel`, `lista.liberacao`, `questao.linha IN (1,2)`, `marcacao.estado`, `documento.tipo`).
  - `UNIQUE`: `unidade.numero`, `fonte.sha256`, `secao_livro(livro_id, codigo)`, `questao(lista_id, rotulo)`, `documento.caminho`, `materia.uid`.
  - FKs com `ON DELETE CASCADE` em: `topico.unidade_id`, `topico.pai_id`, `questao.lista_id`, `marcacao.questao_id`, `lista_topico`, `lista_secao`, `topico_secao`, `sessao_questao`, `historico_mudanca.grupo_id`, `secao_livro.livro_id`. `ON DELETE SET NULL` em `evento.unidade_id`, `documento.unidade_id/secao_id/questao_id`, `formula.secao_id`. `lista.unidade_id` e `sessao_estudo.unidade_id`, `formula.unidade_id`: `RESTRICT` (não se apaga unidade com conteúdo sem decidir para onde vai).
  - Índices: `questao(lista_id)`, `topico(unidade_id)`, `evento(unidade_id, tipo)`, `historico_mudanca(grupo_id)`.

- [ ] **Step 1: Escrever os testes**

  ```python
  TABELAS = {"materia","unidade","evento","horario_aula","topico","fonte","livro","secao_livro","topico_secao",
             "lista","lista_secao","lista_topico","questao","marcacao","sessao_estudo","sessao_questao","formula",
             "documento","nota_avaliacao","criterio_correcao","historico_grupo","historico_mudanca","schema_versao"}

  def test_tabelas_existem(con_vazia):   # fixture: conectar + aplicar_migracoes
      nomes = {r[0] for r in con_vazia.execute("SELECT name FROM sqlite_master WHERE type='table'")}
      assert TABELAS <= nomes

  def test_check_estado_marcacao(con_vazia): # inserir unidade, lista, questão; marcacao estado='talvez' → sqlite3.IntegrityError
  def test_cascade_lista_apaga_questoes_e_marcacoes(con_vazia): ...
  def test_restrict_unidade_com_lista(con_vazia): # DELETE unidade com lista → IntegrityError
  def test_unique_rotulo_por_lista(con_vazia): ...
  ```

- [ ] **Step 2: Rodar** → FAIL. **Step 3: Escrever o SQL.** **Step 4: Rodar** → PASS.
- [ ] **Step 5: Commit** — `feat(backend): schema inicial do banco da matéria`

---

### Task 5: Workspace — descobrir, criar e abrir matérias

**Files:**
- Create: `_app/backend/estudos/workspace.py`, `_app/backend/tests/test_workspace.py`

**Interfaces:**
- Consumes: `conectar`, `aplicar_migracoes`, `transacao` (Task 3).
- Produces:
  ```python
  ARQUIVO_DB = "materia.db"
  SUBPASTAS: tuple[str, ...]   # exatamente as pastas da spec §3 (fontes/*, conteudo/*, figuras, .versoes)
  @dataclass(frozen=True)
  class MateriaRef:
      uid: str; nome: str; pasta: Path
      @property
      def db(self) -> Path
  def nome_pasta_valido(nome: str) -> str          # strip; rejeita vazio, <>:"/\|?*, nomes reservados Windows, terminar em "." ou " "
  def descobrir_materias(workspace: Path) -> list[MateriaRef]   # ignora pastas iniciadas por "_" ou "."; ordena por nome
  def criar_materia(workspace: Path, nome: str, periodo: str | None = None) -> MateriaRef
      # pasta já existente → DadoInvalido; cria SUBPASTAS, aplica migrações, insere linha materia (uid=uuid4().hex)
  def abrir_materia(workspace: Path, uid: str) -> MateriaRef     # NaoEncontrado se não existir
  ```
  Ao descobrir, aplicar migrações pendentes em cada `materia.db` (o banco sempre fica na versão do código).

- [ ] **Step 1: Escrever os testes**

  ```python
  def test_criar_e_descobrir_com_acentos(tmp_path):
      ref = criar_materia(tmp_path, "Cálculo 2", "2026.2")
      assert (tmp_path / "Cálculo 2" / "materia.db").exists()
      assert all((tmp_path / "Cálculo 2" / p).is_dir() for p in SUBPASTAS)
      assert [m.uid for m in descobrir_materias(tmp_path)] == [ref.uid]

  @pytest.mark.parametrize("nome", ["", "  ", "a/b", "CON", "nul", "x:y", "fim."])
  def test_nome_invalido(nome):
      with pytest.raises(DadoInvalido):
          nome_pasta_valido(nome)

  def test_ignora_pastas_sem_db_e_com_underscore(tmp_path):
      (tmp_path / "_app").mkdir(); (tmp_path / "solta").mkdir(); criar_materia(tmp_path, "Física 1")
      assert [m.nome for m in descobrir_materias(tmp_path)] == ["Física 1"]

  def test_criar_duplicada(tmp_path): ...       # DadoInvalido
  def test_abrir_por_uid_inexistente(tmp_path): # NaoEncontrado
  ```

- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): descoberta e criação de matérias`

---

### Task 6: Histórico e desfazer (linhas)

**Files:**
- Create: `_app/backend/estudos/historico.py`, `_app/backend/estudos/repos/__init__.py`, `_app/backend/estudos/repos/_base.py`, `_app/backend/tests/test_historico.py`

**Interfaces:**
- Consumes: `transacao`.
- Produces:
  ```python
  # historico.py
  @dataclass
  class GrupoHistorico: id: int; momento: str; descricao: str; desfaz_grupo: int | None; desfeito_em: str | None
  class Operacao:
      con: sqlite3.Connection; grupo_id: int; raiz: Path | None
      def registrar(self, tabela: str, chave: dict, antes: dict | None, depois: dict | None) -> None
      def registrar_arquivo(self, caminho_rel: str, versao_rel: str | None) -> None   # usado na Task 9
  @contextmanager
  def operacao(con, descricao: str, raiz: Path | None = None) -> Iterator[Operacao]
      # abre transacao, cria historico_grupo; grupo sem mudanças é apagado no fim
  def listar(con, limite: int = 50) -> list[GrupoHistorico]
  def desfazer_ultimo(con, raiz: Path | None = None) -> GrupoHistorico | None
      # grupo mais recente com desfeito_em IS NULL e desfaz_grupo IS NULL; aplica mudanças em ordem inversa
      # (antes None → DELETE; depois None → INSERT antes; senão UPDATE para antes); arquivos: Task 9
      # registra novo grupo com desfaz_grupo; marca original com desfeito_em; retorna o original
  def podar(con, max_grupos: int) -> int   # apaga grupos mais antigos além do limite; retorna quantos

  # repos/_base.py — único lugar que monta SQL dinâmico
  TABELAS_PERMITIDAS: frozenset[str]   # tabelas de domínio da Task 4 (sem historico_*, schema_versao)
  def inserir(op: Operacao, tabela: str, valores: dict) -> int
  def atualizar(op: Operacao, tabela: str, chave: dict, valores: dict) -> None   # NaoEncontrado se 0 linhas
  def remover(op: Operacao, tabela: str, chave: dict) -> None
  def obter(con, tabela: str, chave: dict) -> dict | None
  ```
  `inserir/atualizar/remover` leem a linha antes, executam e chamam `op.registrar`. `remover` em tabela com filhos em cascata **registra também os filhos** (consulta `PRAGMA foreign_key_list` das tabelas permitidas para descobrir dependentes e registra-os antes, para que o desfazer os reinsira na ordem pai → filho). Nomes de tabela/coluna fora de `TABELAS_PERMITIDAS`/colunas reais (`PRAGMA table_info`) → `DadoInvalido`.

- [ ] **Step 1: Escrever os testes** (fixture `con` = matéria criada via `criar_materia` + `conectar`)

  ```python
  def test_desfazer_insercao(con):
      with operacao(con, "criar unidade") as op:
          uid = inserir(op, "unidade", {"numero": 1, "titulo": "U1", "origem": "manual"})
      desfazer_ultimo(con)
      assert obter(con, "unidade", {"id": uid}) is None

  def test_desfazer_atualizacao_e_remocao_em_grupo(con): ...  # um grupo com update + delete → ambos revertidos
  def test_desfazer_remocao_reinsere_filhos_em_cascata(con):
      # unidade → lista → questão → marcacao; remover lista; desfazer → lista, questão e marcação de volta com os mesmos ids
  def test_desfazer_nao_repete_grupo_ja_desfeito(con): ...   # dois desfazer seguidos revertem dois grupos distintos
  def test_falha_no_meio_nao_deixa_grupo(con): ...           # exceção dentro de operacao → nenhuma linha em historico_grupo
  def test_tabela_nao_permitida(con):
      with operacao(con, "x") as op, pytest.raises(DadoInvalido):
          inserir(op, "historico_grupo", {"descricao": "hack"})
  def test_podar(con): ...  # 5 grupos, podar(con, 2) == 3, restam os 2 mais novos
  ```

- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): histórico transacional e desfazer`

---

### Task 7: Repositórios de estrutura — matéria, unidades, eventos, tópicos

**Files:**
- Create: `_app/backend/estudos/modelos.py`, `_app/backend/estudos/repos/materia.py`, `repos/unidades.py`, `repos/eventos.py`, `repos/topicos.py`, `_app/backend/tests/test_repos_estrutura.py`

**Interfaces:**
- Consumes: `repos._base`, `Operacao`.
- Produces (dataclasses de leitura em `modelos.py`, `frozen=True`):
  ```python
  Materia(id, uid, nome, periodo, instituicao, professor, email_professor)
  Unidade(id, numero, titulo, origem, confianca, data_prova: str | None)
  Evento(id, tipo, data, hora_inicio, hora_fim, unidade_id, descricao, origem)
  Topico(id, unidade_id, pai_id, ordem, titulo, status, origem)

  # repos/materia.py
  def obter(con) -> Materia
  def atualizar(op, **campos) -> None
  # repos/unidades.py
  def criar(op, numero: int, titulo: str = "", origem: str = "manual", confianca: float | None = None) -> int
  def listar(con) -> list[Unidade]                  # ordem por numero; data_prova vem do evento 'prova'
  def atualizar(op, unidade_id: int, **campos) -> None
  def remover(op, unidade_id: int) -> None
  def unidade_atual(con, hoje: date) -> Unidade | None   # regra da spec §5
  # repos/eventos.py
  def criar(op, tipo: str, data: str, unidade_id: int | None = None, hora_inicio: str | None = None,
            hora_fim: str | None = None, descricao: str = "", origem: str = "manual") -> int
  def listar(con, unidade_id: int | None = None) -> list[Evento]   # ordem por data, hora_inicio
  def remover(op, evento_id: int) -> None
  # repos/topicos.py
  def criar(op, unidade_id: int, titulo: str, pai_id: int | None = None, ordem: int | None = None, origem: str = "manual") -> int
      # ordem None → max(ordem dos irmãos)+1
  def listar(con, unidade_id: int) -> list[Topico]   # ordem: pai antes dos filhos, depois ordem
  def definir_status(op, topico_id: int, status: str) -> None   # DadoInvalido fora de pendente/proxima/visto
  def atualizar(op, topico_id: int, **campos) -> None
  def remover(op, topico_id: int) -> None
  ```

- [ ] **Step 1: Escrever os testes**

  ```python
  def test_data_prova_vem_do_evento(con):
      with operacao(con, "x") as op:
          u = unidades.criar(op, 1); eventos.criar(op, "prova", "2026-09-14", unidade_id=u, hora_inicio="14:30")
      assert unidades.listar(con)[0].data_prova == "2026-09-14"

  def test_unidade_atual(con):
      # provas 2026-09-14 (U1), 2026-10-19 (U2), 2026-11-30 (U3)
      assert unidades.unidade_atual(con, date(2026, 10, 21)).numero == 3
      assert unidades.unidade_atual(con, date(2026, 9, 14)).numero == 1
      assert unidades.unidade_atual(con, date(2027, 1, 1)).numero == 3   # depois da última → última

  def test_quantidade_livre_de_unidades(con): ...   # cria 5 unidades; listar devolve 5
  def test_topicos_ordem_e_hierarquia(con): ...     # pai, 2 filhos com ordem automática 1 e 2
  def test_status_invalido(con): ...                 # DadoInvalido
  def test_desfazer_status_topico(con): ...          # definir_status + desfazer_ultimo → status anterior
  ```

- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): repositórios de matéria, unidades, eventos e tópicos`

---

### Task 8: Listas, questões e marcações

**Files:**
- Create: `_app/backend/estudos/repos/listas.py`, `repos/marcacoes.py`, `_app/backend/tests/test_repos_listas.py`
- Modify: `_app/backend/estudos/modelos.py` (dataclasses abaixo)

**Interfaces:**
- Consumes: Task 6 e 7.
- Produces:
  ```python
  Lista(id, codigo, titulo, unidade_id, fonte_id, liberacao, ordem, origem, aberta: bool)
  Questao(id, lista_id, rotulo, ordem, linha, enunciado_md, expressao, pagina_pdf, figura)
  @dataclass(frozen=True)
  class QuestaoEntrada: rotulo: str; linha: int = 1; enunciado_md: str = ""; expressao: str | None = None;
                        pagina_pdf: int | None = None; figura: str | None = None; chave_legada: str | None = None
  Placar(ok: int, err: int, dub: int, total: int, feitos_linha1: int, total_linha1: int,
         feitos_linha2: int, total_linha2: int, taxa_acerto: float | None)   # ok/(ok+err), None se 0

  # repos/listas.py
  def criar(op, codigo: str, titulo: str, unidade_id: int, liberacao: str = "auto",
            fonte_id: int | None = None, origem: str = "manual") -> int
  def listar(con, unidade_id: int) -> list[Lista]          # 'aberta' calculada pela regra da spec §5
  def obter(con, lista_id: int) -> Lista
  def definir_liberacao(op, lista_id: int, liberacao: str) -> None
  def vincular_topico(op, lista_id: int, topico_id: int) -> None
  def vincular_secao(op, lista_id: int, secao_id: int) -> None
  def sincronizar_questoes(op, lista_id: int, questoes: list[QuestaoEntrada]) -> dict[str, int]
      # upsert por rotulo (preserva id e marcação); ordem = posição na entrada; rótulos ausentes são removidos;
      # rótulo repetido na entrada → DadoInvalido; retorna {rotulo: questao_id}
  def listar_questoes(con, lista_id: int) -> list[Questao]
  def remover(op, lista_id: int) -> None
  # repos/marcacoes.py
  def definir(op, questao_id: int, estado: str | None) -> None   # None remove; agora ISO em atualizado_em
  def estados(con, unidade_id: int) -> dict[int, str]           # questao_id → estado
  def placar(con, unidade_id: int) -> Placar                    # só listas abertas
  ```

- [ ] **Step 1: Escrever os testes**

  ```python
  def test_lista_auto_abre_quando_topico_visto(con):
      # unidade, tópico pendente, lista auto vinculada ao tópico → aberta False; definir_status visto → True; pendente → False
  def test_liberacao_manual_tem_precedencia(con): ...   # travada + tópico visto → False; aberta + pendente → True

  def test_sincronizar_preserva_marcacao(con):
      ids = listas.sincronizar_questoes(op, l, [QuestaoEntrada("6(a)"), QuestaoEntrada("7", linha=2)])
      marcacoes.definir(op, ids["7"], "err")
      ids2 = listas.sincronizar_questoes(op, l, [QuestaoEntrada("7", linha=2, enunciado_md="novo"), QuestaoEntrada("8")])
      assert ids2["7"] == ids["7"] and marcacoes.estados(con, u)[ids["7"]] == "err"
      assert "6(a)" not in {q.rotulo for q in listas.listar_questoes(con, l)}

  def test_desfazer_sincronizacao_restaura_questao_e_marcacao(con):   # Review Focus 3
      # marca "6(a)" como ok; sincroniza sem "6(a)" (grupo próprio); desfazer_ultimo → "6(a)" volta com estado ok e mesmo id

  def test_rotulo_duplicado_na_entrada(con): ...   # DadoInvalido
  def test_placar(con):
      # lista aberta: L1 = 3 questões (ok, err, dub), L2 = 2 (ok, sem marca); lista travada com 1 ok (ignorada)
      p = marcacoes.placar(con, u)
      assert (p.ok, p.err, p.dub, p.total) == (2, 1, 1, 5)
      assert (p.feitos_linha1, p.total_linha1, p.feitos_linha2, p.total_linha2) == (3, 3, 1, 2)
      assert p.taxa_acerto == pytest.approx(2 / 3)
  def test_estado_invalido(con): ...  # DadoInvalido
  ```

- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): listas, questões com id estável e marcações`

---

### Task 9: Conteúdo Markdown, documentos, cronograma e formulário

**Files:**
- Create: `_app/backend/estudos/conteudo.py`, `repos/documentos.py`, `repos/cronograma.py`, `repos/formulas.py`, `_app/backend/tests/test_conteudo.py`, `_app/backend/tests/test_repos_conteudo.py`
- Modify: `_app/backend/estudos/historico.py` (`desfazer_ultimo` passa a restaurar arquivos), `modelos.py`

**Interfaces:**
- Consumes: Tasks 2 (`caminho_seguro`), 6, 7, 8.
- Produces:
  ```python
  # conteudo.py
  @dataclass
  class DocumentoMd: meta: dict[str, str | int | None]; corpo: str
  def ler_md(caminho: Path) -> DocumentoMd          # frontmatter "---\nchave: valor\n---"; int se só dígitos; "null"/vazio → None
  def serializar_md(doc: DocumentoMd) -> str         # chaves em ordem de inserção; round-trip exato com ler_md
  def escrever_md(op: Operacao, caminho_rel: str, doc: DocumentoMd) -> None
      # exige op.raiz; caminho_seguro; se existe, copia para .versoes/<caminho_rel>/<grupo_id>-<n>.md;
      # op.registrar_arquivo(caminho_rel, versao_rel ou None); grava UTF-8 com "\n"
  def apagar_md(op: Operacao, caminho_rel: str) -> None   # versiona e remove

  Documento(id, tipo, caminho, titulo, unidade_id, secao_id, questao_id, origem, atualizado_em)
  Sessao(id, unidade_id, codigo, data, foco_md, feito, ordem, origem, questao_ids: tuple[int, ...])
  Formula(id, unidade_id, secao_id, titulo, corpo_tex, notas_md, ordem, origem)

  # repos/documentos.py
  PASTA_POR_TIPO = {"resumo": "conteudo/resumos", "resolucao": "conteudo/resolucoes",
                    "plano": "conteudo/planos", "anotacao": "conteudo/anotacoes", "contexto": "conteudo"}
  def salvar(op, tipo: str, nome_arquivo: str, titulo: str, corpo: str, unidade_id: int | None = None,
             secao_id: int | None = None, questao_id: int | None = None, origem: str = "manual") -> int
      # caminho = PASTA_POR_TIPO[tipo]/nome_arquivo (.md acrescentado se faltar); upsert por caminho;
      # frontmatter = {tipo, titulo, unidade (número), secao (codigo), questao (id), origem}; NUNCA altera o corpo
  def listar(con, tipo: str | None = None, unidade_id: int | None = None) -> list[Documento]
  def ler_corpo(raiz: Path, documento: Documento) -> str
  def remover(op, documento_id: int) -> None
  # repos/cronograma.py
  def criar_sessao(op, unidade_id: int, codigo: str, data: str | None = None, foco_md: str = "",
                   ordem: int | None = None, origem: str = "manual") -> int
  def definir_feito(op, sessao_id: int, feito: bool) -> None
  def vincular_questoes(op, sessao_id: int, questao_ids: list[int]) -> None   # substitui o conjunto
  def listar(con, unidade_id: int) -> list[Sessao]
  def atualizar(op, sessao_id: int, **campos) -> None
  def remover(op, sessao_id: int) -> None
  # repos/formulas.py
  def criar(op, unidade_id: int, titulo: str, corpo_tex: str, notas_md: str = "",
            secao_id: int | None = None, origem: str = "manual") -> int
  def listar(con, unidade_id: int) -> list[Formula]
  def atualizar(op, formula_id: int, **campos) -> None
  def remover(op, formula_id: int) -> None
  ```
  `historico.desfazer_ultimo(con, raiz)`: mudança de arquivo com `versao_arquivo` → copia a versão de volta; sem versão → apaga o arquivo. `raiz` obrigatória quando o grupo tem arquivos (`DadoInvalido` se faltar).

- [ ] **Step 1: Escrever os testes**

  ```python
  def test_frontmatter_round_trip():
      doc = DocumentoMd({"tipo": "resumo", "titulo": "Integrais: polares", "unidade": 3, "secao": None}, "# T\n\n$x^2$\n")
      assert ler_md_texto(serializar_md(doc)) == doc   # helper de teste que escreve em tmp e lê

  def test_salvar_resumo_nao_altera_corpo(con, materia):
      corpo = "# 15.4\n\n> Referência\n\ntexto"
      with operacao(con, "x", materia.pasta) as op:
          d = documentos.salvar(op, "resumo", "polares", "Polares", corpo, unidade_id=u)
      doc = documentos.listar(con, "resumo")[0]
      assert doc.caminho == "conteudo/resumos/polares.md"
      assert documentos.ler_corpo(materia.pasta, doc) == corpo

  def test_desfazer_sobrescrita_restaura_arquivo(con, materia):
      # salvar v1 (grupo 1), salvar v2 no mesmo nome (grupo 2), desfazer → corpo v1; desfazer de novo → arquivo não existe e linha some

  def test_documento_fora_da_pasta(con, materia):   # nome_arquivo="../../x" → CaminhoInvalido
  def test_sessao_questoes_e_feito(con): ...       # vincular [q1,q2], listar → questao_ids == (q1,q2); definir_feito True
  def test_formula_crud_e_desfazer(con): ...
  ```

- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): documentos markdown versionados, cronograma e formulário`

---

### Task 10: API — app, matérias, painel, marcações e histórico

**Files:**
- Create: `_app/backend/estudos/main.py`, `estudos/api/__init__.py`, `api/deps.py`, `api/materias.py`, `api/painel.py`, `api/marcacoes.py`, `api/historico.py`, `_app/backend/tests/test_api_base.py`
- Modify: `estudos/modelos.py` (modelos Pydantic de API, sufixo `Entrada`/`Saida`)

**Interfaces:**
- Consumes: tudo das Tasks 1–9.
- Produces:
  ```python
  def create_app(settings: Settings) -> FastAPI
      # OrigemLocalMiddleware(porta=settings.porta); handlers: NaoEncontrado→404, DadoInvalido/CaminhoInvalido→422,
      # sqlite3.IntegrityError→409; corpo de erro sempre {"erro": str}; podar histórico após cada operação de escrita
  # api/deps.py
  def obter_settings(request) -> Settings                 # de app.state.settings
  def materia_dep(materia_uid: str, settings=Depends(obter_settings)) -> MateriaRef
  def con_dep(materia: MateriaRef = Depends(materia_dep)) -> Iterator[sqlite3.Connection]   # abre e fecha por requisição
  ```
  Rotas:
  | Método | Caminho | Corpo / retorno |
  |---|---|---|
  | GET | `/api/materias` | `[{uid, nome}]` |
  | POST | `/api/materias` | `{nome, periodo?}` → `{uid, nome}` (201) |
  | GET | `/api/materias/{uid}/painel?unidade=N` | `{materia, unidades, unidade_atual: numero, unidade: numero exibida, topicos, listas: [{…, questoes, }], marcacoes: {questao_id: estado}, sessoes, formulas, documentos (sem corpo), placar}`; sem `unidade` → unidade atual; matéria sem unidades → listas vazias e `unidade: null` |
  | PUT | `/api/materias/{uid}/marcacoes/{questao_id}` | `{estado: "ok"|"err"|"dub"|null}` → `{placar}` |
  | GET | `/api/materias/{uid}/historico?limite=50` | `[GrupoHistorico]` |
  | POST | `/api/materias/{uid}/historico/desfazer` | → `{desfeito: GrupoHistorico | null}` |

- [ ] **Step 1: Escrever os testes** (fixture `cliente`: `TestClient(create_app(carregar_settings(tmp/_app, tmp)), base_url="http://127.0.0.1:8790")`)

  ```python
  def test_criar_e_listar_materia(cliente):
      r = cliente.post("/api/materias", json={"nome": "Física 1"})
      assert r.status_code == 201
      assert [m["nome"] for m in cliente.get("/api/materias").json()] == ["Física 1"]

  def test_materia_inexistente_404(cliente):
      assert cliente.get("/api/materias/naoexiste/painel").status_code == 404

  def test_painel_materia_vazia(cliente): ...   # unidade None, listas []

  def test_marcar_e_desfazer(cliente, materia_com_lista):   # fixture popula via repos
      uid, qid = materia_com_lista
      r = cliente.put(f"/api/materias/{uid}/marcacoes/{qid}", json={"estado": "ok"})
      assert r.json()["placar"]["ok"] == 1
      cliente.post(f"/api/materias/{uid}/historico/desfazer", json={})
      assert cliente.get(f"/api/materias/{uid}/painel").json()["marcacoes"] == {}

  def test_estado_invalido_422(cliente, materia_com_lista): ...
  def test_post_text_plain_403(cliente): ...
  ```

- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): app FastAPI com matérias, painel, marcações e histórico`

---

### Task 11: API — CRUD de unidades, eventos, tópicos, listas, cronograma, fórmulas e documentos

**Files:**
- Create: `api/unidades.py`, `api/topicos.py`, `api/listas.py`, `api/cronograma.py`, `api/formulas.py`, `api/documentos.py`, `_app/backend/tests/test_api_crud.py`
- Modify: `estudos/main.py` (incluir routers), `estudos/modelos.py`

**Interfaces:**
- Consumes: repos das Tasks 7–9, deps da Task 10.
- Produces: rotas REST sob `/api/materias/{uid}` — cada uma é uma chamada de repo dentro de `operacao(con, descricao, materia.pasta)` com descrição legível em português (ex.: `"Marcar tópico 'Integrais triplas' como visto"`):
  - `unidades`: `POST /unidades`, `PATCH /unidades/{id}`, `DELETE /unidades/{id}`; `POST /eventos`, `DELETE /eventos/{id}`
  - `topicos`: `POST /topicos`, `PATCH /topicos/{id}` (inclui `status`), `DELETE /topicos/{id}`
  - `listas`: `POST /listas`, `PATCH /listas/{id}` (`liberacao`, `titulo`, `unidade_id`), `PUT /listas/{id}/questoes` (lista de `QuestaoEntrada` → `{rotulo: id}`), `POST /listas/{id}/topicos/{topico_id}`, `DELETE /listas/{id}`
  - `cronograma`: `POST /sessoes`, `PATCH /sessoes/{id}` (inclui `feito`), `PUT /sessoes/{id}/questoes`, `DELETE /sessoes/{id}`
  - `formulas`: `POST /formulas`, `PATCH /formulas/{id}`, `DELETE /formulas/{id}`
  - `documentos`: `GET /documentos?tipo=&unidade_id=`, `GET /documentos/{id}` (com `corpo`), `PUT /documentos` (`salvar`), `DELETE /documentos/{id}`
  - `GET /arquivos/{uid}/{caminho:path}` → `FileResponse` via `caminho_seguro(materia.pasta, caminho)`

- [ ] **Step 1: Escrever os testes** — um fluxo ponta a ponta que exercita todas as rotas e o desfazer:

  ```python
  def test_fluxo_completo(cliente, uid):
      u = cliente.post(f"/api/materias/{uid}/unidades", json={"numero": 1, "titulo": "Derivadas"}).json()["id"]
      cliente.post(f"/api/materias/{uid}/eventos", json={"tipo": "prova", "data": "2026-09-14", "unidade_id": u})
      t = cliente.post(f"/api/materias/{uid}/topicos", json={"unidade_id": u, "titulo": "Limites"}).json()["id"]
      l = cliente.post(f"/api/materias/{uid}/listas", json={"codigo": "L1", "titulo": "Lista 1", "unidade_id": u}).json()["id"]
      cliente.post(f"/api/materias/{uid}/listas/{l}/topicos/{t}")
      cliente.put(f"/api/materias/{uid}/listas/{l}/questoes", json=[{"rotulo": "1"}, {"rotulo": "2", "linha": 2}])
      painel = cliente.get(f"/api/materias/{uid}/painel").json()
      assert painel["listas"][0]["aberta"] is False
      cliente.patch(f"/api/materias/{uid}/topicos/{t}", json={"status": "visto"})
      assert cliente.get(f"/api/materias/{uid}/painel").json()["listas"][0]["aberta"] is True
      assert cliente.get(f"/api/materias/{uid}/painel").json()["unidades"][0]["data_prova"] == "2026-09-14"

  def test_documento_salvar_ler_e_arquivo(cliente, uid): ...   # PUT documento; GET corpo; GET /arquivos/... devolve o .md
  def test_arquivo_traversal_422(cliente, uid):
      assert cliente.get(f"/arquivos/{uid}/..%2F..%2Fsegredo.txt").status_code == 422
  def test_remover_unidade_com_lista_409(cliente, uid): ...
  ```

- [ ] **Step 2–4:** FAIL → implementar → PASS.
- [ ] **Step 5: Commit** — `feat(backend): rotas CRUD da matéria`

---

### Task 12: Inicialização lado a lado com o legado

**Files:**
- Create: `_app/abrir-novo.bat`, `_app/backend/estudos/__main__.py`, `_app/backend/tests/test_main.py`
- Modify: `README.md` (seção "Novo motor (em construção)" com os comandos abaixo)

**Interfaces:**
- Consumes: `create_app`, `carregar_settings`.
- Produces: `python -m estudos [--porta N] [--sem-navegador]` → `uvicorn.run(create_app(settings), host=settings.host, port=porta)`; abre o navegador em `http://127.0.0.1:{porta}/docs` até a Fase 5 existir. `abrir-novo.bat`: cria o venv se não existir (`py -3.13 -m venv` + `pip install -e .`), depois `python -m estudos`.

- [ ] **Step 1: Escrever o teste**

  ```python
  def test_argumentos(monkeypatch, tmp_path):
      chamado = {}
      monkeypatch.setattr("uvicorn.run", lambda app, host, port: chamado.update(host=host, port=port))
      main(["--porta", "8801", "--sem-navegador"], app_dir=tmp_path / "_app")
      assert chamado == {"host": "127.0.0.1", "port": 8801}
  ```
- [ ] **Step 2–4:** FAIL → implementar `main(argv: list[str] | None = None, app_dir: Path | None = None) -> None` em `__main__.py` → PASS.
- [ ] **Step 5: Verificação manual** — rodar `_app/abrir-novo.bat`; `GET http://127.0.0.1:8790/api/materias` responde `[]` (o workspace ainda não tem `materia.db`); o legado (`abrir.bat`, porta 8780) continua funcionando ao mesmo tempo.
- [ ] **Step 6: Suite completa** — `.venv/Scripts/python -m pytest -q` → todos PASS.
- [ ] **Step 7: Commit** — `feat(backend): inicialização do novo motor ao lado do legado`

---

## Próximos planos (escritos ao final desta fase)

- `2026-10-xx-fase-2-migracao-calculo-2.md` — script idempotente `curso.json`/`exercicios.json`/`status.json`/`.md` → `materia.db` + `conteudo/` com frontmatter; mapeia chaves `"15.4-22"` para `questao.chave_legada`; move o app antigo para `legado/`.
- `…-fase-3-importacao.md` — `pdf.py` (PyMuPDF), classificador, parsers (fixtures: `Programa.pdf`, `Calendario.pdf`, `info_S3.pdf`, `exercicios_3un.pdf`, `Lista5_2026-1.pdf`, Stewart com outline, Guidorizzi sem outline), vínculo e rotas de revisão.
- `…-fase-4-rag.md`, `…-fase-5-frontend.md`, `…-fase-6-agente.md`, `…-fase-7-limpeza.md`.
