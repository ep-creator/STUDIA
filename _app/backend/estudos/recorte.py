"""Recorte do exercício na página do livro: só o pedaço em que ele está escrito, como imagem.

O texto extraído de um livro de cálculo sai quebrado (∭ vira "xxx", √ vira "s", as colunas se misturam), então o
enunciado de verdade é a própria página. Mas a página inteira tem dezenas de exercícios: o estudante teria de procurar
o dele. Aqui o recorte vai do rótulo do exercício ("13.", em negrito, como os livros numeram) até o rótulo seguinte na
mesma coluna (ou até o vizinho ao lado, quando dois exercícios curtos dividem a linha).

Nada é adivinhado: sem achar o rótulo com segurança, não há recorte e a tela mostra a página inteira.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pymupdf

ZOOM = 3.0            # 72 dpi × 3 = 216 dpi: nítido mesmo quando a tela amplia um exercício de uma linha só
MARGEM = 4.0          # pontos em volta do recorte
RODAPE = 45.0         # o fim da página (número, notas) não entra no recorte
_ROTULO = re.compile(r"^(\d{1,3})\.(?!\d)")   # "13." ou "5.Calcule" (sem espaço), mas não "2.5"


@dataclass(frozen=True)
class Rotulo:
    numero: int
    x0: float
    y0: float
    tamanho: float    # corpo da letra do rótulo (o texto do exercício tem o mesmo)
    texto: str        # o resto da linha depois do rótulo (para escolher entre rótulos repetidos)


def _normal(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFD", texto)
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in sem_acento if not unicodedata.combining(c)).lower()).strip()


def rotulos(pagina: pymupdf.Page) -> list[Rotulo]:
    """Rótulos de exercício da página: linhas que começam com "N." cujo primeiro trecho está em negrito."""
    achados = []
    for bloco in pagina.get_text("dict")["blocks"]:
        for linha in bloco.get("lines", []):
            spans = linha["spans"]
            if not spans:
                continue
            texto = "".join(s["text"] for s in spans).strip()
            m = _ROTULO.match(texto)
            negrito = "bold" in spans[0]["font"].lower() or bool(spans[0]["flags"] & 16)
            if m and negrito:
                x0, y0 = linha["bbox"][0], linha["bbox"][1]
                achados.append(Rotulo(int(m.group(1)), x0, y0, spans[0]["size"], texto[m.end():].strip()))
    return achados


SUBIDA_MAXIMA = 40.0   # até onde o começo do próximo exercício pode subir acima do rótulo dele (integral com limites)


def _ultima_folga(pagina: pymupdf.Page, esquerda: float, direita: float, de: float, ate: float) -> float:
    """Onde cortar entre o fim de um exercício e o rótulo do seguinte.

    O que cruza a linha do rótulo seguinte é dele: o sinal de integral (mais alto que a linha) e, acima, os limites, que
    cruzam o topo do sinal. O topo do próximo exercício sobe por esses trechos encadeados; o corte fica no meio do vão
    entre esse topo e o fim do que veio antes. Sem nada cruzando, o corte é rente ao rótulo."""
    trechos = [
        (s["bbox"][1], s["bbox"][3])
        for b in pagina.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]
        if s["text"].strip() and s["bbox"][2] > esquerda and s["bbox"][0] < direita and s["bbox"][3] > de
    ]
    topo = ate
    while True:
        cruzam = [y0 for y0, y1 in trechos if y0 < topo - 0.3 and y1 > topo + 0.3]
        if not cruzam or ate - min(cruzam) > SUBIDA_MAXIMA:
            break
        topo = min(cruzam)
    antes = [y1 for y0, y1 in trechos if y1 <= topo + 0.3]
    return (max(antes) + topo) / 2 if antes else topo - 2


def _area(pagina: pymupdf.Page, todos: list[Rotulo], alvo: Rotulo) -> pymupdf.Rect | None:
    largura, altura = pagina.rect.width, pagina.rect.height
    meio = largura / 2
    esquerda = alvo.x0 - MARGEM
    # duas colunas (como o livro) só quando há rótulo na metade direita; lista da turma em LaTeX tem uma coluna só
    duas_colunas = any(r.x0 >= meio - 10 for r in todos)
    direita = (meio + 2 if alvo.x0 < meio else largura - 30) if duas_colunas else largura - 20
    # dois exercícios curtos na mesma linha: o recorte para antes do vizinho
    lado = [r.x0 for r in todos if abs(r.y0 - alvo.y0) < 4 and alvo.x0 < r.x0 < direita]
    if lado:
        direita = min(lado) - 3
    abaixo = [r.y0 for r in todos if r.y0 > alvo.y0 + 4 and esquerda - 6 <= r.x0 < direita]
    if abaixo:
        fim = _ultima_folga(pagina, esquerda, direita, alvo.y0 + 6, min(abaixo))
    else:
        # o último da coluna: vai até o último texto dela, antes do rodapé
        blocos = [b["bbox"][3] for b in pagina.get_text("dict")["blocks"]
                  if b["bbox"][1] >= alvo.y0 - 1 and b["bbox"][3] < altura - RODAPE
                  and b["bbox"][0] >= esquerda - 6 and b["bbox"][0] < direita]
        fim = (max(blocos) if blocos else altura - RODAPE) + 2
    # a direita vai até onde o texto chega (uma coluna só deixaria um vazio que encolhe tudo na tela)
    fins = [sp["bbox"][2] for b in pagina.get_text("dict")["blocks"] for l in b.get("lines", []) for sp in l["spans"]
            if sp["text"].strip() and sp["bbox"][1] >= alvo.y0 - 4 and sp["bbox"][3] <= fim + 2
            and sp["bbox"][0] >= esquerda - 2 and sp["bbox"][2] <= direita + 2]
    if fins:
        direita = min(direita, max(fins) + MARGEM)
    area = pymupdf.Rect(esquerda, alvo.y0 - 3, direita, fim)
    if area.height < 8 or area.height > 0.8 * altura or area.width < 20:
        return None
    return area


def recortar(pdf: Path, pagina: int, numero: int, dica: str | None = None) -> bytes | None:
    """PNG do exercício `numero` na `pagina` (1 = primeira) do PDF, ou None se o rótulo não for achado com segurança.

    `dica` é o texto do índice para o exercício (ou a resposta): com o mesmo número mais de uma vez na página (as
    respostas de várias seções), vale o rótulo cuja linha aparece nela."""
    with pymupdf.open(pdf) as doc:
        if not 1 <= pagina <= doc.page_count:
            return None
        p = doc[pagina - 1]
        todos = rotulos(p)
        # notas de rodapé também começam com "1." em negrito: o que fica no rodapé não é exercício
        candidatos = [r for r in todos if r.numero == numero and r.y0 < p.rect.height - RODAPE]
        if not candidatos:
            return None
        if len(candidatos) > 1:
            if not dica:
                return None
            alvo_dica = _normal(dica)
            casam = [r for r in candidatos if r.texto and _normal(r.texto)[:24] in alvo_dica]
            if len(casam) != 1:
                return None
            candidatos = casam
        area = _area(p, todos, candidatos[0])
        if area is None:
            return None
        return p.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=area).tobytes("png")


def recortar_em(pdf: Path, paginas: list[int] | None, numero: int, dica: str | None = None) -> bytes | None:
    """Como `recortar`, procurando nas páginas dadas (ou em todas, para PDFs curtos como as listas da turma)."""
    if paginas is None:
        with pymupdf.open(pdf) as doc:
            if doc.page_count > 40:
                return None
            paginas = list(range(1, doc.page_count + 1))
    for pagina in paginas:
        png = recortar(pdf, pagina, numero, dica)
        if png is not None:
            return png
    return None


def pagina_do_rotulo(pdf: Path, paginas: list[int], numero: int) -> int | None:
    """A primeira das páginas dadas em que o rótulo do exercício aparece (fora do rodapé), ou None."""
    with pymupdf.open(pdf) as doc:
        for pagina in paginas:
            if not 1 <= pagina <= doc.page_count:
                continue
            p = doc[pagina - 1]
            if any(r.numero == numero and r.y0 < p.rect.height - RODAPE for r in rotulos(p)):
                return pagina
    return None

