"""Classifica um PDF pelo conteúdo das primeiras páginas e pela forma do documento. Cada sinal soma pontos."""

import re
from dataclasses import dataclass

from estudos.importacao.idioma import normalizar
from estudos.importacao.pdf import DocumentoPdf

TIPOS = ("programa", "calendario", "turma", "livro", "lista", "slides", "prova", "anotacao", "outro")
_PAGINAS_ANALISADAS = 2
_CONFIANCA_MINIMA = 0.2
_DATA = re.compile(r"\b\d{1,2}/\d{1,2}\b")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_CABECALHO_UNIDADE = re.compile(r"^(?:\w+ unidade|unidade [\divx]+)$")
_MARCADOR = re.compile(r"^[○◦•▪‣]")
_NUMERADA = re.compile(r"^\d{1,3}\s*[.)]")
_SECAO = re.compile(r"^secao \d+ \d+")
_TITULO_PROVA = re.compile(r"\b(prova|exame|avaliacao)\b")
_SUMARIO_NUMERADO = re.compile(r"^\d+(\.\d+)*\s*[-–.]?\s+\S")


@dataclass(frozen=True)
class Classificacao:
    tipo: str
    confianca: float
    sinais: dict[str, float]


def _pontuar(doc: DocumentoPdf) -> dict[str, float]:
    texto = doc.texto(1, _PAGINAS_ANALISADAS)
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    norm = [normalizar(l) for l in linhas]
    unidas = " ".join(norm)
    total = doc.total_paginas
    pontos = dict.fromkeys(TIPOS, 0.0)

    if any(n in ("programa", "ementa", "conteudo programatico") for n in norm):
        pontos["programa"] += 3
    if sum(1 for n in norm if _CABECALHO_UNIDADE.match(n)) >= 2:
        pontos["programa"] += 2
    if sum(1 for l in linhas if _MARCADOR.match(l)) >= 3:
        pontos["programa"] += 1

    if any(n in ("calendario", "calendario de atividades") for n in norm):
        pontos["calendario"] += 3
    if len(_DATA.findall(texto)) >= 6:
        pontos["calendario"] += 2
    if any(("exame" in n or "prova" in n) and _DATA.search(l) for l, n in zip(linhas, norm)):
        pontos["calendario"] += 1

    for titulo in ("objetivo", "metodologia", "avaliacao", "referencia", "horario"):
        if any(n.startswith(titulo) and len(n) < 40 for n in norm):
            pontos["turma"] += 1
    if _EMAIL.search(texto) and pontos["turma"]:
        pontos["turma"] += 1

    if "lista de exercicios" in unidas or re.search(r"exercicios d[ao] \w+ unidade", unidas):
        pontos["lista"] += 3
    if sum(1 for n in norm if _SECAO.match(n)) >= 3:
        pontos["lista"] += 2
    numeradas = sum(1 for l in linhas if _NUMERADA.match(l))
    if numeradas >= 3:
        pontos["lista"] += 1

    if total >= 100:
        pontos["livro"] += 4
    if sum(1 for e in doc.sumario if _SUMARIO_NUMERADO.match(e.titulo)) >= 10:
        pontos["livro"] += 3

    if doc.paginas and sum(1 for p in doc.paginas if p.largura > p.altura) / len(doc.paginas) >= 0.8:
        pontos["slides"] += 4

    if any(_TITULO_PROVA.search(n) for n in norm[:5]) and numeradas >= 3 and total < 10:
        pontos["prova"] += 3
    return pontos


def classificar(doc: DocumentoPdf, nome_arquivo: str = "") -> Classificacao:
    pontos = _pontuar(doc)
    ordenados = sorted(pontos.items(), key=lambda kv: kv[1], reverse=True)
    (melhor, p1), (_, p2) = ordenados[0], ordenados[1]
    if p1 == 0:
        return Classificacao("outro", _CONFIANCA_MINIMA, pontos)
    return Classificacao(melhor, max(_CONFIANCA_MINIMA, round((p1 - p2) / p1, 2)), pontos)
