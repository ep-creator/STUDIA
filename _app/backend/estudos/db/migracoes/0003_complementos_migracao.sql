-- Complementos exigidos pela migração do legado (Fase 2).

-- Texto de apoio do tópico ("Onde estamos": detalhe e previsão de aula).
ALTER TABLE topico ADD COLUMN detalhe_md TEXT NOT NULL DEFAULT '';

-- Um documento pode valer para outras unidades além da sua (ex.: resumo de pré-requisito).
CREATE TABLE documento_unidade_extra (
    documento_id INTEGER NOT NULL REFERENCES documento (id) ON DELETE CASCADE,
    unidade_id INTEGER NOT NULL REFERENCES unidade (id) ON DELETE CASCADE,
    PRIMARY KEY (documento_id, unidade_id)
);

-- Seções equivalentes entre livros (ex.: Guidorizzi cap. 8 ↔ Stewart 14.1). Gravada nos dois sentidos.
CREATE TABLE secao_equivalente (
    secao_id INTEGER NOT NULL REFERENCES secao_livro (id) ON DELETE CASCADE,
    equivalente_id INTEGER NOT NULL REFERENCES secao_livro (id) ON DELETE CASCADE,
    PRIMARY KEY (secao_id, equivalente_id),
    CHECK (secao_id <> equivalente_id)
);
