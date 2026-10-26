"""Avaliação dos vínculos (tópico → seção, lista → unidade, documento → seção) contra o gabarito, sem gravar nada.

Usa as mesmas funções da importação (`melhores`, `secao_do_documento`). As listas do Cálculo 2 vieram da migração, sem os
conteúdos lidos do PDF; o título da lista faz o papel deles na comparação com os tópicos.
"""

import sqlite3
from dataclasses import dataclass

from estudos.avaliacao.gabarito import GabaritoVinculos
from estudos.importacao.vinculo import Candidato, construir_idf, melhores, secao_do_documento
from estudos.repos import documentos, livros


@dataclass(frozen=True)
class ConfigVinculo:
    nome: str
    semantica: object | None = None   # Semantica (Task 9); None = só regra
    peso: float = 0.5


@dataclass(frozen=True)
class LinhaVinculo:
    nome: str
    tipo: str                 # "topicos", "listas", "documentos" ou "total"
    acertos: int
    total: int
    erros_confiantes: int     # escolha errada com confiança ≥ limiar de gravar (entraria sem revisão)
    para_revisao: int         # escolha com confiança abaixo do limiar (iria para revisão)


def _conta(nome, tipo, resultados: list[tuple[bool, object, float]], limiar_gravar: float) -> LinhaVinculo:
    return LinhaVinculo(
        nome, tipo,
        acertos=sum(1 for certo, _, _ in resultados if certo),
        total=len(resultados),
        erros_confiantes=sum(1 for certo, escolha, conf in resultados if not certo and escolha is not None and conf >= limiar_gravar),
        para_revisao=sum(1 for _, escolha, conf in resultados if escolha is not None and conf < limiar_gravar),
    )


def _avaliar_um(con, gabarito: GabaritoVinculos, config: ConfigVinculo, limiar_vinculo, limiar_gravar) -> list[LinhaVinculo]:
    principal = livros.principal(con)
    secoes = livros.listar_secoes(con, principal.fonte_id) if principal else []
    cand_secoes = [Candidato(s.codigo, f"{s.codigo} {s.titulo}") for s in secoes]
    idf_secoes = construir_idf([c.titulo for c in cand_secoes])
    topicos = con.execute("SELECT t.titulo, u.numero FROM topico t JOIN unidade u ON u.id = t.unidade_id").fetchall()
    cand_topicos = [Candidato(numero, titulo) for titulo, numero in topicos]
    idf_topicos = construir_idf([c.titulo for c in cand_topicos])

    sentido = {"semantica": config.semantica, "peso": config.peso} if config.semantica is not None else {}

    def um(texto, candidatos, idf):
        [v] = melhores(texto, candidatos, limiar_vinculo, idf=idf, **sentido) or [None]
        return (v.chave, v.confianca) if v else (None, 0.0)

    res_topicos = []
    for item in gabarito.topicos:
        escolha, conf = um(item.titulo, cand_secoes, idf_secoes)
        res_topicos.append(((escolha in item.secoes) if escolha else not item.secoes, escolha, conf))
    res_listas = []
    for item in gabarito.listas:
        escolha, conf = um(item.titulo, cand_topicos, idf_topicos)
        res_listas.append((escolha == item.unidade, escolha, conf))
    por_titulo = {d.titulo: d for d in documentos.listar(con)}
    res_docs = []
    for item in gabarito.documentos:
        doc = por_titulo.get(item.titulo)
        if doc is None:
            raise ValueError(f"documento do gabarito não existe na matéria: {item.titulo!r}")
        # a avaliação vê o documento como se ainda não tivesse seção (mede a regra, não a ligação já gravada)
        s = secao_do_documento(con, doc, limiar_vinculo, **sentido)
        escolha, conf = (s.codigo, s.confianca) if s else (None, 0.0)
        res_docs.append(((escolha in item.secoes) if escolha else not item.secoes, escolha, conf))
    linhas = [
        _conta(config.nome, "topicos", res_topicos, limiar_gravar),
        _conta(config.nome, "listas", res_listas, limiar_gravar),
        _conta(config.nome, "documentos", res_docs, limiar_gravar),
    ]
    return linhas + [_conta(config.nome, "total", res_topicos + res_listas + res_docs, limiar_gravar)]


def avaliar(
    con: sqlite3.Connection, gabarito: GabaritoVinculos, configuracoes: list[ConfigVinculo], limiar_vinculo: float,
    limiar_gravar: float,
) -> list[LinhaVinculo]:
    return [linha for c in configuracoes for linha in _avaliar_um(con, gabarito, c, limiar_vinculo, limiar_gravar)]
