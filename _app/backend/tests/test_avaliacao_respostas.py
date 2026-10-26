import pytest

from estudos.avaliacao.respostas import Aceita, casa, ler_aceita
from estudos.rag.busca import Resultado


def _r(**k):
    base = dict(trecho_id=1, origem="fonte:1", tipo="slides", titulo="Aula 3 - Retas e planos", trecho="", pagina=5,
                secao_id=None, secao_codigo=None, fonte_id=1, documento_id=None, score=0.0)
    return Resultado(**(base | k))


@pytest.mark.parametrize("texto, esperado", [
    ("secao:15.4", Aceita("secao", "15.4")),
    ("fonte:Aula 3 - Retas e planos", Aceita("fonte", "Aula 3 - Retas e planos")),
    ("fonte:Aula 3 - Retas e planos#p5", Aceita("fonte", "Aula 3 - Retas e planos", 5, 5)),
    ("fonte:Lista 1 - GA#p2-3", Aceita("fonte", "Lista 1 - GA", 2, 3)),
    ("documento:15.4 Integrais#mudanca-para-polares", Aceita("documento", "15.4 Integrais", bloco="mudanca-para-polares")),
])
def test_ler_aceita(texto, esperado):
    assert ler_aceita(texto) == esperado
    assert ler_aceita(texto).precisa == (esperado.pag_ini is not None or esperado.bloco is not None)


@pytest.mark.parametrize("texto", ["capitulo:1", "fonte:", "fonte:X#pdez", "fonte:X#p7-3", "secao"])
def test_aceita_invalida(texto):
    with pytest.raises(ValueError):
        ler_aceita(texto)


def test_fonte_casa_pelo_titulo_e_pela_pagina():
    titulos = {1: ("Aula 3 - Retas e planos", "fontes/slides/Aula 3 - Retas e planos-2.pdf")}
    assert casa(titulos, {}, _r(), ler_aceita("fonte:Aula 3 - Retas e planos"), trecho=False)
    assert casa(titulos, {}, _r(), ler_aceita("fonte:Aula 3 - Retas e planos-2"), trecho=False)   # nome do arquivo
    assert casa(titulos, {}, _r(pagina=6), ler_aceita("fonte:Aula 3 - Retas e planos#p5-7"), trecho=True)
    assert not casa(titulos, {}, _r(pagina=9), ler_aceita("fonte:Aula 3 - Retas e planos#p5-7"), trecho=True)
    assert casa(titulos, {}, _r(pagina=9), ler_aceita("fonte:Aula 3 - Retas e planos#p5-7"), trecho=False)


def test_documento_casa_pelo_bloco():
    docs = {9: "15.4 Integrais"}
    r = _r(origem="documento:9", tipo="resumo", titulo="15.4 Integrais — Mudança para polares", fonte_id=None, documento_id=9)
    assert casa({}, docs, r, ler_aceita("documento:15.4 Integrais#mudanca-para-polares"), trecho=True)
    assert not casa({}, docs, r, ler_aceita("documento:15.4 Integrais#exemplos"), trecho=True)
    assert casa({}, docs, r, ler_aceita("documento:15.4 Integrais#exemplos"), trecho=False)


def test_secao_casa_pelo_codigo():
    assert casa({}, {}, _r(secao_codigo="15.4"), ler_aceita("secao:15.4"), trecho=False)
    assert not casa({}, {}, _r(secao_codigo="15.5"), ler_aceita("secao:15.4"), trecho=False)
