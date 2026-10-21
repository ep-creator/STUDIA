import hashlib

import pytest

from estudos.erros import DadoInvalido
from estudos.historico import operacao
from estudos.repos import fontes, listas, livros, topicos, unidades


def _arquivo(materia, rel, conteudo=b"abc"):
    caminho = materia.pasta / rel
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(conteudo)
    return rel


def test_registrar_fonte_calcula_sha(con, materia):
    rel = _arquivo(materia, "fontes/livros/a.pdf")
    with operacao(con, "x", materia.pasta) as op:
        f = fontes.registrar(op, "livro", rel, "Livro A", paginas=10)
    fonte = fontes.obter_por_caminho(con, rel)
    assert fonte.id == f and fonte.sha256 == hashlib.sha256(b"abc").hexdigest() and fonte.paginas == 10
    assert [x.id for x in fontes.listar(con, "livro")] == [f] and fontes.listar(con, "lista") == []


def test_fonte_duplicada(con, materia):
    a = _arquivo(materia, "fontes/livros/a.pdf")
    b = _arquivo(materia, "fontes/documentos/b.pdf")
    with operacao(con, "x", materia.pasta) as op:
        fontes.registrar(op, "livro", a)
    with operacao(con, "y", materia.pasta) as op, pytest.raises(DadoInvalido, match="a.pdf"):
        fontes.registrar(op, "outro", b)


def test_tipo_fonte_invalido(con, materia):
    rel = _arquivo(materia, "fontes/x.pdf")
    with operacao(con, "x", materia.pasta) as op, pytest.raises(DadoInvalido):
        fontes.registrar(op, "receita", rel)


@pytest.fixture
def livro(con, materia):
    rel = _arquivo(materia, "fontes/livros/stewart.pdf")
    with operacao(con, "x", materia.pasta) as op:
        f = fontes.registrar(op, "livro", rel)
        livros.criar(op, f, "principal", offset_pagina=-489, gabarito_pdf_ini=614, gabarito_pdf_fim=643)
    return f


def test_livro_principal(con, livro):
    p = livros.principal(con)
    assert (p.fonte_id, p.offset_pagina, p.gabarito_pdf_ini) == (livro, -489, 614)


def test_secao_nivel_automatico(con, livro):
    with operacao(con, "x") as op:
        livros.criar_secao(op, livro, "15.4", "Polares", 406, 411)
        livros.criar_secao(op, livro, "8", "Capítulo 8", 162, 177)
    niveis = {s.codigo: s.nivel for s in livros.listar_secoes(con, livro)}
    assert niveis == {"15.4": 2, "8": 1}
    assert [s.codigo for s in livros.listar_secoes(con, livro)] == ["8", "15.4"]
    assert livros.secao_por_codigo(con, livro, "15.4").pagina_pdf_fim == 411


def test_secao_fim_antes_do_inicio(con, livro):
    with operacao(con, "x") as op, pytest.raises(DadoInvalido):
        livros.criar_secao(op, livro, "15.4", "Polares", 411, 406)


def test_equivalencia_nos_dois_sentidos(con, livro):
    with operacao(con, "x") as op:
        a = livros.criar_secao(op, livro, "14.1", "A", 1, 2)
        b = livros.criar_secao(op, livro, "8", "B", 3, 4)
        livros.vincular_equivalente(op, a, b)
        livros.vincular_equivalente(op, a, b)
    pares = set(map(tuple, con.execute("SELECT secao_id, equivalente_id FROM secao_equivalente")))
    assert pares == {(a, b), (b, a)}


def test_vinculo_topico_secao_abre_lista_auto(con, livro):
    with operacao(con, "x") as op:
        u = unidades.criar(op, 3)
        t = topicos.criar(op, u, "Polares")
        s = livros.criar_secao(op, livro, "15.4", "Polares", 406, 411)
        livros.vincular_topico(op, t, s, confianca=1.0, confirmado=True)
        lista = listas.criar(op, "15.4", "Seção 15.4", u)
        listas.vincular_secao(op, lista, s)
        topicos.definir_status(op, t, "visto")
    assert listas.obter(con, lista).aberta is True
    vinculo = con.execute("SELECT confianca, confirmado FROM topico_secao").fetchone()
    assert tuple(vinculo) == (1.0, 1)
