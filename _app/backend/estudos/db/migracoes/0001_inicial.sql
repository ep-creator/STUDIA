-- Schema inicial do banco da matéria (spec §5).
-- Convenções: datas ISO-8601 em TEXT; `origem` registra de onde veio o dado; `confianca` só em dados inferidos.

CREATE TABLE materia (
    id INTEGER PRIMARY KEY,
    uid TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    periodo TEXT,
    instituicao TEXT,
    professor TEXT,
    email_professor TEXT,
    criada_em TEXT NOT NULL
);

CREATE TABLE unidade (
    id INTEGER PRIMARY KEY,
    numero INTEGER NOT NULL UNIQUE CHECK (numero >= 1),
    titulo TEXT NOT NULL DEFAULT '',
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado')),
    confianca REAL CHECK (confianca BETWEEN 0 AND 1)
);

CREATE TABLE evento (
    id INTEGER PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('aula', 'prova', 'segunda_chamada', 'exame_final', 'extra', 'feriado')),
    data TEXT NOT NULL,
    hora_inicio TEXT,
    hora_fim TEXT,
    unidade_id INTEGER REFERENCES unidade (id) ON DELETE SET NULL,
    descricao TEXT NOT NULL DEFAULT '',
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado'))
);
CREATE INDEX idx_evento_unidade_tipo ON evento (unidade_id, tipo);

CREATE TABLE horario_aula (
    id INTEGER PRIMARY KEY,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    hora_inicio TEXT NOT NULL,
    hora_fim TEXT NOT NULL
);

CREATE TABLE topico (
    id INTEGER PRIMARY KEY,
    unidade_id INTEGER NOT NULL REFERENCES unidade (id) ON DELETE CASCADE,
    pai_id INTEGER REFERENCES topico (id) ON DELETE CASCADE,
    ordem INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'proxima', 'visto')),
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado'))
);
CREATE INDEX idx_topico_unidade ON topico (unidade_id);

CREATE TABLE fonte (
    id INTEGER PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('programa', 'calendario', 'turma', 'livro', 'lista', 'slides', 'prova', 'anotacao', 'outro')),
    caminho TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL UNIQUE,
    titulo TEXT NOT NULL DEFAULT '',
    paginas INTEGER,
    importada_em TEXT NOT NULL,
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado'))
);

CREATE TABLE livro (
    fonte_id INTEGER PRIMARY KEY REFERENCES fonte (id) ON DELETE CASCADE,
    papel TEXT NOT NULL CHECK (papel IN ('principal', 'complementar')),
    autor TEXT NOT NULL DEFAULT '',
    titulo_obra TEXT NOT NULL DEFAULT '',
    edicao TEXT NOT NULL DEFAULT '',
    offset_pagina INTEGER NOT NULL DEFAULT 0,
    gabarito_pdf_ini INTEGER,
    gabarito_pdf_fim INTEGER
);

CREATE TABLE secao_livro (
    id INTEGER PRIMARY KEY,
    livro_id INTEGER NOT NULL REFERENCES livro (fonte_id) ON DELETE CASCADE,
    codigo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    nivel INTEGER NOT NULL DEFAULT 1,
    pagina_pdf_ini INTEGER NOT NULL,
    pagina_pdf_fim INTEGER NOT NULL,
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado')),
    confianca REAL CHECK (confianca BETWEEN 0 AND 1),
    UNIQUE (livro_id, codigo)
);

CREATE TABLE topico_secao (
    topico_id INTEGER NOT NULL REFERENCES topico (id) ON DELETE CASCADE,
    secao_id INTEGER NOT NULL REFERENCES secao_livro (id) ON DELETE CASCADE,
    confianca REAL CHECK (confianca BETWEEN 0 AND 1),
    confirmado INTEGER NOT NULL DEFAULT 0 CHECK (confirmado IN (0, 1)),
    PRIMARY KEY (topico_id, secao_id)
);

CREATE TABLE lista (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    unidade_id INTEGER NOT NULL REFERENCES unidade (id) ON DELETE RESTRICT,
    fonte_id INTEGER REFERENCES fonte (id) ON DELETE SET NULL,
    liberacao TEXT NOT NULL DEFAULT 'auto' CHECK (liberacao IN ('auto', 'aberta', 'travada')),
    ordem INTEGER NOT NULL,
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado'))
);

CREATE TABLE lista_secao (
    lista_id INTEGER NOT NULL REFERENCES lista (id) ON DELETE CASCADE,
    secao_id INTEGER NOT NULL REFERENCES secao_livro (id) ON DELETE CASCADE,
    PRIMARY KEY (lista_id, secao_id)
);

CREATE TABLE lista_topico (
    lista_id INTEGER NOT NULL REFERENCES lista (id) ON DELETE CASCADE,
    topico_id INTEGER NOT NULL REFERENCES topico (id) ON DELETE CASCADE,
    PRIMARY KEY (lista_id, topico_id)
);

CREATE TABLE questao (
    id INTEGER PRIMARY KEY,
    lista_id INTEGER NOT NULL REFERENCES lista (id) ON DELETE CASCADE,
    rotulo TEXT NOT NULL,
    ordem INTEGER NOT NULL,
    linha INTEGER NOT NULL DEFAULT 1 CHECK (linha IN (1, 2)),
    enunciado_md TEXT NOT NULL DEFAULT '',
    expressao TEXT,
    pagina_pdf INTEGER,
    figura TEXT,
    chave_legada TEXT,
    UNIQUE (lista_id, rotulo)
);
CREATE INDEX idx_questao_lista ON questao (lista_id);

CREATE TABLE marcacao (
    questao_id INTEGER PRIMARY KEY REFERENCES questao (id) ON DELETE CASCADE,
    estado TEXT NOT NULL CHECK (estado IN ('ok', 'err', 'dub')),
    atualizado_em TEXT NOT NULL
);

CREATE TABLE sessao_estudo (
    id INTEGER PRIMARY KEY,
    unidade_id INTEGER NOT NULL REFERENCES unidade (id) ON DELETE RESTRICT,
    codigo TEXT NOT NULL,
    data TEXT,
    foco_md TEXT NOT NULL DEFAULT '',
    feito INTEGER NOT NULL DEFAULT 0 CHECK (feito IN (0, 1)),
    ordem INTEGER NOT NULL,
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado'))
);

CREATE TABLE sessao_questao (
    sessao_id INTEGER NOT NULL REFERENCES sessao_estudo (id) ON DELETE CASCADE,
    questao_id INTEGER NOT NULL REFERENCES questao (id) ON DELETE CASCADE,
    PRIMARY KEY (sessao_id, questao_id)
);

CREATE TABLE formula (
    id INTEGER PRIMARY KEY,
    unidade_id INTEGER NOT NULL REFERENCES unidade (id) ON DELETE RESTRICT,
    secao_id INTEGER REFERENCES secao_livro (id) ON DELETE SET NULL,
    titulo TEXT NOT NULL,
    corpo_tex TEXT NOT NULL,
    notas_md TEXT NOT NULL DEFAULT '',
    ordem INTEGER NOT NULL,
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado'))
);

CREATE TABLE documento (
    id INTEGER PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('resumo', 'resolucao', 'plano', 'anotacao', 'contexto')),
    caminho TEXT NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    unidade_id INTEGER REFERENCES unidade (id) ON DELETE SET NULL,
    secao_id INTEGER REFERENCES secao_livro (id) ON DELETE SET NULL,
    questao_id INTEGER REFERENCES questao (id) ON DELETE SET NULL,
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado')),
    atualizado_em TEXT NOT NULL
);

CREATE TABLE nota_avaliacao (
    unidade_id INTEGER PRIMARY KEY REFERENCES unidade (id) ON DELETE CASCADE,
    nota REAL NOT NULL,
    registrada_em TEXT NOT NULL
);

CREATE TABLE criterio_correcao (
    id INTEGER PRIMARY KEY,
    ordem INTEGER NOT NULL,
    texto TEXT NOT NULL,
    origem TEXT NOT NULL CHECK (origem IN ('importado', 'manual', 'agente', 'migrado'))
);

CREATE TABLE historico_grupo (
    id INTEGER PRIMARY KEY,
    momento TEXT NOT NULL,
    descricao TEXT NOT NULL,
    desfaz_grupo INTEGER REFERENCES historico_grupo (id) ON DELETE SET NULL,
    desfeito_em TEXT
);

CREATE TABLE historico_mudanca (
    id INTEGER PRIMARY KEY,
    grupo_id INTEGER NOT NULL REFERENCES historico_grupo (id) ON DELETE CASCADE,
    ordem INTEGER NOT NULL,
    tabela TEXT,
    chave_json TEXT,
    antes_json TEXT,
    depois_json TEXT,
    arquivo TEXT,
    versao_arquivo TEXT
);
CREATE INDEX idx_historico_mudanca_grupo ON historico_mudanca (grupo_id);
