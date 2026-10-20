# ⚙️ Arquitetura e Funcionamento Interno da Plataforma

Este documento detalha como cada módulo da plataforma funciona por debaixo dos panos e serve como manual de referência para expandir o projeto a longo prazo.

---

## 1. Filosofia do Projeto: Separação entre Operação (0 Tokens) e Inteligência (Agente + RAG)

No modelo antigo, qualquer alteração no site (marcar que uma aula foi dada, destravar uma lista, adicionar exercícios ou editar o cronograma) exigia pedir para uma IA reescrever arquivos HTML/Python gigantes.

Na arquitetura atual:
- **100% dos dados da disciplina vivem em JSONs e Markdowns limpos** (`_app/dados/curso.json`, `_app/dados/exercicios.json`, `status.json`, `resumos/*.md`, `resolucoes/*.md`).
- **O Frontend (`_app/web/app.js`) é um motor de renderização dinâmico** que lê esses JSONs via API e permite editar tudo diretamente na tela com botões nativos (`0 tokens`).
- **A IA (`_app/agente.py` + `_app/rag.py`) só entra em ação quando há trabalho intelectual real** (sintetizar teoria de aulas/livros em resumos, dar dicas graduais em exercícios ou planejar revisão de prova).

---

## 2. Camada de Dados (`_app/dados/` e Raiz da Disciplina)

### 2.1. `_app/dados/curso.json`
Guarda toda a estrutura pedagógica e visual da cadeira:
- **`id`, `nome`, `codigo`, `instituicao`, `semestre`, `subtituloGeral`**: Metadados exibidos no cabeçalho e no seletor Multi-Disciplinas.
- **`provas`**: Lista das provas (`P1`, `P2`, `P3`), datas, pesos e status.
- **`livros`**: Mapa de livros em PDF na pasta `livros/`, incluindo:
  - `offsetPagina`: diferença entre a página impressa do livro e a página real do PDF (`pagina_pdf = pagina_livro + offsetPagina`).
  - `gabaritoPdfInicio` / `gabaritoPdfFim`: intervalo de páginas do PDF onde fica o apêndice de respostas dos exercícios ímpares.
- **`unidades`**: Dicionário (`"1"`, `"2"`, `"3"`) contendo para cada área:
  - `ondeEstamos`: escada de aulas (`status`: `"visto"`, `"atual"`, `"futuro"`) e `secoesExercicios` vinculadas (que são destravadas automaticamente quando a aula é marcada como vista).
  - `cronograma`: blocos e linhas da tabela de estudo com flag `concluido`.
  - `formulario`: cartões de fórmulas rápidas com suporte a LaTeX (KaTeX).
  - `resumos` e `resolucoes`: metadados apontando para os arquivos `.md` nas pastas `resumos/` e `resolucoes/`.

### 2.2. `_app/dados/exercicios.json`
Lista de seções de exercícios (do livro-texto ou de listas do professor):
- **`num`**: identificador da seção (ex.: `"15.4"`, `"L5"`).
- **`title`, `sub`, `unid`, `prio`, `locked`**: metadados, prioridade (`"alta"`, `"media"`, `"apoio"`) e trava (`locked: true` oculta ou recolhe exercícios de aulas futuras até que a aula correspondente seja marcada como vista).
- **`pdfUrl`, `paginaLivro`, `paginaPdf`**: permitem que o botão **`📄 Abrir PDF na pág.`** abra o livro ou a lista exatamente na página dos enunciados (`#page=N`).
- **`items`**: matriz compacta `[numero, enunciado_html, imagem_opcional, dica_ou_nota_opcional]`.

### 2.3. `status.json` e `exercicios/STATUS.md`
- **`status.json`**: mapa chave-valor (`{"15.4-6": "ok", "15.4-16": "dub"}`) onde os estados possíveis são `"ok"` (acertei), `"dub"` (dúvida) e `"err"` (errei).
- **`exercicios/STATUS.md`**: espelho em Markdown gerado automaticamente pelo `servidor.py` toda vez que `status.json` é salvo, permitindo leitura rápida fora do navegador ou pelo Agente.

### 2.4. `.historico_undo.json` (Pilha de Desfazer Automática)
- Antes de qualquer gravação em `curso.json`, `exercicios.json`, `resumos/*.md` ou `resolucoes/*.md` (seja pela interface ou pelo Agente), a função `registrar_backup_undo()` em `agente.py` salva o conteúdo anterior do arquivo em `.historico_undo.json` (até 25 entradas).
- O botão **`↩️ Desfazer`** na barra superior chama `POST /api/undo` e restaura instantaneamente a versão anterior.

---

## 3. Servidor Backend (`_app/servidor.py`)

Servidor HTTP multithread (`ThreadingHTTPServer`) nativo do Python (sem necessidade de Flask/FastAPI), escutando exclusivamente em `127.0.0.1` (padrão porta `8780`, com avanço automático de porta e `SO_EXCLUSIVEADDRUSE` no Windows para evitar conflito com outros servidores locais).

### Principais Rotas da API:

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/api/ping` | Identifica a plataforma (`estudos-desktop`) e o `workspace` ativo |
| `GET` | `/api/disciplinas` | Lista todas as pastas de disciplinas na raiz do projeto |
| `GET` | `/api/dados?disciplina=...` | Carrega `curso.json`, `exercicios.json`, `status.json` e renderiza os `.md` |
| `GET` | `/api/rag/status` | Retorna estatísticas do banco `rag.db` (chunks FTS5 e seções de livros) |
| `GET` | `/arquivos/<disciplina>/<caminho>` | Serve PDFs de `livros/` e `disciplina/` localmente com suporte a `#page=N` |
| `POST` | `/api/status` | Salva marcações (`ok`, `dub`, `err`) e regenera `exercicios/STATUS.md` |
| `POST` | `/api/curso` | Atualiza `curso.json` (com backup Undo) e destrava seções vinculadas |
| `POST` | `/api/exercicios` | Cria novas listas, alterna trava (`toggle_lock`) ou atualiza `exercicios.json` |
| `POST` | `/api/extrair-pdf` | Extrai questões de um PDF de lista (`pdfplumber`) sem gastar tokens de IA |
| `POST` | `/api/disciplinas/nova` | Cria toda a estrutura de pastas e JSONs para uma nova cadeira (`+ Cadeira`) |
| `POST` | `/api/rag/reindexar` | Sincroniza incrementalmente (ou reconstrói) o índice SQLite FTS5 (`rag.db`) |
| `POST` | `/api/rag/buscar` | Executa busca híbrida (Nível 1 + Nível 2 + vizinhos ímpares) e retorna pacote |
| `POST` | `/api/agente/executar` | Executa o Agente Gemini com *Function Calling* (ou gera pacote `0 Tokens`) |
| `POST` | `/api/undo` | Reverte a última alteração feita em JSON ou Markdown |

---

## 4. Motor RAG Estruturado em 2 Níveis (`_app/rag.py`)

O banco SQLite (`_app/dados/rag.db`) evita o erro clássico de fatiar livros de exatas em pedaços arbitrários de 400 palavras (o que quebraria demonstrações e fórmulas no meio). Ele opera em **2 níveis complementares**:

### Nível 1: `secoes_completas` (Leitura Integral de Seção)
- Cada seção catalogada em `exercicios.json` (ex.: `15.4 — Integrais Duplas em Coordenadas Polares`) tem seu texto completo extraído das páginas correspondentes do livro em PDF (`texto_teoria`), do início ao fim da seção, sem limite artificial de palavras.
- Armazena também a bateria de exercícios da seção (`texto_exercicios`) e o recorte do apêndice de respostas (`texto_gabarito`).

### Nível 2: `chunks_fts` (Busca FTS5 com Ranking BM25)
- Indexa unidades semânticas naturais:
  - Seções `##` dos seus resumos (`resumos/*.md`) e resoluções (`resolucoes/*.md`);
  - Exemplos resolvidos individuais dos livros (`EXEMPLO 1`, `EXEMPLO 2`...);
  - Listas e provas antigas em `disciplina/`.

### Estratégia para Exercícios Pares do Stewart (Sem Gabarito Oficial)
O Stewart publica gabarito apenas para exercícios **ímpares**, mas as listas recomendadas pelos professores têm maioria de exercícios **pares**. Quando você pede ajuda em um exercício par (ex.: `15.4 #22`):
1. `consultar_contexto_exercicio("15.4", "22")` detecta que `22` é par;
2. Busca automaticamente o enunciado do `#22`, os enunciados dos **vizinhos ímpares `#21` e `#23`** (que usam a mesma técnica na bateria do Stewart) e o **gabarito oficial do `#21` e `#23`** no apêndice do livro;
3. O Agente resolve o exercício par usando o método calibrado pelos vizinhos ímpares e executa a ferramenta `conferir_calculo_python` (`numpy`/`scipy.integrate.quad`/`dblquad`/`tplquad`) para validar numericamente a resposta analítica antes de te entregar.

---

## 5. Orquestrador do Agente e Sistema de Skills (`_app/agente.py`)

O Agente utiliza um loop de **Multi-Busca com Function Calling** (até 10 turnos de ferramentas por resposta) compatível com os modelos `gemini-3.8-flash` (rápido e econômico para o dia a dia) e `gemini-4-argon` (raciocínio matemático profundo).

### Ferramentas (Tools) Disponíveis para o Agente:
- **Busca e Verificação (Leitura)**:
  1. `buscar_rag(consulta, tipo, secao, top_k)` — Busca BM25 no FTS5.
  2. `ler_secao_livro(secao, incluir_teoria, incluir_exercicios, incluir_gabarito)` — Lê uma seção inteira do livro.
  3. `consultar_contexto_exercicio(secao, numero)` — Traz enunciado + vizinhos ímpares + gabarito + teoria.
  4. `conferir_calculo_python(expressao_python)` — Executa `numpy`/`scipy`/`math` em sandbox local para provar integrais/derivadas numericamente.
  5. `ler_progresso_aluno()` — Lê `status.json`, `curso.json` e contagens de acertos/dúvidas/erros por seção.
- **Ação e Persistência (Escrita com Backup Undo)**:
  6. `salvar_resumo(slug, titulo, subtitulo, unidade, conteudo_markdown)` — Cria/atualiza `.md` em `resumos/` e registra em `curso.json`.
  7. `salvar_resolucao(slug, titulo, subtitulo, unidade, secao, conteudo_markdown)` — Cria/atualiza guia em `resolucoes/` e registra em `curso.json`.
  8. `adicionar_formula(unidade, titulo, subtitulo, linhas)` — Adiciona card de fórmula em `curso.json`.
  9. `propor_ajuste_cronograma(unidade, bloco_indice, novas_linhas, motivo)` — Retorna proposta de ajuste que exige confirmação de 1 clique do usuário na interface.

---

## 6. Guia de Expansão: Como Evoluir o Projeto

### Como adicionar uma nova disciplina
- **Pela Interface**: Clique em **`+ Cadeira`** no topo direito da página, preencha nome, código e semestre. O servidor criará automaticamente a nova pasta irmã com `_app/dados/curso.json`, `_app/dados/exercicios.json`, `resumos/`, `resolucoes/`, `livros/` e `SKILL-DISCIPLINA.md`.

### Como criar uma nova Skill do Agente
1. Crie um arquivo `.md` em `_app/skills/<id-da-skill>.md` com cabeçalho frontmatter simples (`# Nome da Skill`) e as instruções de quais ferramentas o Agente deve chamar e como formatar a saída.
2. Ela aparecerá automaticamente no seletor do modal **`🤖 Agente & RAG`** e na aba de edição de Skills.

### Como adicionar uma nova Ferramenta (Tool) ao Agente
1. Em `_app/agente.py`, adicione a declaração JSON Schema da função na lista `DECLARACOES_TOOLS`.
2. Implemente o handler correspondente dentro de `_executar_tool_call()` em `_app/agente.py`.
