# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

App web local (Svelte 5 + Vite servido pelo motor FastAPI em `http://127.0.0.1:8790`), aberto no navegador do Windows. Uso só no computador; celular não é alvo. Um "app do Windows" (atalho que abre o Edge em modo aplicativo) é ideia futura e não muda a plataforma.

## Users

- **Principal: o autor (Enzo Priori), estudante de exatas**, no dia a dia da faculdade, com Cálculo 2 e Geometria Analítica. Usa no computador, numa sessão de estudo com o livro e a lista abertos. O trabalho: saber o que cai na prova, o que já fez, o que errou e o que revisar, e conseguir ajuda numa questão sem sair do lugar.
- **Secundário: quem vê o portfólio.** O STUDIA também é vitrine do projeto (README com capturas de tela, e futuramente o domínio .com.br do portfólio). As telas precisam se sustentar quando vistas por alguém de fora, mas sem virar página de marketing: a vitrine é o próprio app em uso.
- **Futuro, não alvo agora:** amigos da faculdade com contas, se o app for hospedado. Não desenhar para eles ainda.

## Product Purpose

Juntar por matéria e por unidade tudo o que uma disciplina de exatas espalha (programa, calendário da turma, livros, listas, slides, anotações) e mostrar o que revisar. O usuário solta os PDFs; o app monta unidades, datas de prova, tópicos, questões e seções do livro por regras, pede conferência no que não tem certeza, e acompanha acertos, erros e dúvidas. Um assistente (Gemini) ajuda nas questões em níveis, escreve resumos e monta plano de revisão, citando a fonte.

Sucesso: abrir o app e saber em segundos o próximo passo de estudo, e chegar na prova com o que errou já revisado.

## Positioning

- **Organizar não depende de IA.** A estrutura da matéria sai de regras explícitas e conferíveis, com origem e nota de confiança; a IA entra só no que exige raciocínio.
- **Ajuda graduada, não resposta pronta.** N1 dica, N2 caminho, N3 esboço, N4 resolução completa (gravada), sempre com o exercício original, a teoria da seção e o resumo do aluno no contexto, citando de onde tirou.
- **Local e no controle do aluno.** Roda no próprio computador, dados em arquivos na pasta do projeto, tudo se desfaz, custo da API à vista com teto mensal.
- **Construído inteiro conversando com uma IA**, com o autor aprovando cada passo. Faz parte da história do portfólio.

## Operating Context

- Sessões de estudo no computador, ao lado do livro (PDF) e da lista de exercícios.
- Fluxo típico: Importar PDFs → conferir e confirmar → Painel da unidade → Listas (marcar Acertei/Errei/Dúvida, pedir ajuda N1–N4) → Para revisar antes da prova.
- Telas: Matérias (início), Painel, Tópicos, Listas, Cronograma, Documentos (Markdown com fórmulas), Formulário (para imprimir), Importar, Histórico, Assistente (página e gaveta).
- Atalhos existentes: Ctrl K (busca na matéria, abre o PDF na página certa), Ctrl Z (desfazer).
- Ciclo de trabalho do projeto: conversa de desenho com esboços → spec em `docs/superpowers/specs/` → plano → testes primeiro → revisão → uso real com capturas de tela.

## Capabilities and Constraints

- Uma pasta por matéria na raiz (`materia.db`, `fontes/`, `conteudo/`); essas pastas ficam fora do Git e só existem no PC do autor.
- Single-user, só aceita requisições locais. Interface toda em português (pt-BR).
- Importação por regras com nota de confiança; nada é gravado sem confirmação. Toda alteração (do usuário ou do assistente) vai para o histórico e pode ser desfeita.
- Embeddings ficaram desligados por medição (`docs/avaliacoes/`); técnicas novas só entram se ganharem num gabarito real.
- Assistente: Gemini com chave do Google AI Studio, modo de demonstração sem chamar a API, custo por resposta e teto mensal.
- **Em aberto:** os vínculos tópico ↔ seção ↔ documento são feitos por regras provisórias; outra tecnologia pode ser avaliada. Hospedagem com contas é plano futuro, não iniciado.

## Brand Commitments

- Nome: **STUDIA**.
- Voz: português direto e curto, sem jargão. Estado vazio é uma frase curta ("Nada para revisar ainda."); ajuda longa vai para o detalhe, não para a tela.
- **Menos texto na tela:** na visão geral, só assunto e números, o que ajuda a decidir o próximo clique; enunciados, legendas e referências ficam para quando o item é aberto. Nenhuma função some; o que é raro fica a um gesto (hover, menu "···").
- Linguagem visual já aprovada pelo autor no redesenho minimalista (`docs/superpowers/specs/2026-10-28-redesenho-minimalista-design.md`), com tema Editorial claro e escuro. É a identidade vigente.

## Evidence on Hand

- Capturas de tela reais em `docs/imagens/` (Listas, Importar, Painel, gaveta e página do Assistente, tema claro), usadas no README.
- Documentação: `README.md`, `docs/guia.md`, `docs/ideia.md`, `docs/tecnologia.md`; specs e planos em `docs/superpowers/`; medições em `docs/avaliacoes/`.
- Números do projeto (de `docs/ideia.md`): 9 dias, 7 fases, 14+ PRs, 150+ commits, cerca de 800 testes.
- Modo de demonstração do assistente (as respostas nas capturas vêm dele).
- **Ausências:** não há usuários além do autor, nem depoimentos, nem métricas de uso. O assistente ainda não foi validado com o Gemini real (modelo e preços não conferidos). Não inventar nada disso.

## Product Principles

1. **Útil antes de bonito, e bonito do jeito simples.** Cada coisa na visão geral precisa ajudar a decidir o próximo clique.
2. **Nada é adivinhado.** Toda decisão automática mostra origem e confiança; na dúvida, o app pergunta em vez de gravar.
3. **A IA ajuda a aprender, não resolve por você.** Ajuda em níveis, sempre citando a fonte, com custo à vista.
4. **Tudo se desfaz, tudo fica no PC.** O aluno controla os próprios dados e pode voltar qualquer alteração.
5. **O app em uso é a vitrine.** Para o portfólio, mostrar o produto real funcionando, não uma página de venda.

## Accessibility & Inclusion

Sem exigência específica além de boas práticas (contraste adequado nos dois temas, navegação por teclado e foco visível, já que ações de linha aparecem no hover ou no foco).
