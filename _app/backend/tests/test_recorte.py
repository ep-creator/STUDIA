"""Recorte do exercício na página do livro (PDF montado aqui, com rótulos em negrito como num livro)."""

import pymupdf
import pytest

from estudos.recorte import recortar, rotulos


@pytest.fixture
def livro(tmp_path):
    caminho = tmp_path / "livro.pdf"
    doc = pymupdf.open()
    p = doc.new_page(width=595, height=794)
    # coluna da esquerda: 1, 2 e 3 (3 e 4 dividem a linha); coluna da direita: 10 e 11; rodapé com nota "1."
    for numero, x, y, texto in [(1, 42, 100, "Calcule a integral dupla."), (2, 42, 140, "Ache o volume do sólido."),
                                (3, 42, 200, "x dx"), (4, 170, 200, "y dy"), (10, 309, 100, "Use coordenadas polares."),
                                (11, 309, 160, "Ache a área."), (1, 48, 770, "As dicas estão no site.")]:
        p.insert_text((x, y), f"{numero}.", fontname="helvetica-bold", fontsize=9)
        p.insert_text((x + 14, y), texto, fontname="helvetica", fontsize=9)
    p.insert_text((42, 240), "Texto que fecha a coluna.", fontname="helvetica", fontsize=9)
    doc.save(caminho)
    return caminho


def altura(png: bytes) -> int:
    return pymupdf.Pixmap(png).height


def test_rotulos_em_negrito_com_a_posicao(livro):
    with pymupdf.open(livro) as doc:
        achados = {(r.numero, round(r.x0)) for r in rotulos(doc[0])}
    assert {(1, 42), (2, 42), (3, 42), (4, 170), (10, 309), (11, 309)} <= achados


def test_recorta_do_rotulo_ate_o_seguinte_da_coluna(livro):
    um = recortar(livro, 1, 1)
    assert um is not None and um.startswith(b"\x89PNG")
    assert altura(um) < 60 * 2.5                    # de y≈100 até antes do 2 (y≈140): menos de 60 pontos
    assert recortar(livro, 1, 10) is not None       # coluna da direita


def test_vizinho_na_mesma_linha_fecha_o_recorte(livro):
    tres, quatro = recortar(livro, 1, 3), recortar(livro, 1, 4)
    assert tres is not None and quatro is not None
    assert pymupdf.Pixmap(tres).width < (170 - 42) * 2.5 + 20


def test_nota_de_rodape_nao_conta_e_numero_ausente_nao_recorta(livro):
    assert recortar(livro, 1, 1) is not None        # o "1." do rodapé não deixa o 1 ambíguo
    assert recortar(livro, 1, 7) is None            # não está na página: sem recorte, a tela mostra a página
    assert recortar(livro, 9, 1) is None            # página que não existe
