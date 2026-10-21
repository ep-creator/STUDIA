"""Livro → seções com faixa de páginas do PDF, deslocamento da paginação impressa e faixa do gabarito.

Duas fontes de sumário, nesta ordem: o sumário embutido no PDF (bookmarks) e a página "Sumário" impressa (com
correção dos erros típicos de OCR). Nada é adivinhado: o que não fecha com as regras vira aviso.
"""

import re
from collections import Counter
from dataclasses import dataclass, field

from estudos.importacao.idioma import normalizar
from estudos.importacao.pdf import DocumentoPdf, EntradaSumario

_CODIGO_SUMARIO = re.compile(r"^(?P<cod>\d+(?:\.\d+)*)\s*[-–.]?\s+(?P<tit>.+)$")
_NAO_SECAO = ("exercicio", "revisao", "projeto", "problemas quentes", "verificacao")
_GABARITO = re.compile(r"\b(respostas?|gabarito|solucoes)\b")
_CODIGO_VALIDO = re.compile(r"^\d+(?:\.\d+)?$")
_TOKEN_CODIGO = re.compile(r"^[\dOolI'.]+$")
# Página impressa no fim da linha; o OCR pode trocar dígitos por O/l/I ("1 O 1" = 101)
_LINHA_COM_PAGINA = re.compile(r"^(?P<corpo>.*?),\s*(?P<pg>\d[\dOolI ]*)$")
_TITULO_SUMARIO = re.compile(r"^(?:[ivxlc]+ )?(?:sumario|indice|conteudo)(?: [ivxlc]+)?$")
_ROMANO = re.compile(r"^[ivxlcdm]+$", re.I)
_PAGINAS_PROCURA_SUMARIO = 30
_MAX_TOKENS_CODIGO = 4
_FRACAO_FINAL_GABARITO = 0.7  # o gabarito fica no fim do livro
CONFIANCA_EMBUTIDO = 1.0
CONFIANCA_PAGINA = 0.7


@dataclass
class SecaoExtraida:
    codigo: str
    titulo: str
    nivel: int
    pagina_pdf_ini: int
    pagina_pdf_fim: int
    confianca: float


@dataclass
class LivroExtraido:
    origem: str
    secoes: list[SecaoExtraida] = field(default_factory=list)
    offset_pagina: int | None = None
    gabarito: tuple[int, int] | None = None
    sem_texto: bool = False
    avisos: list[str] = field(default_factory=list)


@dataclass
class _Entrada:
    codigo: str | None
    titulo: str
    nivel: int
    pagina: int


def normalizar_ocr_codigo(token: str) -> str:
    """Corrige o código de seção vindo de OCR: '1 O'→'10', '10. l'→'10.1', "13'"→'13'."""
    t = token.replace(" ", "").replace("'", "")
    t = t.translate(str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1"}))
    t = re.sub(r"\.+", ".", t).strip(".")
    return t


def _chave(codigo: str) -> tuple[int, ...]:
    return tuple(int(p) for p in codigo.split("."))


def _esperados(anterior: tuple[int, ...] | None) -> set[tuple[int, ...]]:
    if anterior is None:
        return {(1,), (1, 1)}
    capitulo = anterior[0]
    if len(anterior) == 1:
        return {(capitulo, 1), (capitulo + 1,)}
    return {(capitulo, anterior[1] + 1), (capitulo + 1,), (capitulo + 1, 1)}


def _offset(doc: DocumentoPdf) -> int | None:
    diferencas = [p.indice - int(p.rotulo) for p in doc.paginas if p.rotulo.isdigit()]
    return Counter(diferencas).most_common(1)[0][0] if diferencas else None


def _fins(entradas: list[_Entrada], ultima_pagina: int, gabarito_ini: int | None) -> list[SecaoExtraida]:
    """Fim de cada seção = início da próxima seção de nível ≤ (ou da próxima entrada de nível 1 sem código) − 1."""
    secoes = []
    limite_final = (gabarito_ini - 1) if gabarito_ini else ultima_pagina
    for i, e in enumerate(entradas):
        if e.codigo is None:
            continue
        fim = limite_final
        for prox in entradas[i + 1:]:
            if (prox.codigo is not None and prox.nivel <= e.nivel) or (prox.codigo is None and prox.nivel == 1):
                fim = prox.pagina - 1
                break
        secoes.append(SecaoExtraida(e.codigo, e.titulo, e.nivel, e.pagina, max(e.pagina, min(fim, limite_final)), 0.0))
    return secoes


def _gabarito(entradas: list[_Entrada], total: int) -> tuple[int, int] | None:
    candidatas = [
        (i, e) for i, e in enumerate(entradas)
        if e.codigo is None and _GABARITO.search(normalizar(e.titulo)) and e.pagina >= _FRACAO_FINAL_GABARITO * total
    ]
    if not candidatas:
        return None
    i, e = candidatas[-1]
    fim = next((p.pagina - 1 for p in entradas[i + 1:] if p.nivel <= e.nivel), total)
    return e.pagina, max(e.pagina, fim)


# ---------------- sumário embutido ----------------
def _do_sumario_embutido(sumario: tuple[EntradaSumario, ...]) -> list[_Entrada]:
    entradas, vistos = [], set()
    for item in sumario:
        if item.pagina < 1:
            continue
        m = _CODIGO_SUMARIO.match(item.titulo.strip())
        if m and not normalizar(m.group("tit")).startswith(_NAO_SECAO) and m.group("cod") not in vistos:
            vistos.add(m.group("cod"))
            entradas.append(_Entrada(m.group("cod"), m.group("tit").strip(), m.group("cod").count(".") + 1, item.pagina))
        elif not m:
            entradas.append(_Entrada(None, item.titulo.strip(), item.nivel, item.pagina))
    return entradas


# ---------------- página "Sumário" ----------------
def _linhas_do_sumario(doc: DocumentoPdf) -> list[str]:
    linhas = []
    for pagina in doc.paginas[:_PAGINAS_PROCURA_SUMARIO]:
        conteudo = [l.strip() for l in pagina.texto.split("\n") if l.strip()]
        if any(_TITULO_SUMARIO.match(normalizar(l)) for l in conteudo):
            linhas += conteudo
    return linhas


def _eh_cabecalho(linha: str) -> bool:
    n = normalizar(linha)
    return not n or bool(_TITULO_SUMARIO.match(n)) or bool(_ROMANO.match(n.replace(" ", ""))) or n.isdigit()


def _codigo_da_linha(tokens: list[str], anterior: tuple[int, ...] | None) -> tuple[str | None, int]:
    """(código, nº de tokens usados). Prefere o sucessor esperado; senão o menor código maior que o anterior."""
    n = 0
    while n < min(len(tokens), _MAX_TOKENS_CODIGO) and _TOKEN_CODIGO.match(tokens[n]):
        n += 1
    candidatos = []
    for k in range(1, n + 1):
        codigo = normalizar_ocr_codigo(" ".join(tokens[:k]))
        if _CODIGO_VALIDO.match(codigo) and k < len(tokens):
            candidatos.append((codigo, k))
    esperados = _esperados(anterior)
    for codigo, k in candidatos:
        if _chave(codigo) in esperados:
            return codigo, k
    for codigo, k in candidatos:
        if anterior is None or _chave(codigo) > anterior:
            return codigo, k
    return None, 0


def _da_pagina_sumario(doc: DocumentoPdf, offset: int, avisos: list[str]) -> list[_Entrada]:
    entradas, buffer, anterior = [], "", None
    for linha in _linhas_do_sumario(doc):
        if _eh_cabecalho(linha):
            continue
        buffer = f"{buffer} {linha}".strip()
        m = _LINHA_COM_PAGINA.match(buffer)
        if not m:
            continue
        buffer = ""
        pagina = int(normalizar_ocr_codigo(m.group("pg"))) + offset
        tokens = m.group("corpo").split()
        codigo, usados = _codigo_da_linha(tokens, anterior)
        titulo = " ".join(tokens[usados:])
        if codigo is None:
            if tokens and _TOKEN_CODIGO.match(tokens[0]):
                avisos.append(f"sumário: '{m.group('corpo')}' fora de ordem; descartado")
                continue
            entradas.append(_Entrada(None, titulo, 1, pagina))
            continue
        anterior = _chave(codigo)
        entradas.append(_Entrada(codigo, titulo, codigo.count(".") + 1, pagina))
    return entradas


def extrair_livro(doc: DocumentoPdf) -> LivroExtraido:
    if doc.sem_texto and not doc.sumario:
        return LivroExtraido("nenhum", sem_texto=True, avisos=["PDF sem texto extraível (escaneado); seções não detectadas"])
    livro = LivroExtraido("nenhum", offset_pagina=_offset(doc))
    if livro.offset_pagina is None:
        livro.avisos.append("páginas sem numeração impressa reconhecível: deslocamento desconhecido")
    total = doc.total_paginas
    if any(_CODIGO_SUMARIO.match(e.titulo.strip()) for e in doc.sumario):
        livro.origem, confianca = "sumario_embutido", CONFIANCA_EMBUTIDO
        entradas = _do_sumario_embutido(doc.sumario)
    elif livro.offset_pagina is not None and _linhas_do_sumario(doc):
        livro.origem, confianca = "pagina_sumario", CONFIANCA_PAGINA
        entradas = _da_pagina_sumario(doc, livro.offset_pagina, livro.avisos)
    else:
        livro.avisos.append("nenhum sumário encontrado")
        return livro
    livro.gabarito = _gabarito(entradas, total)
    livro.secoes = _fins(entradas, total, livro.gabarito[0] if livro.gabarito else None)
    for s in livro.secoes:
        s.confianca = confianca
    return livro
