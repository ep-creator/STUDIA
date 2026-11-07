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

ZOOM = 2.5            # 72 dpi × 2,5 ≈ 180 dpi: legível na largura da coluna, sem pesar
MARGEM = 4.0          # pontos em volta do recorte
RODAPE = 45.0         # o fim da página (número, notas) não entra no recorte
_ROTULO = re.compile(r"^(\d{1,3})\.(?:\s|$)")


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


def _ultima_folga(pagina: pymupdf.Page, esquerda: float, direita: float, de: float, ate: float, corpo: float) -> float:
    """Onde cortar entre o fim de um exercício e o rótulo do seguinte. Rente ao rótulo, salvo quando o que vem logo
    acima dele é só letra miúda (os limites de uma integral do próximo exercício, que sobem acima da linha dele): aí o
    corte vai para a faixa vazia antes dessa letra miúda."""
    faixas = sorted(
        (s["bbox"][1], s["bbox"][3], s["size"])
        for b in pagina.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]
        if s["text"].strip() and s["bbox"][2] > esquerda and s["bbox"][0] < direita and s["bbox"][3] > de
        and s["bbox"][1] < ate - 1.5   # o que começa quase na altura do rótulo seguinte já é a linha dele
    )
    corte, fim_ocupado = ate - 2, de
    for i, (y0, y1, _) in enumerate(faixas):
        if y0 - fim_ocupado >= 1.0 and all(t < 0.85 * corpo for _, _, t in faixas[i:]):
            corte = (fim_ocupado + y0) / 2
            break
        fim_ocupado = max(fim_ocupado, y1)
    return corte


def _area(pagina: pymupdf.Page, todos: list[Rotulo], alvo: Rotulo) -> pymupdf.Rect | None:
    largura, altura = pagina.rect.width, pagina.rect.height
    meio = largura / 2
    esquerda = alvo.x0 - MARGEM
    direita = meio + 2 if alvo.x0 < meio else largura - 30
    # dois exercícios curtos na mesma linha: o recorte para antes do vizinho
    lado = [r.x0 for r in todos if abs(r.y0 - alvo.y0) < 4 and alvo.x0 < r.x0 < direita]
    if lado:
        direita = min(lado) - 3
    abaixo = [r.y0 for r in todos if r.y0 > alvo.y0 + 4 and esquerda - 6 <= r.x0 < direita]
    if abaixo:
        fim = _ultima_folga(pagina, esquerda, direita, alvo.y0 + 6, min(abaixo), alvo.tamanho)
    else:
        # o último da coluna: vai até o último texto dela, antes do rodapé
        blocos = [b["bbox"][3] for b in pagina.get_text("dict")["blocks"]
                  if b["bbox"][1] >= alvo.y0 - 1 and b["bbox"][3] < altura - RODAPE
                  and b["bbox"][0] >= esquerda - 6 and b["bbox"][0] < direita]
        fim = (max(blocos) if blocos else altura - RODAPE) + 2
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
