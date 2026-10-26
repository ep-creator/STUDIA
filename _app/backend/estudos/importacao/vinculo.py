"""Vínculos por similaridade de texto: tópico do programa ↔ seção do livro ↔ conteúdo de lista.

Similaridade = Jaccard ponderado pelo IDF dos tokens (palavras raras pesam mais que "integral" ou "função").
Com `semantica` (embeddings, opcional), a nota vira (1 − peso) · regra + peso · sentido; sem ela, nada muda.
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
    por: str = "palavras"    # motivo: "palavras", "sentido" (nenhuma palavra em comum) ou "ambos"


_SENTIDO_FORTE = 0.6   # abaixo disso o sentido não conta como motivo do vínculo


class Semantica:
    """Semelhança de sentido entre um texto e títulos, por embeddings, em 0..1 ((1 + cosseno) / 2). Guarda os vetores
    dos títulos de cada lista de candidatos (a importação compara muitos textos com os mesmos candidatos)."""

    def __init__(self, embeddings):
        self._e = embeddings
        self._titulos: dict[tuple[str, ...], object] = {}

    def similaridades(self, texto: str, titulos: list[str]) -> list[float]:
        chave = tuple(titulos)
        if chave not in self._titulos:
            self._titulos[chave] = self._e.de_trechos(list(titulos))
        cos = self._titulos[chave] @ self._e.de_consulta(texto)
        return [max(0.0, min(1.0, (1 + float(c)) / 2)) for c in cos]


def semantica_de(settings) -> "Semantica | None":
    """A semântica dos vínculos, se ligada no config e com o modelo disponível."""
    if not getattr(settings, "vinculos_com_embeddings", False):
        return None
    from estudos.ia.embeddings import obter_embeddings

    e = obter_embeddings(settings)
    return Semantica(e) if e is not None else None


def motivo(regra: float, sentido: float | None) -> str:
    if sentido is None or sentido < _SENTIDO_FORTE:
        return "palavras"
    return "sentido" if regra == 0 else "ambos"


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


def pontuar_com_motivo(
    texto: str, candidatos: list[Candidato], limiar: float, idf: dict[str, float] | None = None,
    semantica=None, peso: float = 0.5,
) -> list[tuple[float, Candidato, str]]:
    """Como `pontuar`, com o motivo de cada nota ("palavras", "sentido" ou "ambos")."""
    if idf is None:
        idf = construir_idf([c.titulo for c in candidatos])
    regras = [similaridade(texto, c.titulo, idf) for c in candidatos]
    sentidos = semantica.similaridades(texto, [c.titulo for c in candidatos]) if semantica is not None else None
    notas = regras if sentidos is None else [(1 - peso) * r + peso * s for r, s in zip(regras, sentidos)]
    # Empate de nota: fica a mais específica (seção 14.3 antes do capítulo 14 de mesmo título)
    pontuados = sorted(
        ((n, c, motivo(r, None if sentidos is None else sentidos[i])) for i, (n, r, c) in enumerate(zip(notas, regras, candidatos))),
        key=lambda trio: (trio[0], _profundidade(trio[1])), reverse=True,
    )
    return [t for t in pontuados if t[0] >= limiar]


def pontuar(
    texto: str, candidatos: list[Candidato], limiar: float, idf: dict[str, float] | None = None,
    semantica=None, peso: float = 0.5,
) -> list[tuple[float, Candidato]]:
    """Candidatos com nota ≥ limiar, do mais parecido para o menos. Quem compara muitos textos com os mesmos
    candidatos passa o `idf` pronto (construir_idf dos títulos) para não recalculá-lo a cada chamada."""
    return [(n, c) for n, c, _ in pontuar_com_motivo(texto, candidatos, limiar, idf, semantica, peso)]


def melhores(
    texto: str, candidatos: list[Candidato], limiar: float, maximo: int = 1, idf: dict[str, float] | None = None,
    semantica=None, peso: float = 0.5,
) -> list[Vinculo]:
    pontuados = pontuar_com_motivo(texto, candidatos, limiar, idf, semantica, peso)
    vinculos = []
    for i, (score, c, por) in enumerate(pontuados[:maximo]):
        # Escolha única entre candidatos igualmente parecidos é um chute: a confiança cai pela metade
        empate = (maximo == 1 and i == 0 and len(pontuados) > 1 and math.isclose(pontuados[1][0], score)
                  and _profundidade(pontuados[1][1]) == _profundidade(c))
        vinculos.append(Vinculo(c.chave, c.titulo, round(score / 2 if empate else score, 4), por))
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


def secao_do_documento(
    con: sqlite3.Connection, documento, limiar: float, semantica=None, peso: float = 0.5
) -> SugestaoSecao | None:
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
            def confere(s) -> float:  # o título confere com o da seção (regra, ou regra + sentido)
                regra = similaridade(resto, s["titulo"], idf)
                if semantica is None:
                    return regra
                return (1 - peso) * regra + peso * semantica.similaridades(resto, [s["titulo"]])[0]

            melhor = max(com_codigo, key=lambda s: (s["principal"], confere(s)))
            confianca = 0.5 + 0.5 * confere(melhor)
            if not melhor["principal"]:
                confianca *= _FATOR_COMPLEMENTAR
            return SugestaoSecao(melhor["id"], melhor["codigo"], melhor["titulo"], round(confianca, 4), "codigo")
    candidatos = [Candidato(s["id"], s["titulo"]) for s in secoes]
    [vinculo] = melhores(documento.titulo, candidatos, limiar, idf=idf, semantica=semantica, peso=peso) or [None]
    if vinculo is None:
        return None
    secao = next(s for s in secoes if s["id"] == vinculo.chave)
    confianca = vinculo.confianca if secao["principal"] else round(vinculo.confianca * _FATOR_COMPLEMENTAR, 4)
    return SugestaoSecao(secao["id"], secao["codigo"], secao["titulo"], confianca, vinculo.por)
