-- Um grupo de desfazer é identificado por esta marca, não por desfaz_grupo: a poda pode apagar o grupo original
-- (desfaz_grupo vira NULL) e o desfazer não pode passar a parecer uma ação comum.
ALTER TABLE historico_grupo ADD COLUMN eh_desfazer INTEGER NOT NULL DEFAULT 0 CHECK (eh_desfazer IN (0, 1));
UPDATE historico_grupo SET eh_desfazer = 1 WHERE desfaz_grupo IS NOT NULL;
