-- Rascunhos de importação: a proposta extraída de um arquivo, revisável antes de virar dado de domínio.
CREATE TABLE importacao (
    id INTEGER PRIMARY KEY,
    fonte_id INTEGER NOT NULL REFERENCES fonte (id) ON DELETE CASCADE,
    tipo TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'proposta' CHECK (estado IN ('proposta', 'confirmada', 'descartada')),
    proposta_json TEXT NOT NULL,
    criada_em TEXT NOT NULL,
    confirmada_em TEXT
);
CREATE INDEX idx_importacao_fonte ON importacao (fonte_id);
