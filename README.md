# STUDIA

Plataforma local de estudos para disciplinas da faculdade, **construída inteira conversando com uma IA**. Você solta os
PDFs da matéria (programa, calendário, livros, listas, slides), e ela monta as unidades, os tópicos, as listas e as
seções do livro; marca o que você acertou e errou, mostra o que revisar e tem um assistente que ajuda nas questões,
escreve resumos e monta o plano até a prova.

Roda no próprio computador, em `http://127.0.0.1:8790`, e guarda tudo em arquivos na pasta do projeto.

## Páginas

| | |
|---|---|
| **[Guia de uso](docs/guia.md)** | como abrir, criar uma matéria, usar cada tela e configurar o assistente |
| **[A ideia do projeto](docs/ideia.md)** | o experimento de construir uma plataforma inteira com IA, os princípios e o método |
| **[Tecnologia e evolução](docs/tecnologia.md)** | a stack, como cada peça funciona e como a tecnologia mudou (inclusive por que o RAG ficou menor) |

## Começar em um minuto

1. Instale **Python 3.13** e **Node.js**.
2. Dê dois cliques em **`abrir.bat`**, na raiz.
3. No navegador, crie uma matéria e solte os PDFs em **Importar**.

O resto está no [Guia de uso](docs/guia.md).

## Estrutura de pastas

```text
Refatoração Site Estudos/
├── abrir.bat             # abre o STUDIA
├── README.md
├── _app/                 # o aplicativo
│   ├── config.toml       # porta, limiares, busca, assistente (modelo, preços, teto)
│   ├── backend/          # motor: Python, FastAPI e SQLite
│   └── frontend/         # interface: Svelte 5, Vite e TypeScript
├── <Matéria>/            # uma pasta por matéria
│   ├── materia.db        # unidades, tópicos, listas, marcações, cronograma, histórico
│   ├── conteudo/         # resumos, resoluções, anotações e planos em Markdown
│   ├── fontes/           # PDFs: documentos da turma, listas e livros
│   └── figuras/          # imagens usadas pelos textos
└── docs/
    ├── guia.md, ideia.md, tecnologia.md
    ├── avaliacoes/       # medições de busca, vínculos e contexto
    └── superpowers/      # especificações e planos de cada fase
```
