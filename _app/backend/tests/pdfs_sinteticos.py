"""PDFs de teste gerados com o próprio PyMuPDF (não dependem dos arquivos reais da matéria)."""

from pathlib import Path

import pymupdf

# Arquivos reais de Cálculo 2 (os testes que os usam pulam se a pasta não existir)
REAL = Path(__file__).resolve().parents[3] / "Calculo 2"
FONTES = REAL / "fontes"
DISCIPLINA = FONTES / "documentos"   # programa, calendário, turma, exercícios e as listas 1 e 2
LISTAS = FONTES / "listas"           # listas 3 a 6
LIVROS = FONTES / "livros"
STEWART = LIVROS / "Calculo - James Stewart - 7 Edição - Volume 2.pdf"
GUIDORIZZI = LIVROS / "Guidorizzi H. L.   Um curso de cálculo vol 2 (2013).pdf"
LEITHOLD = LIVROS / "Calculo com Geometria analitica vol 1 - Louis Leithold 3ªed.pdf"


def pdf_real(nome: str) -> Path:
    """PDF real da turma pelo nome: documentos (programa, calendário, listas 1 e 2…) ou a pasta de listas."""
    return DISCIPLINA / nome if (DISCIPLINA / nome).is_file() else LISTAS / nome


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


def criar_pdf_tabela(caminho: Path, titulo: str, tabelas: list[tuple[str, list[list[str]]]]) -> Path:
    """Uma página com tabelas de bordas desenhadas, como um calendário feito no Word. Cada tabela vem com a linha que
    fica logo acima dela ("1ª Unidade"); célula com "\n" tem várias linhas."""
    doc = pymupdf.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.insert_text((40, 40), titulo, fontsize=12)
    y = 70
    for acima, linhas in tabelas:
        if acima:
            pagina.insert_text((40, y), acima, fontsize=11)
        y += 14
        largura = 515 / max(len(l) for l in linhas)
        for linha in linhas:
            altura = 14 * max(c.count("\n") + 1 for c in linha) + 6
            for j, celula in enumerate(linha):
                retangulo = pymupdf.Rect(40 + j * largura, y, 40 + (j + 1) * largura, y + altura)
                pagina.draw_rect(retangulo, color=(0, 0, 0), width=0.6)
                for k, parte in enumerate(celula.split("\n")):
                    pagina.insert_text((retangulo.x0 + 3, retangulo.y0 + 13 + 14 * k), parte, fontsize=9)
            y += altura
        y += 30
    caminho.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(caminho))
    doc.close()
    return caminho
