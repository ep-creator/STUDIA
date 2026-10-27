"""Divisão de texto em trechos para o índice: por parágrafo, sem cortar no meio quando cabe no limite."""

import re
from dataclasses import dataclass

from estudos.conteudo import analisar_md

LIMITE_TRECHO = 1600  # caracteres
_PARAGRAFO = re.compile(r"\n\s*\n")
_SEPARADOR = "\n\n"


@dataclass(frozen=True)
class TrechoNovo:
    titulo: str
    texto: str
    pagina: int | None
    ordem: int
    pagina_fim: int | None = None   # última página que o trecho cobre (páginas curtas se juntam num trecho só)
    parte: str = "teoria"           # "teoria", "exercicio" ou "resposta" (só livros com seções têm as outras)
    numero: int | None = None       # número do exercício ou da resposta
    secao_id: int | None = None     # seção do livro, quando o corte já a conhece


def _cortar(paragrafo: str, limite: int) -> list[str]:
    """Parágrafo maior que o limite é cortado na última fronteira de frase que cabe (ou no limite, se não houver)."""
    partes = []
    resto = paragrafo
    while len(resto) > limite:
        corte = resto.rfind(". ", 0, limite)
        corte = corte + 1 if corte > 0 else limite
        partes.append(resto[:corte].strip())
        resto = resto[corte:].strip()
    if resto:
        partes.append(resto)
    return partes


def _agrupar(pecas: list[tuple[int | None, str]], titulo: str, limite: int, ordem_inicial: int = 1) -> list[TrechoNovo]:
    trechos: list[TrechoNovo] = []
    atual: list[str] = []
    pagina_atual: int | None = None
    pagina_ultima: int | None = None

    def fechar() -> None:
        if atual:
            trechos.append(TrechoNovo(titulo, _SEPARADOR.join(atual), pagina_atual, ordem_inicial + len(trechos), pagina_ultima))

    for pagina, texto in pecas:
        for parte in _cortar(texto, limite):
            if atual and len(_SEPARADOR.join(atual)) + len(_SEPARADOR) + len(parte) > limite:
                fechar()
                atual = []
            if not atual:
                pagina_atual = pagina
            pagina_ultima = pagina
            atual.append(parte)
    fechar()
    return trechos


def dividir_paginas(paginas: list[tuple[int, str]], titulo: str, limite: int = LIMITE_TRECHO) -> list[TrechoNovo]:
    pecas = [
        (numero, p.strip()) for numero, texto in paginas for p in _PARAGRAFO.split(texto or "") if p.strip()
    ]
    return _agrupar(pecas, titulo, limite)


def dividir_markdown(texto: str, titulo: str, limite: int = LIMITE_TRECHO) -> list[TrechoNovo]:
    """Um ou mais trechos por bloco '## …'; o texto antes do primeiro '##' leva só o título do documento."""
    corpo = analisar_md(texto or "").corpo.replace("\r", "")
    blocos: list[tuple[str, list[str]]] = [(titulo, [])]
    for linha in corpo.split("\n"):
        if linha.startswith("## "):
            blocos.append((f"{titulo} — {linha[3:].strip()}", [linha]))
        else:
            blocos[-1][1].append(linha)
    trechos: list[TrechoNovo] = []
    for titulo_bloco, linhas in blocos:
        pecas = [(None, p.strip()) for p in _PARAGRAFO.split("\n".join(linhas)) if p.strip()]
        trechos += _agrupar(pecas, titulo_bloco, limite, ordem_inicial=len(trechos) + 1)
    return trechos
