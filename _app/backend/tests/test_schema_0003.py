import sqlite3

import pytest

from estudos.historico import desfazer_ultimo, operacao
from estudos.repos import documentos, topicos, unidades


@pytest.fixture
def us(con):
    with operacao(con, "base") as op:
        return unidades.criar(op, 1), unidades.criar(op, 3)


def test_topico_detalhe_md_persiste(con, us):
    with operacao(con, "x") as op:
        topicos.criar(op, us[0], "Polares", detalhe_md="Previsto: Sex 30/10\n\ndA = r dr dθ")
    assert topicos.listar(con, us[0])[0].detalhe_md == "Previsto: Sex 30/10\n\ndA = r dr dθ"


def test_documento_extra_aparece_na_outra_unidade(con, materia, us):
    u1, u3 = us
    with operacao(con, "x", materia.pasta) as op:
        d = documentos.salvar(op, "resumo", "00-polares", "Polares", "x", unidade_id=u1)
        documentos.adicionar_unidade_extra(op, d, u3)
    assert [doc.id for doc in documentos.listar(con, unidade_id=u3)] == [d]
    assert [doc.id for doc in documentos.listar(con, unidade_id=u1)] == [d]


def test_documento_global_aparece_em_todas(con, materia, us):
    u1, u3 = us
    with operacao(con, "x", materia.pasta) as op:
        g = documentos.salvar(op, "anotacao", "calendario", "Calendário", "x")
        documentos.salvar(op, "resumo", "so-u1", "Só U1", "x", unidade_id=u1)
    assert [doc.id for doc in documentos.listar(con, unidade_id=u3)] == [g]


def test_secao_equivalente_nao_aceita_ela_mesma(con):
    con.execute("INSERT INTO fonte (tipo, caminho, sha256, importada_em, origem) VALUES ('livro', 'l.pdf', 'h', 'x', 'manual')")
    con.execute("INSERT INTO livro (fonte_id, papel) VALUES (1, 'principal')")
    con.execute("INSERT INTO secao_livro (livro_id, codigo, titulo, pagina_pdf_ini, pagina_pdf_fim, origem) VALUES (1, '1', 'A', 1, 2, 'manual')")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO secao_equivalente (secao_id, equivalente_id) VALUES (1, 1)")


def test_desfazer_remove_extra(con, materia, us):
    u1, u3 = us
    with operacao(con, "doc", materia.pasta) as op:
        d = documentos.salvar(op, "resumo", "a", "A", "x", unidade_id=u1)
    with operacao(con, "extra") as op:
        documentos.adicionar_unidade_extra(op, d, u3)
    desfazer_ultimo(con, materia.pasta)
    assert documentos.listar(con, unidade_id=u3) == []
