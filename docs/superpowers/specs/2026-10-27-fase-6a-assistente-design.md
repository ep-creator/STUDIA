# Fase 6 · Peça A — O assistente (tutor, resumidor e estrategista)

> Base: `2026-10-20-refatoracao-plataforma-design.md` (§11, Fase 6), `2026-10-22-reestruturacao-inteligencia.md` (§1
> princípios, §6 ligação com o agente) e as peças B e B2 (busca, "Ver no livro"). O agente antigo (Gemini com chamadas
> de função, skills em `.md`, tutor N1–N4, conferência numérica, preços e "pacote RAG") saiu com o legado no PR 9; esta
> peça o traz de volta sobre o banco e a busca novos.

## 1. Objetivo e critério de sucesso

O uso principal, nas palavras do usuário: na página da lista, pedir ajuda numa questão e o agente buscar a teoria e o
exercício no livro e nos slides e responder citando; e criar resumos e resoluções.

Sucesso:

1. na questão aberta nas Listas, os atalhos N1–N4 e a conversa livre respondem com base nos materiais da matéria,
   citando de onde veio (links que abrem o PDF na página ou o resumo no bloco);
2. o N4 grava a resolução, "Resumir a seção" grava o resumo e os cartões de fórmula, sempre pelo Histórico (desfazível)
   e com origem `agente`;
3. o custo de cada resposta e o total do mês aparecem no painel, e passar do teto mensal pede confirmação;
4. sem chave do Gemini, o painel continua útil: "Copiar o contexto" monta o pacote para colar em qualquer chat;
5. os testes não chamam a API (modelo falso), e um teste real opcional confere o formato com a chave do usuário.

## 2. Decisões

| Tema | Decisão |
|---|---|
| Interação | Conversa no painel que sabe o que está aberto na tela, com atalhos por cima (escolha do usuário) |
| Gravação | Grava e avisa: na hora, pelo Histórico, com origem `agente`, e a conversa mostra Abrir e Desfazer (escolha do usuário) |
| Memória | Uma conversa por questão, por seção e uma geral; "Recomeçar" arquiva e abre outra (escolha do usuário) |
| Custo | Custo por resposta e total do mês em R$; teto mensal no config pede confirmação (escolha do usuário) |
| Conferência das contas | Calculadora segura com SymPy/SciPy: o modelo envia a conta, o app calcula; nenhum código do modelo é executado (escolha do usuário) |
| Quem busca o material | Abordagem C: o app entrega o contexto óbvio da tela no começo e o modelo tem ferramentas para buscar mais |
| Modelo | Gemini por REST com chamadas de função, atrás de um único módulo (`agente/modelo.py`); trocar de modelo ou de provedor mexe só ali |
| Papéis | Tutor, resumidor e estrategista em arquivos `.md` (instruções e ferramentas permitidas), editáveis sem mexer no código |

## 3. Motor (`_app/backend/estudos/agente/`)

### 3.1 Componentes

| Arquivo | Responsabilidade |
|---|---|
| `modelo.py` | Único ponto que fala com o Gemini: monta a requisição, recebe a resposta aos pedaços (streaming), devolve texto, chamadas de ferramenta e uso de tokens. Interface `Modelo` com implementação real (`Gemini`) e falsa (`ModeloFalso`, para os testes) |
| `contexto.py` | Monta o contexto inicial a partir do alvo da conversa (questão, seção ou geral). Cada pedaço vai marcado com a origem para a citação |
| `ferramentas.py` | As ferramentas que o modelo pode chamar, com a declaração (nome, descrição, parâmetros) e a execução |
| `calculadora.py` | Calculadora segura: integrais (simples, duplas e triplas, com limites), derivadas e parciais, limites, resolução de sistemas, pontos críticos e avaliação numérica, por SymPy/SciPy, a partir de expressões em texto analisadas com gramática restrita (sem `eval` de código) |
| `papeis/*.md` | `tutor.md`, `resumidor.md`, `estrategista.md`: instruções, ferramentas permitidas e modelo padrão no frontmatter (como as skills antigas) |
| `laco.py` | O laço de uma resposta: contexto → modelo → ferramentas → modelo… até a resposta final (máximo de 6 rodadas de ferramentas) |
| `conversas.py` | Guardar e ler conversas e mensagens; custo; total do mês; teto |
| `custo.py` | Tokens → R$ pela tabela de preços do config e pela cotação do dólar |

### 3.2 Contexto inicial (`contexto.py`)

| Alvo | O que entra |
|---|---|
| Questão | enunciado e lista; o exercício original do livro e a resposta do gabarito (`exercicio_de`/`resposta_de`, quando a questão é exercício do livro); os 3 melhores trechos de teoria da seção da lista (busca com o enunciado, `partes=["teoria"]`); o resumo ligado à seção, se houver; a resolução já gravada, se houver |
| Seção (resumidor) | os trechos de teoria da seção no livro principal (`secao_completa`, só teoria) e os slides ligados aos tópicos da seção (busca pelo título da seção, tipo `slides`) |
| Geral (estrategista) | as marcações da unidade (errei e dúvida, com a questão e a seção), a próxima prova e a data, os tópicos da unidade com as seções |

Cada pedaço leva um rótulo de citação: `[Stewart p. 312]`, `[Aula 11 p. 6]`, `[resumo 14.1 — 2. Definições]`,
`[Lista 14.1 #22]`. Com o índice sendo refeito, os trechos do livro ficam de fora e a resposta avisa.

### 3.3 Ferramentas (`ferramentas.py`)

| Ferramenta | O que faz | Grava? |
|---|---|---|
| `buscar` | busca na matéria (teoria, e o grupo de exercícios), com filtro de tipo e unidade | não |
| `ler_secao` | texto da seção do livro (teoria) | não |
| `exercicio_do_livro` | enunciado original e resposta do gabarito de (seção, número) | não |
| `calcular` | calculadora segura (§3.1) | não |
| `salvar_resolucao` | grava a resolução da questão (documento `resolucao`, ligado à questão) | sim |
| `salvar_resumo` | grava o resumo da seção (documento `resumo`, ligado à seção) | sim |
| `adicionar_formula` | cria um cartão de fórmula ligado à seção | sim |

Cada papel declara as ferramentas que pode usar. As que gravam abrem uma ação do Histórico com descrição clara
("Agente: resolução 14.1-22") e origem `agente`; o resultado volta para a conversa como um aviso com Abrir e Desfazer.
Gravar por cima de um documento existente pede que o modelo leia antes (o texto atual vai no contexto) e a nova versão
fica no Histórico como qualquer edição.

### 3.4 Papéis

- **Tutor** (questão): N1 dica (sem contas), N2 caminho (passos sem contas), N3 esboço com lacunas, N4 resolução
  completa no padrão prova (`**Enunciado.**`, `**Resposta.**`, `**Armadilha.**`), gravada com `salvar_resolucao`. Em
  exercício sem gabarito (pares do Stewart), confere as contas com `calcular` e diz se conferiu. A conversa livre
  continua no mesmo fio.
- **Resumidor** (seção): "Resumir a seção" escreve o resumo no formato dos resumos do usuário e cria os cartões de
  fórmula; grava com `salvar_resumo` e `adicionar_formula`.
- **Estrategista** (geral): "Plano de revisão" responde com diagnóstico e plano até a prova; não grava.

### 3.5 Laço de uma resposta (`laco.py`)

1. checa o teto: se o total do mês mais uma estimativa da resposta passa do teto, devolve "confirmar" (a tela pergunta;
   o reenvio com `confirmado=true` segue);
2. monta o contexto inicial e as instruções do papel (e o nível, nos atalhos do tutor);
3. chama o modelo com o histórico da conversa; se ele pede ferramentas, executa e devolve os resultados; repete até a
   resposta final, no máximo 6 rodadas — passou disso, para e avisa "parei para não gastar demais; peça para continuar";
4. o texto vai para a tela aos pedaços; durante uma ferramenta, a tela mostra o que está acontecendo ("Buscando…",
   "Conferindo a integral…");
5. guarda a mensagem com tokens, modelo e custo.

Erro de ferramenta (busca vazia, conta impossível) volta para o modelo como resultado, e ele segue.

## 4. API

| Rota | O que faz |
|---|---|
| `POST /api/materias/{uid}/agente/mensagem` | corpo: `alvo` (`questao:<id>`, `secao:<id>` ou `geral`), `papel`, `texto` ou `atalho` (`N1`…`N4`, `resumir`, `plano`), `confirmado`; resposta em streaming (eventos: `texto`, `ferramenta`, `gravado`, `confirmar`, `erro`, `fim` com tokens e custo) |
| `GET /api/materias/{uid}/agente/conversa?alvo=…&papel=…` | a conversa ativa do alvo (mensagens) |
| `POST /api/materias/{uid}/agente/conversa/recomecar` | arquiva a ativa e abre outra |
| `GET /api/materias/{uid}/agente/contexto?alvo=…&papel=…&atalho=…` | o pacote para "Copiar o contexto" (instruções, contexto e pedido em texto) |
| `GET /api/agente/estado` | chave configurada (sim/não, nunca a chave), modelo, total do mês, teto |
| `PUT /api/agente/chave` | grava a chave em `_app/.segredos.toml` |

## 5. Dados e configuração

- Migração `0006_agente.sql` no `materia.db`:
  - `conversa (id, papel, alvo, ativa, criada_em)`;
  - `mensagem (id, conversa_id, autor, texto, tokens_entrada, tokens_saida, custo_brl, modelo, criada_em)`, com
    `autor` em `voce | agente | ferramenta`.
- As conversas não passam pelo Histórico (são registro, não dados de estudo); o que o agente grava passa.
- O total do mês soma `custo_brl` de todas as matérias do workspace (o teto é do usuário).
- `config.toml`, seção nova `[agente]`: `modelo` (padrão `gemini-3.8-flash`, o mesmo do agente antigo), `teto_mensal_brl`
  (padrão 20), `cotacao_dolar`, `max_rodadas` (6), `tempo_limite_s` (60) e a tabela `[agente.precos]` (modelo →
  entrada e saída por milhão de tokens, em US$).
- A chave fica em `_app/.segredos.toml`, no `.gitignore` (o repositório é público). A API nunca a devolve.

## 6. Interface

O `EspacoIA` (hoje um lugar reservado em dois pontos: o painel lateral "IA" e a área na questão aberta) vira o painel:

- topo: os atalhos do contexto (na questão: N1, N2, N3, N4; numa seção: "Resumir a seção"; no geral: "Plano de
  revisão"), "Recomeçar" e "Copiar o contexto";
- a conversa: mensagens com Markdown e KaTeX; citações `[…]` viram links que abrem o PDF na página ou o resumo no bloco
  (o mesmo mecanismo da busca); avisos de gravação com Abrir e Desfazer; o que a ferramenta está fazendo;
- rodapé: o campo de texto, o custo da última resposta e o total do mês ("R$ 0,04 · mês: R$ 3,20 de R$ 20");
- sem chave: o aviso com como configurar, o campo para colar a chave e "Copiar o contexto".

"Resumir a seção" entra também em Documentos (no resumo ou no livro aberto numa seção), abrindo o painel no alvo da
seção.

## 7. Falhas

| Situação | O que a pessoa vê |
|---|---|
| Sem chave ou chave inválida | aviso, como configurar e "Copiar o contexto" |
| Gemini fora do ar, demora acima de 60 s ou limite de uso | "não consegui falar com o Gemini" com o motivo e "Tentar de novo"; o que já chegou fica |
| Ferramenta falha | o modelo recebe o erro e segue |
| Mais de 6 rodadas de ferramentas | para e avisa |
| Teto do mês | confirmação antes de chamar |
| Índice sendo refeito | contexto sem os trechos do livro, com aviso na resposta |
| Calculadora recebe algo que não é conta | recusa ("expressão inválida"), sem executar nada |

## 8. Testes

- **Laço com `ModeloFalso`** (respostas e chamadas roteirizadas): contexto, ferramentas, gravação pelo Histórico com
  origem `agente` e Desfazer, custo, teto, limite de rodadas, erro de ferramenta, erro do modelo no meio do streaming.
- **Calculadora:** integral dupla em polares, parcial, Lagrange, limite, sistema — contra valores conhecidos; entradas
  maliciosas (`__import__`, `open(`, atributos, lambda) recusadas.
- **Contexto medido pela avaliação existente:** para cada pergunta de questão dos gabaritos, a resposta aceita está no
  contexto inicial? (registrado em `docs/avaliacoes/`, sem custo de API).
- **API:** streaming dos eventos, conversa por alvo, recomeçar, estado sem expor a chave, chave gravada fora do Git.
- **Tela:** painel com streaming simulado; citação vira link; "Resolução salva" com Desfazer; confirmação do teto; sem
  chave mostra "Copiar o contexto".
- **Teste real opcional** (marcado para não rodar por padrão): uma chamada ao Gemini com a chave do usuário.

## 9. Fora de escopo

- Imagens na conversa (foto da resolução para corrigir).
- Peças C (segunda opinião na importação) e D (geração de material em lote).
- Outro provedor de modelo (o `modelo.py` permite, mas só o Gemini entra agora).
- O reordenador da busca (spec própria).
