-- Conversas do assistente (Fase 6, peça A): uma ativa por alvo (questão, seção ou geral) e papel. Ficam fora do
-- Histórico (são registro, não dados de estudo); o que o agente grava passa pelo Histórico como qualquer edição.
CREATE TABLE conversa (
    id INTEGER PRIMARY KEY,
    papel TEXT NOT NULL CHECK (papel IN ('tutor', 'resumidor', 'estrategista')),
    alvo TEXT NOT NULL,
    ativa INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0, 1)),
    criada_em TEXT NOT NULL
);
CREATE INDEX idx_conversa_alvo ON conversa (alvo, papel, ativa);

CREATE TABLE mensagem (
    id INTEGER PRIMARY KEY,
    conversa_id INTEGER NOT NULL REFERENCES conversa (id) ON DELETE CASCADE,
    autor TEXT NOT NULL CHECK (autor IN ('voce', 'agente', 'ferramenta')),
    texto TEXT NOT NULL,
    tokens_entrada INTEGER NOT NULL DEFAULT 0,
    tokens_saida INTEGER NOT NULL DEFAULT 0,
    custo_brl REAL NOT NULL DEFAULT 0,
    modelo TEXT,
    criada_em TEXT NOT NULL
);
CREATE INDEX idx_mensagem_conversa ON mensagem (conversa_id);
CREATE INDEX idx_mensagem_data ON mensagem (criada_em);
