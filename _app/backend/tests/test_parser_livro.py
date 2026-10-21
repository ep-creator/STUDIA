import pytest

from estudos.importacao.parsers.livro import extrair_livro, normalizar_ocr_codigo
from estudos.importacao.pdf import abrir_pdf
from pdfs_sinteticos import GUIDORIZZI, LEITHOLD, STEWART, criar_pdf


@pytest.mark.parametrize("token,esperado", [
    ("1 O", "10"), ("10. l", "10.1"), ("1 1. l", "11.1"), ("4. 7", "4.7"), ("13'", "13"), ("7 .1", "7.1"), ("1 3.2", "13.2"),
])
def test_normalizar_ocr_codigo(token, esperado):
    assert normalizar_ocr_codigo(token) == esperado


@pytest.fixture
def livro_sintetico(tmp_path):
    paginas = ["capa", "sumário"] + [f"conteúdo {i}" for i in range(3, 21)]
    sumario = [
        [1, "1 Limites", 3], [2, "1.1 Definição", 3], [2, "1.1 Exercícios", 5], [2, "1.2 Continuidade", 6],
        [1, "2- Derivadas", 9], [2, "2.1 Regras", 9], [2, "Revisão", 12], [1, "Apêndice A", 14],
        [1, "Respostas para os Exercícios Ímpares", 17],
    ]
    rotulos = [{"startpage": 2, "prefix": "", "style": "D", "firstpagenum": 1}]
    return abrir_pdf(criar_pdf(tmp_path / "livro.pdf", paginas, sumario=sumario, rotulos=rotulos))


def test_sumario_embutido_sintetico(livro_sintetico):
    livro = extrair_livro(livro_sintetico)
    assert livro.origem == "sumario_embutido" and livro.offset_pagina == 2
    secoes = {s.codigo: s for s in livro.secoes}
    assert list(secoes) == ["1", "1.1", "1.2", "2", "2.1"]
    assert (secoes["1"].nivel, secoes["1"].pagina_pdf_ini, secoes["1"].pagina_pdf_fim) == (1, 3, 8)
    assert (secoes["1.1"].pagina_pdf_ini, secoes["1.1"].pagina_pdf_fim) == (3, 5)
    assert secoes["2"].titulo == "Derivadas" and secoes["2.1"].pagina_pdf_fim == 13
    assert livro.gabarito == (17, 20) and all(s.confianca == 1.0 for s in livro.secoes)


def test_sumario_em_pagina_sintetico(tmp_path):
    sumario = "SUMÁRIO\n1 Funções, 1\n1.1 Funções de uma variável e\nalgumas propriedades, 2\n1 O Derivadas, 5\n10. l Regras, 6\n" \
              "Respostas, Sugestões ou Soluções, 9\nBibliografia, 11"
    paginas = ["capa", sumario] + [f"tema {chr(65 + i % 26)}{chr(65 + i // 26)} do livro" for i in range(1, 13)]
    rotulos = [{"startpage": 2, "prefix": "", "style": "D", "firstpagenum": 1}]
    livro = extrair_livro(abrir_pdf(criar_pdf(tmp_path / "g.pdf", paginas, rotulos=rotulos)))
    assert livro.origem == "pagina_sumario" and livro.offset_pagina == 2
    assert [(s.codigo, s.titulo, s.pagina_pdf_ini) for s in livro.secoes] == [
        ("1", "Funções", 3), ("1.1", "Funções de uma variável e algumas propriedades", 4),
        ("10", "Derivadas", 7), ("10.1", "Regras", 8)]
    assert livro.secoes[0].pagina_pdf_fim == 6 and livro.secoes[-1].pagina_pdf_fim == 10
    assert livro.gabarito == (11, 12) and all(s.confianca == 0.7 for s in livro.secoes)


def test_sem_rotulos_offset_desconhecido(tmp_path):
    livro = extrair_livro(abrir_pdf(criar_pdf(tmp_path / "x.pdf", ["a", "b"], sumario=[[1, "1 Cap", 1], [1, "2 Cap", 2]])))
    assert livro.offset_pagina is None and any("deslocamento" in a for a in livro.avisos)


@pytest.mark.skipif(not STEWART.is_file(), reason="Stewart ausente")
def test_stewart_real():
    livro = extrair_livro(abrir_pdf(STEWART))
    secoes = {s.codigo: s for s in livro.secoes}
    assert livro.origem == "sumario_embutido" and livro.offset_pagina == -489
    assert (secoes["15.4"].pagina_pdf_ini, secoes["15.4"].pagina_pdf_fim) == (406, 411)
    assert secoes["15.8"].pagina_pdf_ini == 433 and secoes["15.4"].titulo == "Integrais Duplas em Coordenadas Polares"
    assert not any("Exercícios" in s.titulo for s in livro.secoes)
    assert livro.gabarito[0] == 613


@pytest.mark.skipif(not GUIDORIZZI.is_file(), reason="Guidorizzi ausente")
def test_guidorizzi_real():
    livro = extrair_livro(abrir_pdf(GUIDORIZZI))
    secoes = {s.codigo: s for s in livro.secoes}
    assert livro.origem == "pagina_sumario" and livro.offset_pagina == 15
    assert secoes["10.1"].pagina_pdf_ini == 188 and secoes["10"].titulo == "Derivadas parciais"
    assert secoes["11.5"].titulo == "O vetor gradiente" and secoes["16.5"].pagina_pdf_ini == 322 + 15
    assert livro.gabarito[0] == 422 + 15
    assert "6.1" in secoes and secoes["6"].titulo.startswith("Os espaços")
    assert len(secoes) == 90


@pytest.mark.skipif(not LEITHOLD.is_file(), reason="Leithold ausente")
def test_leithold_escaneado():
    livro = extrair_livro(abrir_pdf(LEITHOLD, limite_paginas=60))
    assert (livro.origem, livro.sem_texto, livro.secoes) == ("nenhum", True, [])


def test_pagina_com_ocr_no_numero(tmp_path):
    sumario = "Sumário\n5 Equações, 71\n6 Os espaços, 1 O 1\n6. 1 Introdução, 101\n6.2 Vetores, 1 l 2"
    paginas = ["capa", sumario] + [f"tema {chr(65 + i % 26)}{chr(65 + i // 26)} do livro" for i in range(1, 121)]
    rotulos = [{"startpage": 2, "prefix": "", "style": "D", "firstpagenum": 1}]
    livro = extrair_livro(abrir_pdf(criar_pdf(tmp_path / "o.pdf", paginas, rotulos=rotulos)))
    assert [(s.codigo, s.titulo, s.pagina_pdf_ini) for s in livro.secoes] == [
        ("5", "Equações", 73), ("6", "Os espaços", 103), ("6.1", "Introdução", 103), ("6.2", "Vetores", 114)]
