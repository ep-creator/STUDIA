"""Leitura de PDF com PyMuPDF: páginas de texto limpo, sumário embutido e rótulos de página."""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pymupdf

# Acento solto que o LaTeX coloca antes da letra ("Ciˆencias", "Mudan¸ca") → caractere combinante
_ACENTOS = {"ˆ": "̂", "´": "́", "˜": "̃", "¸": "̧", "`": "̀", "¨": "̈"}
_ACENTO_SOLTO = re.compile(r"([ˆ´˜¸`¨])\s?([A-Za-zı])")
_LIGADURAS = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "": "•"}
_CID = re.compile(r"\(cid:\d+\)")
_ESPACOS = re.compile(r"[ \t ]+")
_DIGITOS = re.compile(r"\d+")
_MIN_PAGINAS_REPETIDOS = 5
_FRACAO_REPETIDO = 0.3
_BORDA = 2               # linhas do topo e do rodapé onde cabeçalhos repetidos aparecem
_MIN_CARACTERES = 10     # página com menos caracteres úteis que isso conta como "sem texto"
_FRACAO_SEM_TEXTO = 0.9


class PdfInvalido(ValueError):
    pass


@dataclass(frozen=True)
class PaginaPdf:
    indice: int
    rotulo: str
    texto: str
    largura: float
    altura: float


@dataclass(frozen=True)
class EntradaSumario:
    nivel: int
    titulo: str
    pagina: int


@dataclass(frozen=True)
class DocumentoPdf:
    paginas: tuple[PaginaPdf, ...]
    sumario: tuple[EntradaSumario, ...]
    metadados: dict[str, str]

    @property
    def sem_texto(self) -> bool:
        if not self.paginas:
            return True
        vazias = sum(1 for p in self.paginas if len("".join(p.texto.split())) < _MIN_CARACTERES)
        return vazias / len(self.paginas) >= _FRACAO_SEM_TEXTO

    def texto(self, ini: int = 1, fim: int | None = None) -> str:
        fim = fim or len(self.paginas)
        return "\n".join(p.texto for p in self.paginas if ini <= p.indice <= fim)


def _juntar_acento(m: re.Match) -> str:
    letra = "i" if m.group(2) == "ı" else m.group(2)
    return unicodedata.normalize("NFC", letra + _ACENTOS[m.group(1)])


def limpar_texto(texto: str) -> str:
    t = _ACENTO_SOLTO.sub(_juntar_acento, texto)
    for de, para in _LIGADURAS.items():
        t = t.replace(de, para)
    t = _CID.sub("", t)
    return "\n".join(_ESPACOS.sub(" ", linha).strip() for linha in t.split("\n"))


def remover_repetidos(paginas: list[str]) -> list[str]:
    """Tira cabeçalhos/rodapés: linha das bordas que se repete (com dígitos normalizados) em ≥ 30% das páginas."""
    if len(paginas) < _MIN_PAGINAS_REPETIDOS:
        return paginas
    linhas = [p.split("\n") for p in paginas]

    def bordas(ls: list[str]) -> set[str]:
        nao_vazias = [l for l in ls if l.strip()]
        return {_DIGITOS.sub("#", l.strip()) for l in nao_vazias[:_BORDA] + nao_vazias[-_BORDA:]}

    contagem = Counter(chave for ls in linhas for chave in bordas(ls))
    repetidas = {chave for chave, n in contagem.items() if n >= _FRACAO_REPETIDO * len(paginas)}
    resultado = []
    for ls in linhas:
        candidatas = bordas(ls)
        resultado.append("\n".join(
            l for l in ls if not (l.strip() and _DIGITOS.sub("#", l.strip()) in repetidas & candidatas)
        ))
    return resultado


def abrir_pdf(caminho: Path, limite_paginas: int | None = None) -> DocumentoPdf:
    try:
        doc = pymupdf.open(str(caminho))
    except Exception as e:  # PyMuPDF levanta tipos variados para arquivo inválido
        raise PdfInvalido(f"Não foi possível abrir {caminho.name} como PDF: {e}") from None
    with doc:
        if not doc.is_pdf:
            raise PdfInvalido(f"{caminho.name} não é um PDF.")
        if doc.needs_pass:
            raise PdfInvalido(f"{caminho.name} está protegido por senha.")
        total = doc.page_count if limite_paginas is None else min(doc.page_count, limite_paginas)
        brutas = [doc[i] for i in range(total)]
        textos = remover_repetidos([limpar_texto(p.get_text()) for p in brutas])
        paginas = tuple(
            PaginaPdf(indice=i + 1, rotulo=p.get_label() or "", texto=textos[i], largura=p.rect.width, altura=p.rect.height)
            for i, p in enumerate(brutas)
        )
        sumario = tuple(EntradaSumario(nivel=n, titulo=limpar_texto(t), pagina=pg) for n, t, pg, *_ in doc.get_toc())
        metadados = {k: v for k, v in (doc.metadata or {}).items() if v}
    return DocumentoPdf(paginas=paginas, sumario=sumario, metadados=metadados)
