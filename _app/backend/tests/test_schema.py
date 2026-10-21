import sqlite3

import pytest

from estudos.db.conexao import aplicar_migracoes, conectar

TABELAS = {
    "materia", "unidade", "evento", "horario_aula", "topico", "fonte", "livro", "secao_livro", "topico_secao",
    "lista", "lista_secao", "lista_topico", "questao", "marcacao", "sessao_estudo", "sessao_questao", "formula",
    "documento", "nota_avaliacao", "criterio_correcao", "historico_grupo", "historico_mudanca", "schema_versao",
}


@pytest.fixture
def con_vazia(tmp_path):
    con = conectar(tmp_path / "materia.db")
    aplicar_migracoes(con)
    return con


def _lista_com_questao(con):
    con.execute("INSERT INTO unidade (numero, titulo, origem) VALUES (1, 'U1', 'manual')")
    con.execute("INSERT INTO lista (codigo, titulo, unidade_id, liberacao, ordem, origem) VALUES ('L1', 'Lista 1', 1, 'auto', 1, 'manual')")
    con.execute("INSERT INTO questao (lista_id, rotulo, ordem, linha) VALUES (1, '1', 1, 1)")


def test_tabelas_existem(con_vazia):
    nomes = {r[0] for r in con_vazia.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert TABELAS <= nomes


def test_check_estado_marcacao(con_vazia):
    _lista_com_questao(con_vazia)
    with pytest.raises(sqlite3.IntegrityError):
        con_vazia.execute("INSERT INTO marcacao (questao_id, estado, atualizado_em) VALUES (1, 'talvez', 'x')")


def test_check_origem(con_vazia):
    with pytest.raises(sqlite3.IntegrityError):
        con_vazia.execute("INSERT INTO unidade (numero, titulo, origem) VALUES (1, 'U1', 'chute')")


def test_cascade_lista_apaga_questoes_e_marcacoes(con_vazia):
    _lista_com_questao(con_vazia)
    con_vazia.execute("INSERT INTO marcacao (questao_id, estado, atualizado_em) VALUES (1, 'ok', 'x')")
    con_vazia.execute("DELETE FROM lista WHERE id = 1")
    assert con_vazia.execute("SELECT count(*) FROM questao").fetchone()[0] == 0
    assert con_vazia.execute("SELECT count(*) FROM marcacao").fetchone()[0] == 0


def test_restrict_unidade_com_lista(con_vazia):
    _lista_com_questao(con_vazia)
    with pytest.raises(sqlite3.IntegrityError):
        con_vazia.execute("DELETE FROM unidade WHERE id = 1")


def test_unique_rotulo_por_lista(con_vazia):
    _lista_com_questao(con_vazia)
    with pytest.raises(sqlite3.IntegrityError):
        con_vazia.execute("INSERT INTO questao (lista_id, rotulo, ordem, linha) VALUES (1, '1', 2, 2)")


def test_evento_sobrevive_a_unidade_apagada(con_vazia):
    con_vazia.execute("INSERT INTO unidade (numero, titulo, origem) VALUES (1, 'U1', 'manual')")
    con_vazia.execute("INSERT INTO evento (tipo, data, unidade_id, descricao, origem) VALUES ('prova', '2026-09-14', 1, '', 'manual')")
    con_vazia.execute("DELETE FROM unidade WHERE id = 1")
    assert con_vazia.execute("SELECT unidade_id FROM evento").fetchone()[0] is None
