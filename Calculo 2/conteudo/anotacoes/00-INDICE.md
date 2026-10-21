---
tipo: anotacao
titulo: Índice do projeto
unidade: null
secao: null
questao: null
origem: migrado
---
# Cálculo 2 — 2026.2 — Turma S3 (Prof. Henrique Araújo)

Guia de estudos do Enzo. **Unidade corrente: 3ª** — prova segunda, 30/11.

## Como usar

1. Abra `plano-estudos-unidade3.md` e veja qual é a próxima sessão.
2. Leia o resumo teórico do assunto em `resumos/` **antes** de abrir a lista.
3. Faça os exercícios marcados em `exercicios/stewart-un3.md` e vá atualizando o status.
   No app, o seletor **1ª / 2ª / 3ª unidade** acima da lista escolhe o que aparece e o que entra no placar.
4. Ou use o **app**: duplo clique em `_app\abrir.bat`. Ele abre o caderno no navegador com a mesma lista — enunciado de cada exercício, botões de **acertei / errei / dúvida** e a resolução expansível — lendo estes arquivos ao vivo.
5. Travou? Traga a questão para o Claude. O modo de ajuda é **progressivo**:
   - **N1 — Dica**: qual conceito/teorema está em jogo.
   - **N2 — Caminho**: a estratégia, sem contas.
   - **N3 — Esboço**: os passos com as contas-chave, deixando lacunas.
   - **N4 — Resolução completa**: no padrão de correção do professor.
   Peça pelo nível (ex.: *"me dá um N2 do 14.3 #71"*).

> O app em `_app/` lê estes arquivos **ao vivo**: escreveu uma resolução, aperta F5 e ela está lá. Suas marcações ficam em `status.json`, na raiz — é de lá que o Claude sabe o que você errou.

## Arquivos

| Arquivo | O que é |
|---|---|
| `plano-estudos-unidade3.md` | **Cronograma da 3ª unidade** — 17 sessões até 30/11 |
| `exercicios/stewart-un3.md` | **Lista oficial da 3ª unidade** (15.4, 15.5, 15.7, 15.8, 15.9, 15.10) |
| `exercicios/listas-2026-1.md` | Mapa das seis listas de 2026.1 por assunto — as **5 e 6** cobrem esta unidade |
| `plano-estudos-unidade2.md` | Cronograma da 2ª unidade (encerrado) |
| `plano-estudos-unidade1.md` | Cronograma da 1ª unidade (encerrado) |
| `exercicios/stewart-un2.md` | Lista oficial da 2ª unidade |
| `exercicios/stewart-un1.md` | Lista oficial da 1ª unidade |
| `exercicios/guidorizzi-un1.md` | Exercícios equivalentes no Guidorizzi (fase 3) |
| `referencia/calendario.md` | Datas de aula e de prova das três unidades |
| `resumos/` | Teoria condensada por assunto, no formato que a prova cobra |
| `resolucoes/` | Gabarito comentado dos exercícios já feitos, um arquivo por questão (`14-1-22.md` = seção 14.1, exercício 22) |
| `_app/` | O caderno como aplicação local — `abrir.bat` e pronto. Veja `_app/LEIAME.md` |
| `status.json` | Suas marcações de acertei / errei / dúvida, escritas pelo app |
| `referencia/mapa-livros.md` | Conversão página do livro ↔ página do PDF |
| `livros/` | Os PDFs dos livros: Stewart V2 (referência), Guidorizzi V2 (reforço), e os de Cálculo 1 (Stewart V1, Leithold V1) para consulta |
| `disciplina/` | O que veio do professor: `Programa.pdf`, `info_S3.pdf`, `Calendario.pdf`, `exercicios_1un/2un/3un.pdf` |
| `disciplina/listas-2026-1/` | As seis listas do semestre 2026.1 (outra equipe de professores) |

## Organização da pasta

```
Calculo 2/
├── 00-INDICE.md                 ← você está aqui
├── plano-estudos-unidade3.md   ← a unidade corrente
├── plano-estudos-unidade2.md
├── plano-estudos-unidade1.md
├── status.json                  ← aparece quando você usar o app
├── resumos/                     teoria por assunto
├── resolucoes/                  gabarito comentado, um arquivo por questão
├── exercicios/                  listas do Stewart e do Guidorizzi
├── referencia/                  mapa de páginas dos livros
├── livros/                      os PDFs dos livros
├── disciplina/                  o que o professor distribuiu
│   └── listas-2026-1/           as seis listas do semestre passado
└── _app/                        o caderno como aplicação local
```

Só o que está fora de `_app/` é conteúdo de estudo; `_app/` é maquinário, e o
`LEIAME.md` de lá explica como mexer nele.

## Datas que mandam

| 1º exame | 2º exame | 3º exame | 2ª chamada | Final |
|---|---|---|---|---|
| **14/09** | 19/10 | 30/11 | 09/12 | 14/12 |

Todos às 14h30. Detalhes e datas de aula em `referencia/calendario.md`.

## Estado do conteúdo (atualizado em 20/10/2026)

- **1ª unidade** (14.1–14.5) — encerrada, prova em 14/09: **nota 8,0**.
- **2ª unidade** (14.6–14.8, 15.2, 15.3) — encerrada, prova em 19/10. O programa foi dado inteiro; o último assunto foi a inversão da ordem de integração.
- **3ª unidade** (15.4, 15.5, 15.7–15.10) — **foco atual**. Nenhuma aula ainda: a primeira é **sexta, 30/10**. Até lá, o plano usa a semana livre para pré-requisitos (polares, regiões do 15.3, integrais trigonométricas).

Pendente: a nota da prova 2 (quando sair, uma sessão para dissecar os erros) e as marcações da 2ª unidade no app, que ficaram vazias.

Depois da 3ª prova: segunda chamada em 09/12 e **exame final em 14/12**.

## Regras do professor que afetam o estudo

- **Não há gabarito oficial** de listas nem de provas anteriores. Para tirar dúvida com ele, é preciso levar a **resolução escrita** — ele aponta erros, não resolve.
- A correção exige: embasamento teórico citado, indicação de como o resultado foi usado, **nenhum passo omitido**, justificativas, nenhum cálculo omitido, clareza e organização.
- Por isso, todo exercício aqui deve ser escrito no caderno em formato de prova — não "resolvido de cabeça".
