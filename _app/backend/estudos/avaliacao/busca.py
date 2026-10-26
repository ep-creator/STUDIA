"""Avaliação da busca: cada configuração roda num índice temporário (o índice real da matéria não é tocado)."""

import sqlite3
import statistics
import time
import tracemalloc
from types import SimpleNamespace
from dataclasses import dataclass
from pathlib import Path

from estudos.avaliacao.gabarito import PerguntaBusca
from estudos.avaliacao.metricas import acerto_em, mrr
from estudos.ia.embeddings import Embeddings, obter_embeddings
from estudos.rag.busca import Resultado, buscar_modo
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice, descartar_indice

_LIMITE = 10
_APP_DIR = Path(__file__).resolve().parents[3]   # _app/ (cache dos modelos em _app/.modelos/)


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


def _provedor(modelo: str | None, provedores: dict[str, Embeddings]) -> Embeddings | None:
    if modelo is None:
        return None
    if modelo in provedores:
        return provedores[modelo]
    e = obter_embeddings(SimpleNamespace(embeddings=True, modelo=modelo, app_dir=_APP_DIR))
    if e is None:
        raise ValueError(f"modelo de embeddings {modelo!r} indisponível")
    return e


def _medir(con, raiz: Path, perguntas: list[PerguntaBusca], config: Configuracao, caminho: Path, provedores) -> LinhaBusca:
    embeddings = _provedor(config.modelo, provedores)
    descartar_indice(raiz, caminho)
    tracemalloc.start()
    inicio = time.perf_counter()
    sincronizar(con, raiz, caminho_indice_=caminho, embeddings=embeddings)
    indexacao = time.perf_counter() - inicio
    indice = abrir_indice(raiz, caminho)
    posicoes, tempos = [], []
    try:
        for p in perguntas:
            t0 = time.perf_counter()
            efetivo, resultados = buscar_modo(indice, p.texto, unidade=p.unidade, limite=_LIMITE, modo=config.modo,
                                              embeddings=embeddings)
            if efetivo != config.modo:
                raise ValueError(f"{config.nome}: a busca caiu para {efetivo!r} (sem vetores no índice?)")
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
    con: sqlite3.Connection, raiz: Path, perguntas: list[PerguntaBusca], configuracoes: list[Configuracao], pasta_temp: Path,
    provedores: dict[str, Embeddings] | None = None,
) -> list[LinhaBusca]:
    """`provedores` (nome → Embeddings) substitui os modelos reais, para os testes."""
    pasta_temp.mkdir(parents=True, exist_ok=True)
    return [_medir(con, raiz, perguntas, c, pasta_temp / f"{c.nome.replace(':', '-')}.db", provedores or {})
            for c in configuracoes]
