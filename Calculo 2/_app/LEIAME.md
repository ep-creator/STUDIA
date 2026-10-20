# Plataforma Desktop de Estudos — Multi-Disciplinas, RAG Estruturado & Agente com Skills

Uma aplicação desktop (`127.0.0.1:8765`) 100% orientada a dados para gerenciar múltiplas cadeiras da universidade sem gastar tokens de IA em tarefas operacionais.

## Como Abrir

Dê duplo clique em **`abrir.bat`** na pasta raiz (`C:\Antigravity\Refatoração Site Estudos\abrir.bat`) ou em `Calculo 2\_app\abrir.bat`.

## O que mudou na Arquitetura

1. **Zero Tokens em Tarefas Braçais (Edição Direta na Tela):**
   - **Onde estamos:** Clique no selo (`Até 29/10`, `Sex 30/10`, `Visto`) para alternar o status da aula. Quando você marca uma aula como `Visto`, o sistema **destrava automaticamente** a seção de exercícios vinculada.
   - **Cronograma:** Marque o `✓` nas sessões concluídas, edite linhas existentes ou clique em **+ Sessão no Cronograma**.
   - **Listas de Exercícios (`+ Nova Lista / Seção`):** Crie qualquer lista em 5 segundos digitando intervalos (`1..15, *4`) ou extraindo os enunciados direto do PDF com `pdfplumber` (zero tokens).
   - **Formulário:** Adicione ou edite cartões de fórmula direto pela interface.
   - **Múltiplas Disciplinas (`+ Cadeira`):** Crie uma nova disciplina pelo botão no topo; todo o código HTML/JS/Python é genérico e lê `dados/curso.json` + `dados/exercicios.json`.
   - **Backup e Desfazer (`↩ Desfazer`):** Toda escrita cria backup em `_app/dados/.historico_undo.json`.

2. **RAG Estruturado em 2 Níveis (`rag.py` + `dados/rag.db` em SQLite FTS5):**
   - **Nível 1 (`ler_secao_livro`):** Armazena a seção teórica **completa** e todos os Exemplos Resolvidos de cada seção mapeada nos livros (Stewart, Guidorizzi), sem cortes arbitrários de palavras.
   - **Nível 2 (`buscar_rag` via FTS5 BM25):** Indexa unidades semânticas naturais (`resumos/*.md`, `resolucoes/*.md`, `disciplina/*.pdf`, exemplos e apêndices de respostas).
   - **Estratégia para Exercícios Pares do Stewart (Sem Gabarito):** A tool `consultar_contexto_exercicio` busca automaticamente os **vizinhos ímpares (`#n-1` e `#n+1`) e seus gabaritos no apêndice**, e a tool `conferir_calculo_python` executa `numpy`/`scipy` localmente para validar o resultado numérico.

3. **Agente com Skills Modulares (`agente.py` + `_app/skills/*.md` + `SKILL-DISCIPLINA.md`):**
   - Suporta execução direta via API (`gemini-3.8-flash` e `gemini-4-argon` com loop de até 10 passos de Multi-Busca/Function Calling) ou **Modo Empacotar RAG + Skill (Offline · 0 Tokens API)**.
