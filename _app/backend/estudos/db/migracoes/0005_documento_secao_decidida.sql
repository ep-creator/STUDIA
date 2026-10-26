-- A seção do livro de um documento foi escolhida (ou removida) à mão: a ligação automática não mexe mais nela.
ALTER TABLE documento ADD COLUMN secao_decidida INTEGER NOT NULL DEFAULT 0;
