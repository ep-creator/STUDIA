"""Avaliação da busca: cada configuração roda num índice temporário (o índice real da matéria não é tocado)."""

import sqlite3
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path

from estudos.avaliacao.gabarito import PerguntaBusca
from estudos.avaliacao.metricas import acerto_em, mrr
from estudos.rag.busca import Resultado, buscar
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice, descartar_indice

_LIMITE = 10


@dataclass(frozen=True)
class Configuracao:
    nome: str
    modo: str            # "texto", "vetor" ou "hibrida"
    modelo: str | None   # nome do modelo de embeddings (None no modo "texto")


@dataclass(frozen=True)
class LinhaBusca:
    nome: str
    acerto5: float
    acerto5_exata: float
    acerto5_parafrase: float
    mrr10: float
    indexacao_s: float
    p50_ms: float
    p95_ms: float
    memoria_mb: float


def _casa(con: sqlite3.Connection, resultado: Resultado, aceita: str) -> bool:
    tipo, valor = aceita.split(":", 1)
    if tipo == "secao":
        return resultado.secao_codigo == valor
    if resultado.documento_id is None:
        return False
    linha = con.execute("SELECT titulo FROM documento WHERE id = ?", (resultado.documento_id,)).fetchone()
    return linha is not None and linha["titulo"] == valor


def _posicao(con: sqlite3.Connection, resultados: list[Resultado], aceitas: tuple[str, ...]) -> int | None:
    for i, r in enumerate(resultados, start=1):
        if any(_casa(con, r, a) for a in aceitas):
            return i
    return None


def _medir(con, raiz: Path, perguntas: list[PerguntaBusca], config: Configuracao, caminho: Path) -> LinhaBusca:
    if config.modo != "texto":
        raise ValueError(f"modo {config.modo!r} ainda não disponível na avaliação")
    descartar_indice(raiz, caminho)
    tracemalloc.start()
    inicio = time.perf_counter()
    sincronizar(con, raiz, caminho_indice_=caminho)
    indexacao = time.perf_counter() - inicio
    indice = abrir_indice(raiz, caminho)
    posicoes, tempos = [], []
    try:
        for p in perguntas:
            t0 = time.perf_counter()
            resultados = buscar(indice, p.texto, unidade=p.unidade, limite=_LIMITE)
            tempos.append((time.perf_counter() - t0) * 1000)
            posicoes.append(_posicao(con, resultados, p.aceitas))
    finally:
        indice.close()
        _, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    por_estilo = {e: [pos for pos, p in zip(posicoes, perguntas) if p.estilo == e] for e in ("exata", "parafrase")}
    tempos.sort()
    return LinhaBusca(
        nome=config.nome,
        acerto5=acerto_em(posicoes, 5),
        acerto5_exata=acerto_em(por_estilo["exata"], 5),
        acerto5_parafrase=acerto_em(por_estilo["parafrase"], 5),
        mrr10=mrr(posicoes, 10),
        indexacao_s=round(indexacao, 2),
        p50_ms=round(statistics.median(tempos), 1) if tempos else 0.0,
        p95_ms=round(tempos[max(0, round(0.95 * len(tempos)) - 1)], 1) if tempos else 0.0,
        memoria_mb=round(pico / 2**20, 1),
    )


def avaliar(
    con: sqlite3.Connection, raiz: Path, perguntas: list[PerguntaBusca], configuracoes: list[Configuracao], pasta_temp: Path
) -> list[LinhaBusca]:
    pasta_temp.mkdir(parents=True, exist_ok=True)
    return [_medir(con, raiz, perguntas, c, pasta_temp / f"{c.nome}.db") for c in configuracoes]
