import pytest

from estudos.importacao.classificador import classificar
from estudos.importacao.idioma import normalizar, ordinal_para_int, tokens_relevantes
from estudos.importacao.pdf import abrir_pdf
from pdfs_sinteticos import DISCIPLINA, LIVROS, criar_pdf


@pytest.mark.parametrize("palavra,numero", [
    ("Primeira", 1), ("primeiro", 1), ("Segunda", 2), ("TERCEIRA", 3), ("quarta", 4), ("Quinta", 5), ("sexta", 6),
    ("sétima", 7), ("oitavo", 8), ("nona", 9), ("décima", 10), ("3ª", 3), ("2o", 2), ("1º", 1), ("IV", 4), ("ii", 2),
    ("unidade", None), ("", None),
])
def test_ordinal_para_int(palavra, numero):
    assert ordinal_para_int(palavra) == numero


def test_normalizar():
    assert normalizar("  Integrais Triplas em Coordenadas Cilíndricas! ") == "integrais triplas em coordenadas cilindricas"


def test_tokens_relevantes_singulariza_e_tira_stopwords():
    assert tokens_relevantes("Integrais duplas em coordenadas polares") == ["integral", "dupla", "coordenada", "polar"]
    assert tokens_relevantes("Funções de várias variáveis") == ["funcao", "varia", "variavel"]


REAIS = {
    "Programa.pdf": "programa",
    "Calendario.pdf": "calendario",
    "info_S3.pdf": "turma",
    "exercicios_1un.pdf": "lista",
    "exercicios_2un.pdf": "lista",
    "exercicios_3un.pdf": "lista",
    **{f"listas-2026-1/Lista{n}_2026-1.pdf": "lista" for n in range(1, 7)},
}


@pytest.mark.parametrize("rel,tipo", sorted(REAIS.items()))
def test_documentos_reais(rel, tipo):
    caminho = DISCIPLINA / rel
    if not caminho.is_file():
        pytest.skip("arquivo real ausente")
    c = classificar(abrir_pdf(caminho), caminho.name)
    assert c.tipo == tipo, c.sinais
    assert 0.2 <= c.confianca <= 1


@pytest.mark.parametrize("nome", [
    "Calculo - James Stewart - 7 Edição - Volume 2.pdf",
    "Guidorizzi H. L.   Um curso de cálculo vol 2 (2013).pdf",
    "Calculo com Geometria analitica vol 1 - Louis Leithold 3ªed.pdf",
    "Stewart_1_ptbr.pdf",
])
def test_livros_reais(nome):
    caminho = LIVROS / nome
    if not caminho.is_file():
        pytest.skip("livro ausente")
    assert classificar(abrir_pdf(caminho, limite_paginas=3), caminho.name).tipo == "livro"


def test_slides_sinteticos(tmp_path):
    doc = abrir_pdf(criar_pdf(tmp_path / "aula.pdf", ["Aula 3\nIntegrais duplas"] * 5, paisagem=True))
    assert classificar(doc).tipo == "slides"


def test_pagina_em_branco_e_outro(tmp_path):
    c = classificar(abrir_pdf(criar_pdf(tmp_path / "x.pdf", [""])))
    assert (c.tipo, c.confianca) == ("outro", 0.2)


def test_prova_sintetica(tmp_path):
    texto = "Cálculo 2 - Primeiro Exame\n1. Calcule o limite.\n2. Determine o domínio.\n3. Ache os pontos críticos."
    assert classificar(abrir_pdf(criar_pdf(tmp_path / "prova.pdf", [texto]))).tipo == "prova"


def test_gabarito_de_prova_com_problemas_e_itens(tmp_path):
    texto = ("MA036 – GEOMETRIA ANALÍTICA 1 – 2026.2\nTurmas:\nE1, E2, E3\nP1, P2\n1ª Prova – Gabarito\n1o problema\n"
             "A figura abaixo representa um paralelepípedo.\na) (1,0 pt) Expresse o vetor.\nb) (1,0 pt) Determine F.\n"
             "Solução:\na) Por um lado.\n2o problema\nConsidere a reta.\na) (1,5 pt) Ache.")
    doc = abrir_pdf(criar_pdf(tmp_path / "prova.pdf", [texto, "3o problema\na) (2,0 pt) Calcule.", "Solução: ...", "fim"]))
    assert classificar(doc, "Prova 1 - gabarito oficial.pdf").tipo == "prova"
