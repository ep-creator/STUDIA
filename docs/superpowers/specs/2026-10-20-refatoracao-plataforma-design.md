# Refatoração da Plataforma de Estudos — Especificação de Arquitetura

> Data: 2026-10-20 · Status: aprovada para planejamento · Autor: Enzo Priori + Claude
> Planos de implementação derivados: `docs/superpowers/plans/2026-10-20-fase-*.md`

## 1. Objetivo

Transformar a plataforma num software multi-disciplina robusto em que **criar e organizar uma matéria não exige IA**:
o usuário cria a matéria pela interface, envia os arquivos (programa, calendário, informações da turma, livros,
listas, slides, anotações) e a plataforma **classifica, extrai, vincula e indexa tudo por regras explícitas**,
mostrando uma tela de revisão antes de gravar. A IA fica restrita às tarefas intelectuais (tutor, resumos,
revisão) e é redesenhada numa fase posterior — esta refatoração só a adapta ao novo modelo de dados.

### Princípios (valem para todas as fases)

1. **Nada é adivinhado em tempo de leitura.** Toda informação estrutural (unidade, seção, livro, página, linha 1/2)
   é decidida **uma vez**, na importação ou edição, e gravada como dado. Leitura nunca infere.
2. **Regras, não valores fixos.** Nenhum dado de uma disciplina específica no código (sem mapa `14.1→1`, sem `"stewart"`,
   sem `"15.4"` como padrão, sem limiares de prefixo de arquivo, sem "3 unidades"). Tabelas de linguagem
   (ordinais "Primeira"→1, dias da semana) são permitidas: são regras do idioma, não da disciplina.
3. **Toda inferência tem origem e confiança.** Dado extraído carrega `origem` (`importado` | `manual` | `agente` | `migrado`)
   e, quando inferido, `confianca` (0–1). Abaixo do limiar configurado, exige confirmação na revisão.
4. **Uma fonte de verdade por dado.** Dados estruturados no SQLite da matéria; conteúdo longo (resumos, resoluções,
   planos, anotações) em Markdown com frontmatter. Sem espelhos (`STATUS.md`, listas repetidas em `.md`).
5. **Escritas atômicas e reversíveis.** Toda alteração passa por uma transação que registra o histórico para desfazer.
6. **Seguro por padrão.** API só aceita requisições locais (Host/Origin), JSON validado, caminhos verificados com
   `Path.is_relative_to`, Markdown sanitizado na renderização.

## 2. Decisões tomadas

| Tema | Decisão |
|---|---|
| Armazenamento | SQLite por matéria (`materia.db`) para dados estruturados + índice RAG; arquivos para PDFs e Markdown |
| Backend | Python 3.13 + FastAPI + Pydantic v2 + Uvicorn |
| PDF | PyMuPDF (`pymupdf`) substitui pdfplumber |
| Frontend | Svelte 5 + Vite + TypeScript; markdown-it + KaTeX + DOMPurify |
| Unidades | Inferidas do Programa + Calendário por regras; edição manual sempre disponível |
| Livros | Sumário detectado pelos marcadores do PDF, com fallback para a página "Sumário"; offset calculado; revisão do usuário |
| Listas | Parser de questões numeradas e de "Seção X / linha 1 / linha 2"; IDs estáveis por questão |
| Slides/anotações | Indexados no RAG e vinculados a seções/unidades indicadas na importação; não geram conteúdo sozinhos |
| Agente | Continua Gemini + function calling; nesta refatoração só troca o acesso a dados (Fase 6) |
| Migração | Cálculo 2 migrado integralmente (marcações, resumos, resoluções, cronograma, fórmulas, livros) |

## 3. Layout do workspace

```text
Refatoração Site Estudos/
├── abrir.bat                      # inicia o novo servidor (e, até a Fase 7, oferece o legado)
├── _app/                          # MOTOR (ignorado pela descoberta de matérias por começar com "_")
│   ├── config.toml                # host, porta, limiares de confiança, retenção do histórico
│   ├── skills/                    # skills globais do agente (movidas de Calculo 2/_app/skills)
│   ├── backend/
│   │   ├── pyproject.toml
│   │   ├── estudos/               # pacote Python (ver §4)
│   │   └── tests/
│   └── frontend/                  # Svelte + Vite; build em _app/frontend/dist servido pelo FastAPI
├── legado/                        # app antigo congelado até paridade (removido na Fase 7)
└── Calculo 2/                     # MATÉRIA = só dados
    ├── materia.db
    ├── fontes/
    │   ├── documentos/            # programa, calendário, info da turma
    │   ├── livros/
    │   ├── listas/
    │   ├── slides/
    │   ├── provas/
    │   └── anotacoes/
    ├── conteudo/
    │   ├── resumos/*.md
    │   ├── resolucoes/*.md
    │   ├── planos/*.md
    │   ├── anotacoes/*.md
    │   └── contexto.md            # perfil do estudante + observações livres (antigo SKILL-DISCIPLINA, parte manual)
    ├── figuras/                   # imagens de questões
    └── .versoes/                  # versões anteriores de arquivos .md (para desfazer)
```

**Convivência até o corte (Fase 5):** a matéria nova e as pastas do app legado ficam na mesma pasta (ex.: `Calculo 2/` tem
`resumos/`, `_app/` etc. do legado **e** `materia.db`, `fontes/`, `conteudo/` do motor novo). PDFs e figuras entram por
**hardlink** (mesmo arquivo, sem espaço extra); o legado continua lendo os seus caminhos. A pasta `legado/` só é criada no corte.
A migração (`python -m estudos.migracao`) reconstrói a matéria nova a partir do legado quantas vezes for preciso e grava
`.migracao/relatorio.md`.

Uma pasta do workspace é matéria **se e somente se** contém `materia.db`. Nome da pasta = nome de exibição inicial;
o identificador estável é `materia.id` dentro do banco, nunca o nome da pasta.

## 4. Backend — módulos e responsabilidades

```text
estudos/
├── main.py              # create_app(settings) -> FastAPI; monta routers, middleware, estáticos
├── config.py            # Settings (carrega _app/config.toml; defaults num único lugar)
├── seguranca.py         # middleware Host/Origin local; caminho_seguro(base, rel)
├── workspace.py         # descobrir_materias, criar_materia, abrir_materia
├── db/
│   ├── conexao.py       # conectar(caminho) com PRAGMAs; transacao(); aplicar_migracoes()
│   └── migracoes/0001_inicial.sql, 0002_*.sql …
├── modelos.py           # modelos Pydantic de domínio e de API
├── repos/               # acesso a dados por agregado, sempre dentro de transação
│   ├── materia.py  unidades.py  eventos.py  topicos.py
│   ├── fontes.py   livros.py    listas.py   marcacoes.py
│   ├── cronograma.py  formulas.py  documentos.py  criterios.py
├── historico.py         # registrar mudanças (linhas e arquivos) e desfazer
├── conteudo.py          # leitura/escrita de .md com frontmatter + versões em .versoes/
├── importacao/
│   ├── pdf.py           # wrapper PyMuPDF: texto limpo por página, outline, metadados, cabeçalhos repetidos
│   ├── classificador.py # tipo do arquivo + confiança
│   ├── parsers/programa.py  calendario.py  turma.py  livro.py  lista.py  slides.py
│   ├── vinculo.py       # tópico ↔ seção; lista ↔ tópicos; documento ↔ seção (similaridade de texto)
│   └── pipeline.py      # proposta (rascunho) → revisão → confirmação → gravação + indexação
├── rag/
│   ├── indexador.py     # sincronização incremental por fonte/documento (inclui remoção)
│   └── busca.py         # BM25 + filtros por unidade/seção/tipo
├── agente/              # (Fase 6) agente atual adaptado: tools chamam repos e rag
└── api/                 # routers finos: validação Pydantic → repos/pipeline
    ├── materias.py  unidades.py  topicos.py  listas.py  marcacoes.py  cronograma.py
    ├── formulas.py  documentos.py  importacao.py  rag.py  historico.py  arquivos.py  agente.py
```

Regras de dependência: `api → repos/pipeline/rag → db`. Repos não conhecem HTTP; parsers não conhecem banco
(recebem texto e devolvem dataclasses); `pipeline` é o único que junta parser + vínculo + repos.

## 5. Modelo de dados (SQLite por matéria)

Convenções: PK `id INTEGER`; datas ISO-8601 (`TEXT`); `origem TEXT CHECK (origem IN ('importado','manual','agente','migrado'))`;
`confianca REAL NULL`; `PRAGMA foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout=5000`.

| Tabela | Colunas principais | Observações |
|---|---|---|
| `schema_versao` | `versao` | controlada pelo runner de migrações |
| `materia` | `id, uid, nome, periodo, instituicao, professor, email_professor, criada_em` | 1 linha; `uid` (uuid4 hex) é o identificador da matéria no workspace e na API |
| `unidade` | `id, numero, titulo, origem, confianca` | `numero` único; quantidade livre |
| `evento` | `id, tipo, data, hora_inicio, hora_fim, unidade_id?, descricao, origem` | `tipo ∈ aula, prova, segunda_chamada, exame_final, extra, feriado`; data da prova = evento `prova` da unidade |
| `horario_aula` | `id, dia_semana, hora_inicio, hora_fim` | vindo do info da turma |
| `topico` | `id, unidade_id, pai_id?, ordem, titulo, status, origem, detalhe_md` | `status ∈ pendente, proxima, visto`; hierarquia ○/• do programa; substitui "Onde estamos" |
| `fonte` | `id, tipo, caminho, sha256, titulo, paginas, importada_em, origem` | `tipo ∈ programa, calendario, turma, livro, lista, slides, prova, anotacao, outro`; `sha256` único (evita duplicata) |
| `livro` | `fonte_id, papel, autor, titulo_obra, edicao, offset_pagina, gabarito_pdf_ini?, gabarito_pdf_fim?` | `papel ∈ principal, complementar` (da bibliografia) |
| `secao_livro` | `id, livro_id, codigo, titulo, nivel, pagina_pdf_ini, pagina_pdf_fim, origem, confianca` | `codigo` "15.8", "8" etc.; `UNIQUE(livro_id, codigo)` |
| `secao_equivalente` | `secao_id, equivalente_id` | seções equivalentes entre livros (Guidorizzi cap. 8 ↔ Stewart 14.1), gravadas nos dois sentidos |
| `topico_secao` | `topico_id, secao_id, confianca, confirmado` | vínculo programa ↔ livro |
| `lista` | `id, codigo, titulo, unidade_id, fonte_id?, liberacao, ordem, origem` | `liberacao ∈ auto, aberta, travada` |
| `lista_secao` | `lista_id, secao_id` | seções que a lista cobre |
| `lista_topico` | `lista_id, topico_id` | tópicos que a lista cobre (de "Conteúdos:" ou da seção) |
| `questao` | `id, lista_id, rotulo, ordem, linha, enunciado_md, expressao, pagina_pdf?, figura?, chave_legada?` | `linha ∈ 1,2`; `UNIQUE(lista_id, rotulo)` |
| `marcacao` | `questao_id PK, estado, atualizado_em` | `estado ∈ ok, err, dub` |
| `sessao_estudo` | `id, unidade_id, codigo, data, foco_md, feito, ordem, origem` | cronograma |
| `sessao_questao` | `sessao_id, questao_id` | exercícios da sessão (substitui colunas "x" livres) |
| `formula` | `id, unidade_id, secao_id?, titulo, corpo_tex, notas_md, ordem, origem` | |
| `documento` | `id, tipo, caminho, titulo, unidade_id?, secao_id?, questao_id?, origem, atualizado_em` | `tipo ∈ resumo, resolucao, plano, anotacao, contexto`; espelha o frontmatter do .md; `unidade_id` NULL = vale para todas |
| `documento_unidade_extra` | `documento_id, unidade_id` | unidades adicionais em que o documento aparece |
| `nota_avaliacao` | `unidade_id PK, nota, registrada_em` | nota como dado, não como tag |
| `criterio_correcao` | `id, ordem, texto, origem` | do info da turma; alimenta o agente |
| `historico_grupo` | `id, momento, descricao, desfaz_grupo?, desfeito_em?` | uma ação do usuário; ver §7 |
| `historico_mudanca` | `id, grupo_id, ordem, tabela?, chave_json?, antes_json?, depois_json?, arquivo?, versao_arquivo?` | linhas ou arquivos alterados no grupo |
| `chunk` + `chunk_fts` | `id, fonte_id?, documento_id?, secao_id?, unidade_id?, tipo, titulo, texto, pagina` | FTS5 external-content; ver §8 |
| `importacao` | `id, fonte_id, estado, proposta_json, criada_em, confirmada_em?` | rascunhos aguardando revisão |

### Regras derivadas (calculadas, nunca armazenadas)

- **Data da prova da unidade** = `evento.data` onde `tipo='prova' AND unidade_id=u`.
- **Lista aberta** = `liberacao='aberta'` OU (`liberacao='auto'` E existe `lista_topico`/`lista_secao→topico_secao` cujo tópico tem `status='visto'`).
  Desmarcar o tópico volta a travar. A trava manual (`aberta`/`travada`) tem precedência.
- **Unidade atual** = menor `numero` cuja prova é ≥ hoje; se nenhuma, a última.
- **Placar** = contagem de `marcacao` por estado nas questões de listas abertas da unidade; taxa de acerto =
  `ok/(ok+err)`, dúvidas exibidas à parte (regra explícita na UI).

## 6. Pipeline de importação

```text
upload → fonte (sha256, cópia para fontes/<tipo>/) → classificar → extrair (parser do tipo)
      → vincular (regras de similaridade) → PROPOSTA (importacao.proposta_json)
      → tela de revisão (itens com confiança < limiar destacados; tudo editável)
      → confirmar → gravação transacional (repos + historico) → indexação RAG
```

A proposta nunca toca as tabelas de domínio; só `confirmar` grava. Reimportar o mesmo arquivo (mesmo `sha256`)
abre a proposta existente. Reimportar uma versão nova de uma lista faz upsert por `(lista_id, rotulo)`,
preservando marcações.

### 6.1 Classificador (`classificador.py`)

Pontua cada tipo com sinais das 2 primeiras páginas + metadados; escolhe o maior; `confianca = margem normalizada`.

| Tipo | Sinais |
|---|---|
| `programa` | título "Programa"/"Ementa"; ≥2 cabeçalhos de unidade; marcadores ○/• |
| `calendario` | título "Calendário"; ≥6 datas `dd/mm`; linhas "exame"/"prova" |
| `turma` | seções "Avaliação", "Referência", "Horário"; e-mail |
| `livro` | ≥100 páginas; outline com códigos numéricos ou página "Sumário" |
| `lista` | "Lista"/"Exercícios" no título; ≥3 linhas `^\d+[.)]` ou blocos "Seção X.Y" |
| `slides` | páginas em paisagem (largura > altura) em ≥80% das páginas; pouco texto por página |
| `prova` | "Exame"/"Prova"/"Avaliação" no título + questões numeradas + < 10 páginas |

### 6.2 Parsers (entradas e saídas puras)

- **Programa** → `[UnidadeExtraida(numero, titulo, topicos=[TopicoExtraido(titulo, filhos=[...])])]`.
  Cabeçalho de unidade: `^(?P<ord>Primeira|Segunda|…|Décima|\d+[ªaº]?)\s+Unidade` ou `^Unidade\s+(?P<n>\d+|[IVXLC]+)`
  (tabela de ordinais por extenso + romanos). Nível 1: linhas iniciadas por `○ ◦ o ▪`; nível 2: `• - –`; demais linhas
  continuam o item anterior.
- **Calendário** → aulas e provas por unidade. Cabeçalhos de unidade: mesma regra do programa. Datas `\b(\d{1,2})/(\d{1,2})\b`
  com anotação opcional `\((?P<obs>[^)]*)\)` (ex.: "sábado, 10h-12h" → `extra` com horário). Linhas de prova:
  `(?P<ord>…)\s+exame|prova` + `:\s*dd/mm(,\s*HHhMM-HHhMM)?`; "Segunda chamada", "Exame final" → tipos próprios.
  Ano: primeiro `20\d\d` do cabeçalho; semestre `-1`/`-2`/`.1`/`.2` resolve virada de ano.
- **Turma** → professor (linha com e-mail), horários (`(Segunda|Terça|…)[-\s]feiras?:\s*HHh-HHh`), bibliografia
  (linhas sob "Referência"/"Referências complementares": a primeira seção vira `papel=principal`), critérios de correção
  (marcadores sob a frase que contém "critérios de avaliação").
- **Livro** → `SecaoExtraida(codigo, titulo, nivel, pagina_pdf_ini)`:
  1. Outline do PDF: entradas cujo título casa `^(?P<cod>\d+(\.\d+)*)\s*[-–.]?\s*(?P<tit>.+)`.
  2. Fallback: páginas cujo texto contém "Sumário"/"Índice"; linhas `^(cod)\s+(tit)\s+(\d+)$` (página impressa).
  3. **Offset**: amostra de páginas; número impresso = inteiro isolado na 1ª ou última linha; `offset = moda(pagina_pdf − impressa)`.
  4. `pagina_pdf_fim` = início da próxima seção do mesmo nível − 1.
  5. Gabarito: seção/entrada cujo título casa `Respostas|Gabarito|Answers`.
  6. Remove cabeçalhos/rodapés repetidos (linha idêntica em ≥30% das páginas após normalizar dígitos), como `Calculo15B:calculo7 … Page 922`.
- **Lista** → questões. Dois formatos:
  - *Por seção* (ex.: `exercicios_3un.pdf`): bloco `Seção (?P<cod>\d+(\.\d+)*)`, seguido de linhas-marcador; 1º marcador = linha 1,
    2º = linha 2; números separados por vírgula com itens `38(a)` e observações `20(primeira parte)` preservadas no rótulo.
    A linha "J. Stewart, Cálculo…" vincula ao livro da bibliografia.
  - *Enunciados numerados* (listas UFPE): `^\s*(\d{1,3})\s*[.)]\s+` inicia questão; `\(([a-z])\)` vira subitem;
    linha "Conteúdos:" alimenta `lista_topico` via `vinculo`. Linha padrão = 1 (editável na revisão).
- **Slides** → texto por página → chunks; seções/unidade escolhidas na importação (pré-selecionadas por `vinculo`).

### 6.3 Vínculo por similaridade (`vinculo.py`)

`normalizar(t)`: minúsculas, sem acentos, sem pontuação, sem stopwords PT; `similaridade(a,b)` = Jaccard de tokens com
peso extra para tokens raros (IDF sobre o conjunto de títulos do livro). Para cada tópico, a seção de maior
similaridade é proposta se ≥ `limiar_vinculo` (config); empate ou valor abaixo do limiar → "não vinculado" na revisão.
Unidade de lista/documento proposta = unidade majoritária dos tópicos vinculados às suas seções.

## 7. Histórico e desfazer

- Toda escrita de domínio roda em `with historico.operacao(con, "descrição") as op:`; os repos chamam
  `op.registrar(tabela, chave, antes, depois)`; escrita de arquivo chama `op.registrar_arquivo(caminho)`, que copia a versão
  anterior para `.versoes/<caminho>/<timestamp>.md`.
- Desfazer atua no **grupo** mais recente (uma ação do usuário = um grupo, mesmo que toque várias linhas/arquivos)
  e é registrado como novo grupo (`desfaz_grupo`); o grupo original recebe `desfeito_em`. Refazer fica para depois da Fase 5.
- Marcações ✓/✗/? também entram no histórico.
- Retenção configurável (`historico_max_grupos`, padrão 500); versões de arquivo podadas junto.

## 8. RAG

- Unidades indexáveis: seções de livro (texto integral da faixa de páginas, dividido em teoria/exemplos/exercícios),
  páginas de listas/provas/slides, blocos `##` de documentos Markdown.
- Livros são indexados **na importação**, por seção (não mais sob demanda).
- Sincronização incremental por `fonte.sha256` / `documento.atualizado_em`, com **remoção** de chunks de fontes e documentos
  apagados. Reindexação completa não perde nada (sempre derivável).
- Cada chunk carrega `secao_id` e `unidade_id` (via `topico_secao`), permitindo filtros exatos em vez de `LIKE`.
- Limpeza de texto: cabeçalhos repetidos (§6.2), ligaduras, acentos LaTeX combinantes, `(cid:N)`.

## 9. API (resumo)

Prefixo `/api/materias/{materia_uid}/…`. CRUD de unidades, eventos, tópicos, listas/questões, marcações, cronograma,
fórmulas, documentos; `POST …/importacoes` (upload multipart) → proposta; `GET/PUT …/importacoes/{id}` (revisão);
`POST …/importacoes/{id}/confirmar`; `POST …/historico/desfazer`; `GET …/rag/busca`; `GET /arquivos/{materia_id}/{caminho}`
(com `caminho_seguro`). `GET /api/materias/{id}/painel?unidade=N` agrega o que a tela inicial precisa (substitui
`/api/dados`, sem enviar o corpo de todos os .md — o conteúdo é buscado sob demanda).

## 10. Frontend

Svelte 5 + Vite + TS. Telas: seletor de matéria / nova matéria; painel da unidade (cabeçalho, tópicos, cronograma,
listas com marcação, formulário); leitor de documentos (Markdown + KaTeX, sanitizado); importação (upload,
revisão com destaques de confiança); histórico; agente (porta do painel atual). Textos de apresentação ("1ª unidade",
"Cronograma — 1ª unidade") são gerados pela UI a partir do número, não armazenados.

## 11. Fases

| Fase | Entrega | Critério de pronto |
|---|---|---|
| 1. Fundação do backend | `_app/backend` com config, segurança, workspace, SQLite+migrações, repos, histórico, API CRUD básica, testes | `pytest` verde; servidor sobe em porta própria ao lado do legado |
| 2. Migração de Cálculo 2 | `estudos.migracao`: legado → `materia.db` + `fontes/` (hardlink) + `conteudo/` com frontmatter, por regras explícitas | `relatorio.bate()` e teste com os dados reais verdes; legado intacto (o congelamento em `legado/` passa para a Fase 5) |
| 3. Importação por regras | `pdf.py`, classificador, parsers, vínculo, pipeline, rotas de revisão | os PDFs reais de Cálculo 2 viram propostas corretas (testes com fixtures reais) |
| 4. RAG novo | indexador incremental com remoção, livros por seção, busca filtrada | buscas de referência retornam as seções esperadas; reindexação idempotente |
| 5. Frontend novo | Svelte com todas as telas e KaTeX | paridade de uso diário com o legado; criar matéria nova só com cliques |
| 6. Agente adaptado | tools do agente sobre repos/rag; preços/câmbio em config | os fluxos tutor/resumidor/estrategista funcionam sobre o novo banco |
| 7. Limpeza | remover `legado/`, atualizar README e docs | nenhum código morto; docs descrevem o pipeline real |

Fases 3 e 4 dependem de 1; 2 depende de 1 (e usa o parser de livro da 3 opcionalmente — a migração lê o sumário já
existente em `curso.json`); 5 depende de 1–4; 6 depende de 4.

## 12. Fora de escopo (desta refatoração)

Redesenho da interação com a IA (será tratado depois, por decisão do usuário); OCR de anotações manuscritas;
sincronização em nuvem; múltiplos usuários.
