"""PDFs de teste gerados com o próprio PyMuPDF (não dependem dos arquivos reais da matéria)."""

from pathlib import Path

import pymupdf

# Arquivos reais de Cálculo 2 (os testes que os usam pulam se a pasta não existir)
REAL = Path(__file__).resolve().parents[3] / "Calculo 2"
DISCIPLINA = REAL / "disciplina"
LIVROS = REAL / "livros"
STEWART = LIVROS / "Calculo - James Stewart - 7 Edição - Volume 2.pdf"
GUIDORIZZI = LIVROS / "Guidorizzi H. L.   Um curso de cálculo vol 2 (2013).pdf"
LEITHOLD = LIVROS / "Calculo com Geometria analitica vol 1 - Louis Leithold 3ªed.pdf"


def criar_pdf(
    caminho: Path,
    paginas: list[str],
    sumario: list[list] | None = None,
    paisagem: bool = False,
    rotulos: list[dict] | None = None,
) -> Path:
    """Cria um PDF com uma página por texto. `sumario` no formato de `set_toc` ([nível, título, página])."""
    doc = pymupdf.open()
    largura, altura = (842, 595) if paisagem else (595, 842)
    for texto in paginas:
        pagina = doc.new_page(width=largura, height=altura)
        y = 50
        for linha in texto.split("\n"):
            if linha:
                pagina.insert_text((40, y), linha, fontsize=10)
            y += 14
    if sumario:
        doc.set_toc(sumario)
    if rotulos:
        doc.set_page_labels(rotulos)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(caminho))
    doc.close()
    return caminho
