# Redesenho do STUDIA: Hoje, progresso derivado e 4 áreas — design

**Data:** 2026-11-05 · **Branch:** `redesenho/hoje` (a partir de `ajustes/finais`)
**Origem:** crítica do app inteiro com o Impeccable (23/40, `.impeccable/critique/2026-11-05T21-23-46Z__app-frontend-src.md`).
**Decisões do usuário:** centro da sessão = o plano (Hoje); progresso derivado; estrutura de 4 áreas; visual mantido com as
regras corrigidas. Trabalho autônomo nos 7 passos, com commits; consultar só em decisões importantes não cobertas aqui.

## 1. Problema

O app é organizado pelo que o banco guarda (tópicos, listas, cronograma, documentos, formulário), não pelo que o aluno
faz numa sessão de estudo. A sessão de hoje já está no Cronograma, mas a tela de entrada da matéria mostra uma "próxima
aula" tirada do status manual dos tópicos ("Sem aula — pré-requisitos") e números zerados, porque os três registros
manuais (status do tópico, sessão feita, marcação de questão) não são mantidos.

## 2. Quem e quando (modo Operate)

O autor, no computador, abrindo a matéria para uma sessão de estudo de 1h30–2h30, com livro e lista ao lado. Sucesso:
em segundos saber **o que estudar agora** e chegar ao material (seção, resumo, fórmulas, questões) com um clique.
Secundário: alguém do portfólio vendo o app real.

## 3. Estrutura nova

Barra lateral da matéria:

| Item | Rota (chave interna mantida) | O que é |
|---|---|---|
| **Hoje** | `painel` | casa da matéria (este documento, §4) |
| **Tópicos** | `topicos` | mapa da unidade; cada tópico vira página própria (passo 2) |
| **Praticar** | `listas` | listas e a questão aberta (passo 3) |
| **Biblioteca** | `documentos` | resumos, resoluções, planos, anotações e PDFs |
| ── | | |
| Plano completo | `cronograma` | a linha do tempo inteira (Hoje mostra só 7 dias) |
| Folha de fórmulas | `formulario` | a folha para imprimir |
| **＋ Material** | `importar` | importar PDFs (com o número de pendências) |
| Histórico | `historico` | auditoria e desfazer |

- As chaves de rota não mudam (favoritos antigos continuam valendo); só os nomes visíveis.
- A página **Assistente** sai da barra (passo 4 decide o destino); a IA fica na gaveta "IA ›".
- A linha "CÁLCULO 2 · 2026.2 … 3ª UNIDADE" (moldura) sai: repete a barra lateral e as abas.

## 4. Hoje

De cima para baixo, só o que ajuda a decidir o próximo clique:

1. **Cabeçalho:** "Hoje" + a data por extenso curta; à direita, a prova da unidade ("Prova em 25 dias · seg 30/11"),
   em brasa com 7 dias ou menos (regra já existente).
2. **Sessão de hoje** (o foco da tela): código e título (a parte em negrito do foco do plano, ex. "15.5 Aplicações"),
   o resto do foco em uma linha suave, e o material, cada item um clique:
   - **Livro:** a seção (ex. "15.5 no livro · p. 1012") abre o PDF na página;
   - **Resumo:** o resumo da seção, abre na Biblioteca;
   - **Fórmulas:** as fórmulas da seção (por `secao_id` ou pelo código no título), com o número;
   - **Questões:** os números da sessão (de `sessao_questao`) agrupados por lista, com a marcação e a resolução
     gravada; clicar abre a questão em Praticar.
   - **Ação forte única da tela:** "Começar pelas questões" (abre a primeira questão não trabalhada).
   Sem sessão hoje: "Próxima sessão · sáb 07/11" com o mesmo bloco. Sem plano: uma frase e o atalho para o Plano.
3. **Para revisar:** questões com ✗ ou ? de **todas as unidades**, agrupadas por lista (com a unidade quando não for a
   atual). Clicar abre em Praticar, na unidade certa. Vazio: "Nada para revisar." (sem culpa).
4. **Próximos 7 dias:** sessões e eventos (aula, prova) em linhas curtas: data, código, título, estado. "Plano
   completo →".
5. **Tópicos da unidade:** cada tópico com o estado derivado (§5) e "trabalhadas/total" das questões ligadas, erros em
   vermelho. Clicar leva ao tópico.

**Reta final** (prova da unidade em 7 dias ou menos): entra no topo, antes da sessão, uma faixa curta: dias até a prova,
total para revisar (todas as unidades), tópicos com mais erros primeiro, e "Folha de fórmulas". Não é outra tela.

Saem da casa da matéria: a contagem gigante, "% feito", "Próxima aula" pelo status manual, a lista de desempenho por
lista (fica em Praticar).

## 5. Progresso derivado (motor, `estudos/progresso.py`)

Regras explícitas, conferíveis e sem IA:

- **Questão trabalhada:** tem marcação **ou** tem resolução gravada (`documento.questao_id`).
- **Sessão:** `feita` se marcada à mão **ou** se alguma questão dela foi trabalhada; senão `hoje` (data = hoje),
  `passou` (data < hoje, mostrada neutra, sem cobrança) ou `futura`.
- **Seções de uma sessão:** seções das listas das questões dela (`lista_secao`) + códigos "NN.N" no foco do plano.
- **Tópico:** `visto` se marcado à mão, **ou** coberto por uma sessão com data ≤ hoje, **ou** com alguma questão
  trabalhada; `hoje` se coberto pela sessão de hoje; senão `a seguir`. Um tópico "cobre" uma sessão quando
  compartilham uma seção (`topico_secao`) ou quando a lista da questão está ligada ao tópico (`lista_topico`).
- **Questões de um tópico:** as das listas ligadas a ele ou às suas seções.
- **Fórmula de uma seção:** `formula.secao_id`, ou o código "(NN.N)" no título.

O status manual dos tópicos e o "marcar feita" das sessões continuam existindo (desfazer, histórico), mas deixam de ser
necessários. A marcação de questão continua manual e barata (teclas 1/2/3/0).

Nova rota `GET /api/materias/{uid}/hoje` devolve tudo da tela Hoje numa chamada (sessão em foco com material,
próximos 7 dias, revisar de todas as unidades, tópicos da unidade atual com progresso, prova da unidade, reta final).

## 6. Estados e faixas reais

- Sessões por unidade: 8–14; questões por sessão: 0–14; listas por unidade: 3–8; tópicos: 6–8.
- Matéria sem unidades/sem plano (Sistemas Digitais, Geometria Analítica): Hoje mostra o primeiro passo
  ("Adicionar material") — o passo 5 (onboard) refina.
- Sessão sem questões (simulado, revisão): mostra só foco e material das seções.
- Seção sem resumo/fórmula: o item some (não mostra "0 fórmulas").

## 7. Fora deste passo

Página de tópico (passo 2), Praticar (passo 3), IA única e importação que falha (passo 4), matéria vazia (passo 5),
tipografia dos rótulos e largura de leitura (passo 6), polimento (passo 7).

## 8. Restrições

- Visual do DESIGN.md (papel, Fraunces + Inter, um laranja, sem caixas); nada de cartões.
- Português, desktop, teclado: tudo alcançável com Tab, foco visível, títulos reais (h1/h2) na tela.
- Testes primeiro no motor (pytest) e na interface (vitest); nenhum teste antigo quebrado sem motivo.
