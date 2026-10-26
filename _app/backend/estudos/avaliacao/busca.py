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
from estudos.avaliacao.respostas import casa, ler_aceita
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
    acerto5: float                      # resposta aceita (arquivo ou seção) entre os 5 primeiros
    mrr10: float
    por_estilo: dict[str, float]        # acerto@5 por estilo de pergunta
    por_origem: dict[str, float]        # acerto@5 por quem escreveu a pergunta
    acerto5_trecho: float | None        # página/bloco exato entre os 5 primeiros (só perguntas com trecho indicado)
    n_trecho: int
    indexacao_s: float
    p50_ms: float
    p95_ms: float
    memoria_mb: float


def _posicao(nomes, resultados: list[Resultado], aceitas, trecho: bool) -> int | None:
    fontes, documentos = nomes
    for i, r in enumerate(resultados, start=1):
        if any(casa(fontes, documentos, r, a, trecho) for a in aceitas):
            return i
    return None


def _nomes(con: sqlite3.Connection):
    fontes = {r["id"]: (r["titulo"] or "", r["caminho"]) for r in con.execute("SELECT id, titulo, caminho FROM fonte")}
    documentos = {r["id"]: r["titulo"] for r in con.execute("SELECT id, titulo FROM documento")}
    return fontes, documentos


def _por_grupo(posicoes: list[int | None], chaves: list[str]) -> dict[str, float]:
    grupos: dict[str, list[int | None]] = {}
    for pos, chave in zip(posicoes, chaves):
        grupos.setdefault(chave, []).append(pos)
    return {chave: acerto_em(ps, 5) for chave, ps in grupos.items()}


def _provedor(modelo: str | None, provedores: dict[str, Embeddings]) -> Embeddings | None:
    if modelo is None:
        return None
    if modelo in provedores:
        return provedores[modelo]
    e = obter_embeddings(SimpleNamespace(embeddings=True, modelo=modelo, app_dir=_APP_DIR))
    if e is None:
        raise ValueError(f"modelo de embeddings {modelo!r} indisponível")
    return e


def _medir(con, raiz: Path, perguntas: list[PerguntaBusca], config: Configuracao, caminho: Path, provedores,
           ja_indexados: dict[Path, float]) -> LinhaBusca:
    """`ja_indexados`: índices desta rodada (caminho → segundos para indexar); o mesmo modelo não é indexado duas vezes."""
    embeddings = _provedor(config.modelo, provedores)
    tracemalloc.start()
    if caminho in ja_indexados:
        indexacao = ja_indexados[caminho]
    else:
        descartar_indice(raiz, caminho)
        inicio = time.perf_counter()
        sincronizar(con, raiz, caminho_indice_=caminho, embeddings=embeddings)
        indexacao = ja_indexados[caminho] = time.perf_counter() - inicio
    indice = abrir_indice(raiz, caminho)
    nomes = _nomes(con)
    aceitas = [tuple(ler_aceita(a) for a in p.aceitas) for p in perguntas]
    posicoes, trechos, tempos = [], [], []
    try:
        for p, aceitas_p in zip(perguntas, aceitas):
            t0 = time.perf_counter()
            efetivo, resultados = buscar_modo(indice, p.texto, unidade=p.unidade, limite=_LIMITE, modo=config.modo,
                                              embeddings=embeddings)
            if efetivo != config.modo:
                raise ValueError(f"{config.nome}: a busca caiu para {efetivo!r} (sem vetores no índice?)")
            tempos.append((time.perf_counter() - t0) * 1000)
            posicoes.append(_posicao(nomes, resultados, aceitas_p, trecho=False))
            precisas = tuple(a for a in aceitas_p if a.precisa)
            if precisas:
                trechos.append(_posicao(nomes, resultados, precisas, trecho=True))
    finally:
        indice.close()
        _, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    tempos.sort()
    return LinhaBusca(
        nome=config.nome,
        acerto5=acerto_em(posicoes, 5),
        mrr10=mrr(posicoes, 10),
        por_estilo=_por_grupo(posicoes, [p.estilo for p in perguntas]),
        por_origem=_por_grupo(posicoes, [p.origem for p in perguntas]),
        acerto5_trecho=acerto_em(trechos, 5) if trechos else None,
        n_trecho=len(trechos),
        indexacao_s=round(indexacao, 2),
        p50_ms=round(statistics.median(tempos), 1) if tempos else 0.0,
        p95_ms=round(tempos[max(0, round(0.95 * len(tempos)) - 1)], 1) if tempos else 0.0,
        memoria_mb=round(pico / 2**20, 1),
    )


def avaliar(
    con: sqlite3.Connection, raiz: Path, perguntas: list[PerguntaBusca], configuracoes: list[Configuracao], pasta_temp: Path,
    provedores: dict[str, Embeddings] | None = None,
) -> list[LinhaBusca]:
    """`provedores` (nome → Embeddings) substitui os modelos reais, para os testes. Configurações do mesmo modelo
    ("vetor" e "hibrida") usam o mesmo índice temporário e repetem o tempo de indexação medido na primeira."""
    pasta_temp.mkdir(parents=True, exist_ok=True)
    ja_indexados: dict[Path, float] = {}
    return [_medir(con, raiz, perguntas, c, pasta_temp / f"indice-{(c.modelo or 'texto').replace('/', '-')}.db",
                   provedores or {}, ja_indexados)
            for c in configuracoes]
