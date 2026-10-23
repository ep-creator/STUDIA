# STUDIA

Plataforma local de estudos para disciplinas da faculdade. Roda no próprio computador (`http://127.0.0.1:8790`), guarda tudo em arquivos da pasta do projeto e organiza cada matéria em unidades, tópicos, listas de exercícios, cronograma, documentos e formulário.

## Como abrir

Dê dois cliques em **`abrir.bat`** na raiz. Na primeira vez ele cria o ambiente Python do motor e compila a interface; depois só abre.

Requisitos: Python 3.13 e Node.js (a interface é compilada localmente).

## Como funciona

- **Uma pasta por matéria** na raiz (ex.: `Calculo 2/`). O app lista toda pasta que tiver um `materia.db`.
- **Importação por regras:** você solta os PDFs (programa, calendário, listas, livros, provas) e o motor propõe unidades, tópicos, datas e questões; você revisa e confirma.
- **Desfazer e histórico:** toda alteração fica registrada e pode ser desfeita.
- **Busca** nos PDFs e textos da matéria.
- **IA:** chega na Fase 6 (a área já aparece na interface, recolhida).

## Estrutura de pastas

```text
Refatoração Site Estudos/
├── abrir.bat                 # abre o STUDIA
├── README.md
├── _app/                     # o aplicativo
│   ├── abrir-novo.bat        # o que o abrir.bat da raiz chama
│   ├── config.toml           # porta, limiares da importação, histórico
│   ├── backend/              # motor: Python, FastAPI e SQLite (pacote "estudos")
│   └── frontend/             # interface: Svelte 5, Vite e TypeScript
├── Calculo 2/                # uma matéria
│   ├── materia.db            # unidades, tópicos, listas, marcações, cronograma, histórico
│   ├── conteudo/             # resumos, resoluções, anotações e planos em Markdown
│   ├── fontes/               # PDFs: documentos da turma, listas e livros
│   ├── figuras/              # imagens usadas pelos textos
│   └── .migracao/            # relatório da migração do app antigo (Fase 2)
├── docs/
│   ├── superpowers/          # specs e planos de cada fase da refatoração
│   └── legado/               # documentação do app antigo
└── _legado/                  # o app antigo, guardado só para consulta
    ├── abrir-antigo.bat      # ainda abre o app antigo (porta 8780)
    └── Calculo 2/            # app antigo e Cálculo 2 no formato antigo (sem os PDFs)
```

Os PDFs do formato antigo eram idênticos aos de `Calculo 2/fontes/` e saíram do `_legado/`; o histórico do Git guarda a versão completa, se for preciso refazer a migração.

## Desenvolvimento

```bash
# motor (em _app/backend)
.venv/Scripts/python.exe -m pytest -q

# interface (em _app/frontend)
npm test          # Vitest
npm run check     # svelte-check e TypeScript
npm run e2e       # Playwright, ponta a ponta
npm run build
```

As specs e os planos de cada fase ficam em `docs/superpowers/`.
