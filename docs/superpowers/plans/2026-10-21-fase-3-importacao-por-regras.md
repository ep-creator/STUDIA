# Fase 3 — Importação por Regras: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Subir um PDF (programa, calendário, informações da turma, livro, lista, slides, prova, anotação) e a plataforma classificar, extrair, vincular e propor tudo por regras — sem IA —, mostrando uma proposta revisável que só grava no banco quando confirmada.

**Architecture:** `importacao/pdf.py` abre o PDF com PyMuPDF e entrega páginas de texto limpo + sumário + rótulos de página. `classificador.py` escolhe o tipo. Um parser puro por tipo transforma texto em dataclasses. `vinculo.py` liga tópicos↔seções↔listas por similaridade de texto. `pipeline.py` junta tudo numa **proposta** (JSON na tabela `importacao`), editável pela API, e `confirmar` aplica a proposta pelos repositórios numa operação desfazível.

**Tech Stack:** Python 3.13, PyMuPDF (`pymupdf`), FastAPI + `python-multipart` (upload), SQLite.

**Spec:** `docs/superpowers/specs/2026-10-20-refatoracao-plataforma-design.md` §6 (pipeline, classificador, parsers, vínculo).

## Global Constraints

- **Sem IA e sem valores de disciplina no código.** Tabelas de idioma (ordinais por extenso, numerais romanos, dias da semana, meses) são permitidas.
- **Toda extração carrega `confianca` (0–1)**; item com `confianca < settings.limiar_confianca` vai marcado `"revisar": true` na proposta. Vínculos abaixo de `settings.limiar_vinculo` não são propostos.
- **Proposta nunca toca o domínio.** Só `confirmar` grava, numa única `operacao` (um "desfazer" reverte a importação inteira).
- **Reimportar nunca apaga.** Para listas, o modo padrão é `mesclar` (acrescenta e atualiza; não remove questões nem marcações). `substituir` só se o usuário escolher na revisão.
- PDF sem texto (escaneado) é aceito e registrado; a proposta diz "sem texto extraível" e não inventa conteúdo. OCR está fora do escopo.
- Parsers são **funções puras** (texto → dataclass), testadas com o texto real dos PDFs de Cálculo 2 e com PDFs sintéticos gerados pelo próprio PyMuPDF nos testes.
- Mesmas convenções das fases anteriores (português, `snake_case`, TDD, `.venv/Scripts/python -m pytest` em `_app/backend`).

## O que os PDFs reais mostram (base das regras)

| Arquivo | Achado | Regra resultante |
|---|---|---|
| `Programa.pdf` | "Primeira Unidade"; tópico `○Funções…` (marcador colado); subtópico em duas linhas: `•` sozinho e o texto na linha seguinte | linha só com marcador ⇒ o item é a próxima linha não vazia |
| `Calendario.pdf` | datas `dd/mm` uma por linha; `12/09 (sábado, 10h-12h)`; `Primeiro exame: 14/09, 14h30-17h`; `Segunda chamada:` e `Exame final:` no fim; ano no cabeçalho `2026-2` | prova da unidade = linha "`<ordinal> exame`"; horário `HHhMM-HHhMM` |
| `info_S3.pdf` | `Nome – email`; `Quartas-feiras: 13h-15h`; `Referência` / `Referências complementares`; critérios com `•` sozinho na linha | item termina em `;`/`.` ou quando a linha seguinte começa com maiúscula sem marcador |
| `exercicios_Nun.pdf` | `Exercícios da terceira unidade`; `J. Stewart, Cálculo, V.II…`; `` + `Seção 15.4`; duas linhas `o 7,8,11,…` | 1ª linha `o` = linha 1, 2ª = linha 2; unidade pelo ordinal do título |
| `Lista5_2026-1.pdf` (LaTeX) | acentos combinantes (`Ciˆencias`, `Mudan¸ca`); `Quinta Lista…`; `Conteúdos:` em duas linhas; questões `N. ` ou `N.` colado; itens `a.`; fórmulas truncadas | numeração sequencial obrigatória (N = anterior+1); itens `a.` ficam no enunciado; código `L5` pelo ordinal |
| Stewart vol. 2 | sumário embutido (383 entradas, níveis 1–3), códigos `15.4 …` e `15.4 Exercícios`; rótulos de página (`get_label` = número impresso); `I- Respostas para os Exercícios Ímpares` | seção = entrada com código que não é "Exercícios"; fim = início da próxima seção com código − 1; offset pela moda de `índice − rótulo` |
| Guidorizzi vol. 2 | sem sumário embutido; página "SUMARIO"/"Sumário" com OCR (`1 O` = 10, `10. l` = 10.1, página `1 23`); rótulos de página presentes | parser de sumário com normalização de OCR; confiança 0.7 |
| Leithold | 770 páginas sem texto | `sem_texto=True`; nenhuma seção |

## Review Focus

1. **Reimportar a lista de uma seção que já tem marcações** (ex.: `exercicios_3un.pdf` sobre o Cálculo 2 migrado) → nenhuma marcação perdida; questões novas acrescentadas. Teste na Task 11.
2. **PDF escaneado / vazio / corrompido / não-PDF** → proposta "sem texto" ou erro 422 claro; nunca 500. Testes nas Tasks 1 e 10.
3. **O mesmo arquivo enviado duas vezes** → devolve a importação existente (sha256), não duplica fonte. Teste na Task 9.
4. **Confirmar duas vezes / confirmar proposta descartada** → 409. Teste na Task 10.
5. **Matéria nova só com PDFs** → unidades, datas de prova, tópicos, seções do livro, listas e vínculos sem nenhum cadastro manual. Teste na Task 11.

---

## Mapa de arquivos

```text
_app/backend/
├── pyproject.toml                          # Task 1 (pymupdf, python-multipart)
├── estudos/
│   ├── db/migracoes/0004_importacao.sql    # Task 2
│   ├── repos/importacoes.py turma.py       # Task 2
│   ├── importacao/
│   │   ├── __init__.py  pdf.py             # Task 1
│   │   ├── idioma.py                       # Task 3 (ordinais, romanos, dias, normalizar)
│   │   ├── classificador.py                # Task 3
│   │   ├── parsers/programa.py calendario.py   # Task 4
│   │   ├── parsers/turma.py                # Task 5
│   │   ├── parsers/livro.py                # Task 6
│   │   ├── parsers/lista.py                # Task 7
│   │   ├── vinculo.py                      # Task 8
│   │   └── pipeline.py                     # Task 9
│   └── api/importacoes.py                  # Task 10
└── tests/
    ├── pdfs_sinteticos.py                  # Task 1 (gera PDFs de teste com PyMuPDF)
    ├── test_importacao_pdf.py … test_importacao_ponta_a_ponta.py
```

---

### Task 1: Dependências e leitor de PDF

**Files:** Modify `pyproject.toml`; Create `estudos/importacao/__init__.py`, `estudos/importacao/pdf.py`, `tests/pdfs_sinteticos.py`, `tests/test_importacao_pdf.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True) class PaginaPdf: indice: int; rotulo: str; texto: str; largura: float; altura: float   # indice 1-based
  @dataclass(frozen=True) class EntradaSumario: nivel: int; titulo: str; pagina: int                            # pagina 1-based
  @dataclass(frozen=True) class DocumentoPdf:
      paginas: tuple[PaginaPdf, ...]; sumario: tuple[EntradaSumario, ...]; metadados: dict[str, str]
      @property def sem_texto(self) -> bool          # < 50 caracteres úteis em ≥ 90% das páginas
      def texto(self, ini: int = 1, fim: int | None = None) -> str
  class PdfInvalido(ValueError): ...
  def abrir_pdf(caminho: Path, limite_paginas: int | None = None) -> DocumentoPdf   # arquivo inválido/protegido → PdfInvalido
  def limpar_texto(texto: str) -> str      # acentos combinantes LaTeX (ˆe→ê, ´a→á, ¸c→ç, ˜a→ã, ´ı→í), ligaduras ﬁ/ﬂ, (cid:N), →•, espaços repetidos
  def remover_repetidos(paginas: list[str]) -> list[str]   # linha idêntica (dígitos normalizados) em ≥ 30% das páginas (mín. 5 páginas) sai
  ```
  `tests/pdfs_sinteticos.py`: `criar_pdf(caminho, paginas: list[str], sumario=None, paisagem=False, rotulos=None) -> Path` usando `pymupdf.open()` + `insert_text` + `set_toc` + `set_page_labels`.

- [ ] **Steps:** testes (`limpar_texto("Ciˆencias … Mudan¸ca … var´ıaveis")` → "Ciências … Mudança … variáveis"; `remover_repetidos` tira "Calculo15B:calculo7 … Page 922"; PDF sintético com sumário e rótulos lido de volta; arquivo `.txt` renomeado para `.pdf` → `PdfInvalido`; PDF sem texto → `sem_texto`; real: Stewart tem 383 entradas e rótulo "790" no índice 301; Leithold `sem_texto` — testes reais pulam se o arquivo faltar) → RED → implementar → GREEN → commit `feat(importacao): leitor de PDF com PyMuPDF e limpeza de texto`.

---

### Task 2: Tabela de importações e repositório da turma

**Files:** Create `db/migracoes/0004_importacao.sql`, `repos/importacoes.py`, `repos/turma.py`, `tests/test_repos_importacao_turma.py`; Modify `repos/_base.py` (`TABELAS_PERMITIDAS`), `modelos.py`

**Interfaces:**
- SQL: `importacao(id, fonte_id REFERENCES fonte ON DELETE CASCADE, tipo, estado CHECK IN ('proposta','confirmada','descartada'), proposta_json TEXT NOT NULL, criada_em, confirmada_em)`.
- ```python
  Importacao(id, fonte_id, tipo, estado, proposta: dict, criada_em, confirmada_em)
  # repos/importacoes.py  (rascunhos: escrevem SEM histórico — não são domínio)
  def criar(con, fonte_id: int, tipo: str, proposta: dict) -> int
  def obter(con, importacao_id: int) -> Importacao
  def por_fonte(con, fonte_id: int) -> Importacao | None
  def listar(con, estado: str | None = None) -> list[Importacao]
  def atualizar_proposta(con, importacao_id: int, proposta: dict) -> None   # só em 'proposta', senão DadoInvalido
  def marcar(con, importacao_id: int, estado: str) -> None                  # 'confirmada' grava confirmada_em
  # repos/turma.py (com histórico)
  HorarioAula(id, dia_semana, hora_inicio, hora_fim); Criterio(id, ordem, texto, origem)
  def definir_horarios(op, horarios: list[tuple[int, str, str]]) -> None    # substitui o conjunto
  def listar_horarios(con) -> list[HorarioAula]
  def definir_criterios(op, textos: list[str], origem: str = "manual") -> None
  def listar_criterios(con) -> list[Criterio]
  ```
- [ ] **Steps:** testes (estados, edição só em proposta, cascade ao apagar fonte, horários/critérios substituídos e desfazíveis) → RED → implementar → GREEN → commit.

---

### Task 3: Idioma e classificador

**Files:** Create `importacao/idioma.py`, `importacao/classificador.py`, `tests/test_importacao_classificador.py`

**Interfaces:**
- ```python
  # idioma.py
  def normalizar(texto: str) -> str                      # minúsculas, sem acento, sem pontuação, espaços simples
  def ordinal_para_int(palavra: str) -> int | None       # "Primeira"/"primeiro"/"Terceira"/"décima"… e "3ª"/"3o"; romanos "IV"
  def tokens_relevantes(texto: str) -> list[str]          # normalizar + remove stopwords PT (de, da, do, em, e, a, o, as, os, para, com, por, no, na, nas, nos, um, uma, mais)
  DIAS_SEMANA = {"segunda": 0, …, "domingo": 6}
  # classificador.py
  TIPOS = ("programa", "calendario", "turma", "livro", "lista", "slides", "prova", "anotacao", "outro")
  @dataclass(frozen=True) class Classificacao: tipo: str; confianca: float; sinais: dict[str, float]
  def classificar(doc: DocumentoPdf, nome_arquivo: str = "") -> Classificacao
  ```
  Pontuação (somente das 2 primeiras páginas + metadados; cada sinal soma pontos, vence o maior; `confianca = (1º − 2º) / 1º`, mínimo 0.2; nada pontuou → `outro`, 0.2): sinais da spec §6.1 com os achados reais (ex.: `calendario` = palavra "calendário" + ≥ 6 datas `dd/mm` + "exame"; `lista` = "lista de exercícios" / "exercícios da … unidade" / ≥ 3 blocos "Seção X.Y"; `livro` = ≥ 100 páginas ou sumário com ≥ 10 entradas numeradas; `slides` = ≥ 80% das páginas em paisagem; `sem_texto` com ≥ 100 páginas → `livro`, senão `outro`).
- [ ] **Steps:** testes com os 13 PDFs reais (tipo esperado para cada um: Programa→programa, Calendario→calendario, info_S3→turma, exercicios_Nun→lista, Lista1..6→lista, 4 livros→livro) + sintéticos (paisagem→slides; 1 página em branco→outro) → RED → implementar → GREEN → commit.

---

### Task 4: Parsers de programa e calendário

**Files:** Create `importacao/parsers/__init__.py`, `parsers/programa.py`, `parsers/calendario.py`, `tests/test_parser_programa_calendario.py`

**Interfaces:**
- ```python
  @dataclass class TopicoExtraido: titulo: str; filhos: list["TopicoExtraido"]
  @dataclass class UnidadeExtraida: numero: int; titulo: str; topicos: list[TopicoExtraido]
  def extrair_programa(texto: str) -> list[UnidadeExtraida]
      # cabeçalho: "^<ordinal> Unidade" | "^Unidade <n|romano>"; nível 1: ○ ◦ o▪ ; nível 2: • - – ‣; marcador sozinho ⇒ próxima linha;
      # linha sem marcador continua o item anterior; texto antes da 1ª unidade é ignorado
  @dataclass class EventoExtraido: tipo: str; data: str; hora_inicio: str | None; hora_fim: str | None; descricao: str
  @dataclass class UnidadeCalendario: numero: int; aulas: list[EventoExtraido]; prova: EventoExtraido | None
  @dataclass class CalendarioExtraido: ano: int | None; unidades: list[UnidadeCalendario]; eventos: list[EventoExtraido]
  def extrair_calendario(texto: str, ano_padrao: int | None = None) -> CalendarioExtraido
      # ano: 1º "20\d\d" do cabeçalho (senão ano_padrao); "(sábado, 10h-12h)" ⇒ tipo 'extra' com horário; "<ordinal> exame|prova:" ⇒ prova da unidade;
      # "Segunda chamada:" ⇒ 'segunda_chamada'; "Exame final:" ⇒ 'exame_final'; horário "14h30-17h" ⇒ ("14:30","17:00")
  ```
- [ ] **Steps:** testes com o texto real (PyMuPDF) dos dois PDFs: programa = 3 unidades; U1 com 2 tópicos e 6 + 4 subtópicos; U3 "Integrais duplas em coordenadas polares" sem filhos; calendário: ano 2026; U1 9 aulas (uma `extra` 12/09 10:00–12:00) e prova 2026-09-14 14:30–17:00; U3 prova 2026-11-30; 2 eventos finais (09/12 e 14/12). Variações sintéticas: "Unidade II", "1ª Unidade", sem ano → `ano_padrao` → RED → implementar → GREEN → commit.

---

### Task 5: Parser de informações da turma

**Files:** Create `parsers/turma.py`, `tests/test_parser_turma.py`

**Interfaces:**
- ```python
  @dataclass class ReferenciaExtraida: texto: str; papel: str              # 'principal' | 'complementar'
  @dataclass class TurmaExtraida: professor: str | None; email: str | None; horarios: list[tuple[int, str, str]]
                                  referencias: list[ReferenciaExtraida]; criterios: list[str]
  def extrair_turma(texto: str) -> TurmaExtraida
      # professor = texto antes de "–|-" na 1ª linha com e-mail; horários "<dia>(s)[-\s]feiras?: HHh[MM]-HHh[MM]";
      # "Referência(s)" ⇒ principal até "Referências complementares" ⇒ complementar, até a próxima linha-título (linha curta sem pontuação final seguida de texto)
      # critérios: itens com marcador depois da frase que contém "critérios de avaliação"; item termina em ;/. ou antes de linha que começa com maiúscula sem marcador
  ```
- [ ] **Steps:** testes com o texto real: professor "Henrique Araújo", e-mail, horários [(2,"13:00","15:00"),(4,"15:00","17:00")], 1 principal (Stewart) + 2 complementares, 6 critérios (o 1º com 3 linhas juntadas; o último "Deve haver clareza e organização") → RED → implementar → GREEN → commit.

---

### Task 6: Parser de livro (sumário, offset, gabarito)

**Files:** Create `parsers/livro.py`, `tests/test_parser_livro.py`

**Interfaces:**
- ```python
  @dataclass class SecaoExtraida: codigo: str; titulo: str; nivel: int; pagina_pdf_ini: int; pagina_pdf_fim: int; confianca: float
  @dataclass class LivroExtraido:
      origem: str                     # 'sumario_embutido' | 'pagina_sumario' | 'nenhum'
      secoes: list[SecaoExtraida]; offset_pagina: int | None; gabarito: tuple[int, int] | None; sem_texto: bool; avisos: list[str]
  def extrair_livro(doc: DocumentoPdf) -> LivroExtraido
  def normalizar_ocr_codigo(token: str) -> str        # "1 O"→"10", "10. l"→"10.1", "1 1. l"→"11.1", "4. 7"→"4.7", "13'"→"13"
  ```
  Regras: (1) sumário embutido: entradas `^(\d+(?:\.\d+)*)\s*[-–.]?\s+(.+)` cujo título **não** é `Exercícios`/`Revisão`/`Projeto…`; `nivel = pontos + 1`; confiança 1.0. (2) Sem sumário: páginas (até a 30ª) com "SUMÁRIO/Sumário/Índice"; linhas `<código> <título>, <página impressa>` com títulos de várias linhas; páginas impressas → PDF pelo offset; confiança 0.7; código fora de ordem crescente ⇒ descartado + aviso. (3) Offset = moda de `índice − int(rótulo)` nas páginas com rótulo numérico; sem rótulos ⇒ número isolado na 1ª/última linha; nenhum ⇒ `None` + aviso. (4) Fim de seção = início da próxima seção de nível ≤ ao seu − 1 (última → início do gabarito − 1 ou última página). (5) Gabarito = entrada `Respostas…Exercícios` / `Respostas, Sugestões` / `Gabarito` até a próxima entrada de nível ≤ ou o fim.
- [ ] **Steps:** testes reais: Stewart → `sumario_embutido`, seção 15.4 = 406–411, 15.8 começa em 433, nenhuma seção "15.4 Exercícios", offset −489, gabarito começa em 613; Guidorizzi → `pagina_sumario`, seção "10.1" existe com página impressa 173 → PDF 188, offset +15, gabarito "Respostas, Sugestões ou Soluções" ≈ 437; Leithold → `nenhum`, `sem_texto`; unitários de `normalizar_ocr_codigo` → RED → implementar → GREEN → commit.

---

### Task 7: Parser de listas

**Files:** Create `parsers/lista.py`, `tests/test_parser_lista.py`

**Interfaces:**
- ```python
  @dataclass class QuestaoExtraida: rotulo: str; linha: int; enunciado_md: str; pagina_pdf: int | None
  @dataclass class ListaExtraida: codigo: str; titulo: str; secao_livro: str | None; questoes: list[QuestaoExtraida]
  @dataclass class ArquivoListas:
      formato: str                      # 'por_secao' | 'numerada'
      titulo: str; unidade: int | None  # ordinal do título ("Exercícios da terceira unidade")
      referencia_livro: str | None      # linha "J. Stewart, Cálculo, V.II…"
      conteudos: list[str]              # linha(s) "Conteúdos:" separadas por vírgula
      listas: list[ListaExtraida]; avisos: list[str]
  def extrair_listas(doc: DocumentoPdf, nome_arquivo: str = "") -> ArquivoListas
      # por_secao: bloco "Seção <cod>" + linhas "o <rótulos>" (1ª = linha 1, 2ª = linha 2); rótulos separados por vírgula, "38(a)", "20(primeira parte)" preservados
      # numerada: "^(\d{1,3})\.\s*" só aceita N = anterior + 1; enunciado até a próxima questão (itens "a." juntos); código "L<n>" pelo ordinal do título
      #           ("Quinta Lista" → L5) ou "Lista\s*(\d+)" no nome do arquivo; senão o nome do arquivo sem extensão
  ```
- [ ] **Steps:** testes reais: `exercicios_3un` → por_secao, unidade 3, 6 listas, 15.4 linha 1 = [7,8,11,17,21,22,25,29], 15.9 tem "38(a)", 15.10 tem "20(primeira parte)"; `exercicios_1un` 14.3 tem "101(b)(c)(d)"; `Lista5` → numerada, código L5, 15 questões 1..15, conteúdos ["Coordenadas polares", "Integral dupla em coordenadas polares", "Mudança de variáveis"], questão 5 ("5.Calcule…") reconhecida; as 6 listas UFPE têm numeração 1..N sem buracos → RED → implementar → GREEN → commit.

---

### Task 8: Vínculos por similaridade

**Files:** Create `importacao/vinculo.py`, `tests/test_importacao_vinculo.py`

**Interfaces:**
- ```python
  @dataclass(frozen=True) class Candidato: chave: object; titulo: str
  @dataclass(frozen=True) class Vinculo: chave: object; titulo: str; confianca: float
  def similaridade(a: str, b: str, idf: dict[str, float]) -> float     # Jaccard ponderado por IDF dos tokens_relevantes
  def construir_idf(titulos: list[str]) -> dict[str, float]
  def melhores(texto: str, candidatos: list[Candidato], limiar: float, maximo: int = 1) -> list[Vinculo]
      # ordena por similaridade; empate exato entre os dois primeiros ⇒ confiança reduzida à metade
  def unidade_majoritaria(unidades: list[int]) -> tuple[int | None, float]   # (unidade, fração dos votos)
  ```
- [ ] **Steps:** testes com títulos reais: tópico "Integrais triplas em coordenadas cilíndricas" → Stewart "15.8 Integrais Triplas em Coordenadas Cilíndricas" acima de 0.8; "Multiplicadores de Lagrange" → 14.8; "Gráficos" sem candidato acima de 0.35; conteúdo "Integral dupla em coordenadas polares" → tópico "Integrais duplas em coordenadas polares" (singular/plural: `tokens_relevantes` tira o "s" final de palavras com ≥ 5 letras) → RED → implementar → GREEN → commit.

---

### Task 9: Pipeline — proposta e confirmação

**Files:** Create `importacao/pipeline.py`, `tests/test_importacao_pipeline.py`

**Interfaces:**
- Consumes: Tasks 1–8, repos das Fases 1–2.
- ```python
  PASTA_POR_TIPO = {"programa": "fontes/documentos", "calendario": "fontes/documentos", "turma": "fontes/documentos",
                    "livro": "fontes/livros", "lista": "fontes/listas", "slides": "fontes/slides", "prova": "fontes/provas",
                    "anotacao": "fontes/anotacoes", "outro": "fontes/documentos"}
  def receber_arquivo(con, raiz: Path, origem: Path, nome_original: str, settings: Settings) -> Importacao
      # sha256 já registrado ⇒ devolve a importação existente; senão copia para fontes/<tipo>/<nome> (sufixo -2 em colisão),
      # registra a fonte (origem='importado') numa operação, classifica, extrai e cria a importação 'proposta'
  def reprocessar(con, raiz: Path, importacao_id: int, tipo: str, settings: Settings) -> Importacao   # usuário corrigiu o tipo
  def confirmar(con, raiz: Path, importacao_id: int) -> dict                                      # aplica; devolve resumo {criados, atualizados, vinculos}
  def descartar(con, importacao_id: int) -> None
  ```
  Formato da proposta (JSON; todos os itens têm `confianca` e `revisar`):
  - `programa`: `{"unidades": [{"numero", "titulo", "topicos": [{"titulo", "filhos": [...], "secoes": [{"secao_id", "codigo", "livro", "confianca", "aceito"}]}]}]}` — seções propostas por `vinculo.melhores` contra as seções já cadastradas.
  - `calendario`: `{"ano", "unidades": [{"numero", "aulas": [...], "prova": {...}}], "eventos": [...]}`.
  - `turma`: `{"professor", "email", "horarios", "referencias": [{"texto", "papel", "fonte_id"}], "criterios"}` — `fonte_id` proposto por similaridade com os livros cadastrados.
  - `livro`: `{"papel", "titulo_obra", "offset_pagina", "gabarito", "origem", "sem_texto", "secoes": [...], "equivalencias": [{"secao", "equivalente_id", "confianca"}]}` — equivalências por similaridade de título com o livro principal.
  - `lista`: `{"formato", "modo": "mesclar", "unidade": {"numero", "confianca"}, "listas": [{"codigo", "titulo", "secao_id", "topicos": [...], "questoes": [...], "existente": {"lista_id", "novas", "mantidas", "ausentes"}}]}` — unidade: ordinal do título; senão unidade majoritária dos tópicos/seções vinculados.
  - demais tipos: `{"observacao": "registrado; indexação na Fase 4"}`.
  Confirmação (uma `operacao("Importar <arquivo>")`): programa → upsert de unidades por número e tópicos por título normalizado + `topico_secao` aceitos; calendário → eventos por (tipo, data, unidade) sem duplicar; turma → `materia.professor/email_professor`, horários, critérios, papel dos livros referenciados; livro → `livro` + seções (upsert por código) + equivalências; lista → listas por código (cria ou mescla) + `lista_secao`/`lista_topico` + questões (`mesclar`: só acrescenta/atualiza; `substituir`: `sincronizar_questoes`).
- [ ] **Steps:** testes (com uma matéria vazia e os PDFs reais copiados para `tmp_path`): programa propõe 3 unidades; confirmar cria 3 unidades e os tópicos; calendário depois cria 3 provas com hora; mesmo arquivo duas vezes ⇒ mesma importação, 1 fonte; reprocessar com outro tipo troca a proposta; confirmar duas vezes ⇒ `DadoInvalido`; desfazer depois de confirmar remove tudo da importação → RED → implementar → GREEN → commit.

---

### Task 10: API de importação

**Files:** Create `api/importacoes.py`, `tests/test_api_importacoes.py`; Modify `main.py`, `pyproject.toml` (já em Task 1)

**Interfaces:**
| Método | Caminho | Corpo / retorno |
|---|---|---|
| POST | `/api/materias/{uid}/importacoes` | multipart `arquivo` → `Importacao` (201; 200 se já existia) |
| GET | `/api/materias/{uid}/importacoes?estado=` | lista |
| GET | `/api/materias/{uid}/importacoes/{id}` | `Importacao` + `pendencias` (nº de itens `revisar`) |
| PUT | `/api/materias/{uid}/importacoes/{id}` | proposta editada → `Importacao` (422 se o formato não bate com o tipo) |
| POST | `/api/materias/{uid}/importacoes/{id}/tipo` | `{tipo}` → reprocessa |
| POST | `/api/materias/{uid}/importacoes/{id}/confirmar` | → resumo (409 se não está em 'proposta') |
| POST | `/api/materias/{uid}/importacoes/{id}/descartar` | → `{ok}` |

Upload: limite configurável (`settings.limite_upload_mb`, padrão 200), só `.pdf` (assinatura `%PDF`) nesta fase — outro conteúdo ⇒ 422; arquivo vai primeiro para `.versoes/_upload/` e é movido pelo pipeline.
- [ ] **Steps:** testes (upload real do Programa → 201 e proposta com 3 unidades; reenvio → 200 mesmo id; `.txt` → 422; PDF corrompido → 422; confirmar → resumo; confirmar de novo → 409; PUT inválido → 422) → RED → implementar → GREEN → commit.

---

### Task 11: Ponta a ponta e reimportação sobre Cálculo 2

**Files:** Create `tests/test_importacao_ponta_a_ponta.py`; Modify `README.md` (seção "Importar materiais")

- [ ] **Steps:**
  1. Teste "matéria nova só com PDFs" (Review Focus 5): cria matéria vazia pela API; envia Stewart, Programa, Calendário, info_S3, exercicios_1/2/3un, Lista5; confirma todas sem editar (exceto as com `revisar`, que o teste aceita como vieram); verifica: 3 unidades com provas 14/09, 19/10, 30/11; ≥ 15 tópicos; tópico "Integrais triplas em coordenadas cilíndricas" ligado a 15.8; listas 14.1…15.10 nas unidades certas e com `lista_secao`; L5 na unidade 3; professor e 6 critérios.
  2. Teste de reimportação (Review Focus 1): copia o Cálculo 2 migrado para `tmp_path`, importa `exercicios_3un.pdf` em modo `mesclar` → nenhuma marcação/questão perdida, contagem de questões ≥ a anterior.
  3. RED → ajustar o que faltar → GREEN; README; commit `test(importacao): ponta a ponta com os PDFs reais`.

---

## Pronto quando

- Suíte verde localmente e no CI.
- Os 13 PDFs de Cálculo 2 classificados corretamente e o teste "matéria nova só com PDFs" verde.
- Reimportar sobre o Cálculo 2 migrado não perde nenhuma marcação.
