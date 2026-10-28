# A ideia do projeto

[← README](../README.md) · [Guia de uso](guia.md) · **A ideia do projeto** · [Tecnologia e evolução](tecnologia.md)

---

## O experimento

O STUDIA é um experimento: **construir uma plataforma inteira só conversando com uma IA.** Ninguém escreveu o código à
mão. O autor (Enzo Priori, estudante) decidiu o que queria, aprovou cada desenho e testou as telas; a IA (Claude, no
Claude Code) escreveu todo o código, os testes e a documentação.

Isso costuma ser chamado de *vibe coding*. A proposta aqui foi levar a ideia até o fim, num software de uso diário de
verdade, e não num protótipo: com banco de dados, importação de PDFs, busca, um assistente de IA, centenas de testes e
uma interface pensada tela por tela.

## O problema que ele resolve

Estudar uma disciplina de exatas é juntar muita coisa espalhada: o programa e o calendário da turma, um ou dois livros,
listas de exercícios, slides, as próprias anotações. Saber o que cai na prova, o que já foi feito e o que precisa ser
revisado vira um trabalho em si.

O STUDIA junta tudo isso por matéria e por unidade:

- você solta os PDFs, e ele monta sozinho as unidades, as datas, os tópicos, as listas e as seções do livro;
- você marca as questões que acertou, errou ou ficou em dúvida, e ele mostra o que revisar;
- um assistente ajuda a resolver questões em níveis (da dica à resolução completa), escreve resumos e monta um plano
  de revisão, sempre citando de onde tirou cada coisa.

Tudo roda no próprio computador, e os dados ficam em arquivos na pasta do projeto.

## Os princípios

Algumas regras guiaram todas as decisões:

1. **Organizar não depende de IA.** Criar uma matéria e ligar as peças é feito por regras explícitas, que dá para
   entender e conferir. A IA entra só no que exige raciocínio: explicar, resolver, resumir, planejar.
2. **Nada é adivinhado.** Toda decisão automática tem origem e uma nota de confiança; quando o app não tem certeza, ele
   pergunta em vez de gravar.
3. **Medir antes de trocar.** Uma técnica nova só entra se ganhar da atual num gabarito de casos reais. Foi assim que
   os embeddings ficaram desligados (veja [Tecnologia e evolução](tecnologia.md)).
4. **Tudo se desfaz.** Toda alteração, sua ou do assistente, vai para o histórico e pode ser desfeita.
5. **Local e barato.** O que roda a cada busca ou importação roda offline. A API paga só para o que precisa de raciocínio,
   com o custo à vista e um teto mensal.
6. **Útil antes de bonito, e bonito do jeito simples.** Na visão geral, só o que ajuda a decidir o próximo clique; o
   detalhe fica para quando você abre o item.

## Como uma plataforma inteira foi construída conversando

Cada fase seguiu o mesmo ciclo, sempre com o autor aprovando antes do passo seguinte:

1. **Conversa de desenho.** A IA pergunta o objetivo, propõe caminhos com prós e contras e mostra esboços das telas no
   navegador. O autor escolhe.
2. **Especificação.** O desenho aprovado vira um documento (`docs/superpowers/specs/`), que o autor revisa.
3. **Plano.** A especificação vira um plano de tarefas pequenas, cada uma com os testes que provam que ficou pronta
   (`docs/superpowers/plans/`).
4. **Execução com testes primeiro.** Para cada tarefa, a IA escreve o teste, vê falhar, escreve o código e vê passar.
5. **Revisão.** No fim de cada fase, um revisor novo (outra instância da IA, sem o contexto da conversa) lê o trabalho
   inteiro e aponta problemas; os importantes são corrigidos, cada um com um teste.
6. **Uso de verdade.** O autor usa o app, manda capturas de tela e diz o que incomoda; os ajustes entram antes do merge.

Esse ciclo é o que permitiu ir longe sem perder o controle: o autor não precisava ler o código, mas lia e aprovava
cada decisão, e os testes garantiam que o que já funcionava continuava funcionando.

## Números

Em 9 dias (20 a 28 de outubro de 2026):

- 7 fases de refatoração, 14 pull requests;
- mais de 150 commits;
- cerca de 620 testes no motor, 180 na interface e 6 de ponta a ponta;
- cada fase com especificação e plano escritos, e as decisões técnicas medidas em `docs/avaliacoes/`.

## De onde veio

Antes desta refatoração havia uma primeira versão, feita só para Cálculo 2: um app com os dados num arquivo JSON, um
agente que buscava em tudo e um índice de busca próprio. Ela funcionava, mas tudo era específico daquela disciplina
(números de seção, nomes de livros, quantidade de unidades escritos no código). A refatoração começou com uma pergunta:
dá para transformar isso numa plataforma para qualquer matéria, em que a organização sai das regras e não da IA? A
resposta está nas [fases](tecnologia.md#a-evolução).
