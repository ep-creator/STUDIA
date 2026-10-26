"""Vínculos por similaridade de texto: tópico do programa ↔ seção do livro ↔ conteúdo de lista.

Similaridade = Jaccard ponderado pelo IDF dos tokens (palavras raras pesam mais que "integral" ou "função").
"""

import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass

from estudos.importacao.idioma import radicais_relevantes


@dataclass(frozen=True)
class Candidato:
    chave: object
    titulo: str


@dataclass(frozen=True)
class Vinculo:
    chave: object
    titulo: str
    confianca: float


def construir_idf(titulos: list[str]) -> dict[str, float]:
    documentos = [set(radicais_relevantes(t)) for t in titulos]
    frequencia = Counter(token for tokens in documentos for token in tokens)
    total = max(1, len(documentos))
    return {token: math.log(1 + total / df) for token, df in frequencia.items()}


def similaridade(a: str, b: str, idf: dict[str, float]) -> float:
    ta, tb = set(radicais_relevantes(a)), set(radicais_relevantes(b))
    if not ta or not tb:
        return 0.0
    padrao = max(idf.values(), default=1.0)  # token desconhecido conta como raro

    def peso(tokens: set[str]) -> float:
        return sum(idf.get(t, padrao) for t in tokens)

    return peso(ta & tb) / peso(ta | tb)


def _profundidade(c: Candidato) -> int:
    """Nível do código da seção na chave ('14.3' → 1); chaves sem código contam 0."""
    codigo = c.chave[-1] if isinstance(c.chave, tuple) else c.chave
    return codigo.count(".") if isinstance(codigo, str) else 0


def pontuar(
    texto: str, candidatos: list[Candidato], limiar: float, idf: dict[str, float] | None = None
) -> list[tuple[float, Candidato]]:
    """Candidatos com similaridade ≥ limiar, do mais parecido para o menos. Quem compara muitos textos com os mesmos
    candidatos passa o `idf` pronto (construir_idf dos títulos) para não recalculá-lo a cada chamada."""
    if idf is None:
        idf = construir_idf([c.titulo for c in candidatos])
    # Empate de nota: fica a mais específica (seção 14.3 antes do capítulo 14 de mesmo título)
    pontuados = sorted(
        ((similaridade(texto, c.titulo, idf), c) for c in candidatos),
        key=lambda par: (par[0], _profundidade(par[1])), reverse=True,
    )
    return [(s, c) for s, c in pontuados if s >= limiar]


def melhores(
    texto: str, candidatos: list[Candidato], limiar: float, maximo: int = 1, idf: dict[str, float] | None = None
) -> list[Vinculo]:
    pontuados = pontuar(texto, candidatos, limiar, idf)
    vinculos = []
    for i, (score, c) in enumerate(pontuados[:maximo]):
        # Escolha única entre candidatos igualmente parecidos é um chute: a confiança cai pela metade
        empate = (maximo == 1 and i == 0 and len(pontuados) > 1 and math.isclose(pontuados[1][0], score)
                  and _profundidade(pontuados[1][1]) == _profundidade(c))
        vinculos.append(Vinculo(c.chave, c.titulo, round(score / 2 if empate else score, 4)))
    return vinculos


def unidade_majoritaria(votos: list[tuple[int, float]]) -> tuple[int | None, float]:
    """Votos (unidade, força do vínculo). Confiança = fatia da unidade vencedora × seu vínculo mais forte: um único
    vínculo fraco não vira certeza, e votos divididos entre unidades também baixam a confiança."""
    pesos: dict[int, float] = {}
    for unidade, forca in votos:
        pesos[unidade] = pesos.get(unidade, 0.0) + forca
    total = sum(pesos.values())
    if not total:
        return None, 0.0
    unidade = max(pesos, key=pesos.get)
    maior = max(forca for u, forca in votos if u == unidade)
    return unidade, pesos[unidade] / total * maior


# ---------------------------------------------------------------------------------------------------------------
# Documento (resumo, resolução, plano) ↔ seção do livro — spec da peça B, §3.6

_CODIGO_NO_TITULO = re.compile(r"^\D*?(\d+(?:\.\d+)+)")
_FATOR_COMPLEMENTAR = 0.7   # só livro complementar casou o código: nunca passa do limiar de gravar (0,75)
_TIPOS_COM_SECAO = ("resumo", "resolucao", "plano")


@dataclass(frozen=True)
class SugestaoSecao:
    secao_id: int
    codigo: str
    titulo: str
    confianca: float
    por: str          # "questao", "codigo", "palavras" (e, com embeddings, "sentido" ou "ambos")


def _secoes(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute(
        "SELECT s.id, s.codigo, s.titulo, l.papel = 'principal' AS principal "
        "FROM secao_livro s JOIN livro l ON l.fonte_id = s.livro_id ORDER BY principal DESC, l.fonte_id, s.pagina_pdf_ini"
    ).fetchall()


def secao_do_documento(con: sqlite3.Connection, documento, limiar: float) -> SugestaoSecao | None:
    """Seção do livro que o documento cobre, com confiança; None se não há candidato (ou o tipo não tem seção).

    1. resolução de questão → seção da lista da questão (certeza);
    2. código no título → seção com esse código, de preferência no livro principal, conferida pelo título;
    3. sem código → semelhança do título com os títulos das seções.
    """
    if documento.tipo not in _TIPOS_COM_SECAO:
        return None
    secoes = _secoes(con)
    if documento.questao_id is not None:
        linha = con.execute(
            "SELECT ls.secao_id FROM questao q JOIN lista_secao ls ON ls.lista_id = q.lista_id WHERE q.id = ?",
            (documento.questao_id,),
        ).fetchall()
        ids = {r["secao_id"] for r in linha}
        for s in secoes:  # na ordem: livro principal primeiro
            if s["id"] in ids:
                return SugestaoSecao(s["id"], s["codigo"], s["titulo"], 1.0, "questao")
    idf = construir_idf([s["titulo"] for s in secoes])
    achado = _CODIGO_NO_TITULO.match(documento.titulo)
    if achado:
        codigo = achado.group(1)
        resto = documento.titulo.replace(codigo, " ", 1)
        com_codigo = [s for s in secoes if s["codigo"] == codigo]
        if com_codigo:
            melhor = max(com_codigo, key=lambda s: (s["principal"], similaridade(resto, s["titulo"], idf)))
            confianca = 0.5 + 0.5 * similaridade(resto, melhor["titulo"], idf)
            if not melhor["principal"]:
                confianca *= _FATOR_COMPLEMENTAR
            return SugestaoSecao(melhor["id"], melhor["codigo"], melhor["titulo"], round(confianca, 4), "codigo")
    candidatos = [Candidato(s["id"], s["titulo"]) for s in secoes]
    [vinculo] = melhores(documento.titulo, candidatos, limiar, idf=idf) or [None]
    if vinculo is None:
        return None
    secao = next(s for s in secoes if s["id"] == vinculo.chave)
    return SugestaoSecao(secao["id"], secao["codigo"], secao["titulo"], vinculo.confianca, "palavras")
