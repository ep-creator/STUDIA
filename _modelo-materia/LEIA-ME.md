# Modelo de matéria

Esta pasta mostra como o STUDIA organiza uma matéria. Ela fica vazia de propósito: o app não a lista (pastas que começam
com `_` são ignoradas) e nenhum dado pessoal vai para o repositório.

Para criar uma matéria de verdade, use **＋ Nova matéria** na tela inicial. O app cria uma pasta como esta na raiz do
projeto, com o banco `materia.db`, e você solta os PDFs em **Importar**.

```text
<Matéria>/
├── materia.db            # unidades, tópicos, listas, marcações, cronograma, histórico
├── fontes/               # os PDFs
│   ├── documentos/       # programa, calendário, informações da turma
│   ├── livros/
│   ├── listas/
│   ├── slides/
│   ├── provas/
│   └── anotacoes/
├── conteudo/             # textos em Markdown
│   ├── resumos/
│   ├── resolucoes/
│   ├── planos/
│   └── anotacoes/
└── figuras/              # imagens usadas pelos textos
```

As pastas das matérias ficam só no seu computador: o `.gitignore` deixa de fora toda pasta da raiz que não seja do app.
