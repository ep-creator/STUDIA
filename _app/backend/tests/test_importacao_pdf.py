import pytest

from estudos.importacao.pdf import PdfInvalido, abrir_pdf, limpar_texto, remover_repetidos
from pdfs_sinteticos import LEITHOLD, STEWART, criar_pdf


def test_limpar_acentos_latex():
    texto = "Centro de Ciˆencias … Mudan¸ca de var´ıaveis · Conte´udos · C´alculo · regi˜ao"
    assert limpar_texto(texto) == "Centro de Ciências … Mudança de varíaveis · Conteúdos · Cálculo · região"


def test_limpar_ligaduras_cid_e_marcador():
    assert limpar_texto("ﬁm (cid:12)de item   com   espaços") == "fim de• item com espaços"


def test_remover_cabecalhos_repetidos():
    meio = "\n".join(f"texto comum do meio {n}" for n in range(8))
    paginas = [
        f"Calculo15B:calculo7 5/25/13 9:58 AM Page {900 + i}\ncorpo {chr(97 + i)}\n{meio}\nfim {chr(97 + i)}\n{922 + i} CÁLCULO"
        for i in range(6)
    ]
    limpas = remover_repetidos(paginas)
    assert all("Page" not in p and "CÁLCULO" not in p for p in limpas)
    assert "corpo d" in limpas[3] and "texto comum do meio 4" in limpas[3] and "fim d" in limpas[3]


def test_remover_repetidos_ignora_documento_curto():
    paginas = ["Título\nA", "Título\nB"]
    assert remover_repetidos(paginas) == paginas


def test_pdf_sintetico_com_sumario_e_rotulos(tmp_path):
    caminho = criar_pdf(
        tmp_path / "livro.pdf", ["capa", "1.1 Introdução\ntexto", "1.2 Limites\ntexto"],
        sumario=[[1, "1 Capítulo", 2], [2, "1.1 Introdução", 2], [2, "1.2 Limites", 3]],
        rotulos=[{"startpage": 1, "prefix": "", "style": "D", "firstpagenum": 10}],
    )
    doc = abrir_pdf(caminho)
    assert len(doc.paginas) == 3 and doc.paginas[1].indice == 2
    assert [(e.nivel, e.titulo, e.pagina) for e in doc.sumario][1] == (2, "1.1 Introdução", 2)
    assert doc.paginas[1].rotulo == "10" and doc.paginas[0].rotulo == ""
    assert "Limites" in doc.texto(3) and "Introdução" not in doc.texto(3)
    assert doc.sem_texto is False


def test_pdf_sem_texto(tmp_path):
    caminho = criar_pdf(tmp_path / "vazio.pdf", ["", "", ""])
    assert abrir_pdf(caminho).sem_texto is True


def test_paisagem(tmp_path):
    pagina = abrir_pdf(criar_pdf(tmp_path / "s.pdf", ["slide"], paisagem=True)).paginas[0]
    assert pagina.largura > pagina.altura


def test_arquivo_que_nao_e_pdf(tmp_path):
    falso = tmp_path / "falso.pdf"
    falso.write_text("isto não é um pdf", encoding="utf-8")
    with pytest.raises(PdfInvalido):
        abrir_pdf(falso)


def test_limite_de_paginas(tmp_path):
    doc = abrir_pdf(criar_pdf(tmp_path / "x.pdf", ["a", "b", "c"]), limite_paginas=2)
    assert len(doc.paginas) == 2


@pytest.mark.skipif(not STEWART.is_file(), reason="Stewart ausente")
def test_stewart_real():
    doc = abrir_pdf(STEWART)
    assert len(doc.sumario) == 383
    assert doc.paginas[300].indice == 301 and doc.paginas[300].rotulo == "790"
    assert "Calculo15B" not in doc.texto(433, 433)


@pytest.mark.skipif(not LEITHOLD.is_file(), reason="Leithold ausente")
def test_leithold_escaneado():
    assert abrir_pdf(LEITHOLD, limite_paginas=40).sem_texto is True
