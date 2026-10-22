import sqlite3

import pytest

from estudos.rag.indice import VERSAO_INDICE, abrir_indice, caminho_indice


def _tabelas(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'trigger')")}


def test_cria_estrutura(materia):
    con = abrir_indice(materia.pasta)
    assert caminho_indice(materia.pasta).is_file()
    assert {"estado", "trecho", "trecho_fts"} <= _tabelas(con)
    assert con.execute("PRAGMA user_version").fetchone()[0] == VERSAO_INDICE
    con.close()


def test_materia_anexada_somente_leitura(materia):
    con = abrir_indice(materia.pasta)
    assert con.execute("SELECT nome FROM m.materia").fetchone()[0] == "Matéria Teste"
    with pytest.raises(sqlite3.OperationalError):
        con.execute("INSERT INTO m.unidade (numero, titulo, origem) VALUES (1, 'x', 'manual')")
    con.close()


def test_fts_acompanha_a_tabela(materia):
    con = abrir_indice(materia.pasta)
    con.execute("INSERT INTO trecho (origem, tipo, titulo, texto, ordem) VALUES ('documento:1', 'resumo', 'Polares', 'coordenadas polares', 1)")
    assert con.execute("SELECT count(*) FROM trecho_fts WHERE trecho_fts MATCH 'polares'").fetchone()[0] == 1
    con.execute("DELETE FROM trecho")
    assert con.execute("SELECT count(*) FROM trecho_fts WHERE trecho_fts MATCH 'polares'").fetchone()[0] == 0
    con.close()


def test_arquivo_corrompido_e_recriado(materia):
    caminho = caminho_indice(materia.pasta)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(b"lixo que nao e sqlite" * 50)
    con = abrir_indice(materia.pasta)
    assert "trecho" in _tabelas(con)
    con.close()


def test_versao_antiga_e_recriada(materia):
    con = abrir_indice(materia.pasta)
    con.execute("INSERT INTO trecho (origem, tipo, titulo, texto, ordem) VALUES ('x', 't', 't', 't', 1)")
    con.execute("PRAGMA user_version = 0")
    con.close()
    con = abrir_indice(materia.pasta)
    assert con.execute("SELECT count(*) FROM trecho").fetchone()[0] == 0
    con.close()


def test_caminho_alternativo(materia, tmp_path):
    destino = tmp_path / "outro" / "indice.db"
    con = abrir_indice(materia.pasta, destino)
    assert destino.is_file() and not caminho_indice(materia.pasta).exists()
    con.close()
