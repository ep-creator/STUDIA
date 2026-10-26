"""Embeddings: o único ponto de troca do provedor (spec da peça B, §3.2). O resto do sistema só pede "o vetor deste texto".

Vetores sempre normalizados (norma 1): o cosseno vira produto escalar. Para modelos e5, trechos levam o prefixo
"passage: " e consultas "query: ", como o modelo exige.
"""

import hashlib
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Protocol

import numpy as np

from estudos.importacao.idioma import radicais_relevantes

log = logging.getLogger(__name__)

# Modelos que o fastembed não traz no catálogo: registrados a partir do ONNX publicado no Hugging Face
MODELOS_CUSTOM = {
    "intfloat/multilingual-e5-small": (384, "onnx/model.onnx"),
    "intfloat/multilingual-e5-base": (768, "onnx/model.onnx"),
}
_LOTE = 64


class Embeddings(Protocol):
    nome: str
    dimensao: int

    def de_trechos(self, textos: list[str]) -> np.ndarray: ...   # n × dimensao, linhas normalizadas

    def de_consulta(self, texto: str) -> np.ndarray: ...         # vetor normalizado


def _normalizar(m: np.ndarray) -> np.ndarray:
    normas = np.linalg.norm(m, axis=-1, keepdims=True)
    return (m / np.where(normas == 0, 1, normas)).astype(np.float32)


class EmbeddingsFalso:
    """Determinístico e sem download, para os testes: soma vetores fixos por radical (textos com radicais em comum ficam
    próximos)."""

    def __init__(self, dimensao: int = 32):
        self.dimensao = dimensao
        self.nome = f"falso-{dimensao}"

    def _vetor(self, texto: str) -> np.ndarray:
        total = np.zeros(self.dimensao, dtype=np.float64)
        for r in radicais_relevantes(texto) or ["vazio"]:
            semente = int.from_bytes(hashlib.sha256(r.encode()).digest()[:8], "little")
            total += np.random.default_rng(semente).standard_normal(self.dimensao)
        return total

    def de_trechos(self, textos: list[str]) -> np.ndarray:
        if not textos:
            return np.zeros((0, self.dimensao), dtype=np.float32)
        return _normalizar(np.stack([self._vetor(t) for t in textos]))

    def de_consulta(self, texto: str) -> np.ndarray:
        return _normalizar(self._vetor(texto)[None, :])[0]


class FastEmbed:
    """Modelo local via fastembed (ONNX Runtime, só CPU). Baixa uma vez para `cache`; depois funciona offline."""

    def __init__(self, modelo: str, cache: Path):
        from fastembed import TextEmbedding

        if modelo in MODELOS_CUSTOM and modelo not in {m["model"] for m in TextEmbedding.list_supported_models()}:
            from fastembed.common.model_description import ModelSource, PoolingType

            dimensao, arquivo = MODELOS_CUSTOM[modelo]
            TextEmbedding.add_custom_model(model=modelo, pooling=PoolingType.MEAN, normalization=True,
                                           sources=ModelSource(hf=modelo), dim=dimensao, model_file=arquivo)
        cache.mkdir(parents=True, exist_ok=True)
        self._modelo = TextEmbedding(modelo, cache_dir=str(cache))
        self.nome = modelo
        self.dimensao = int(self._modelo.embedding_size)
        self._e5 = "e5" in modelo.lower()

    def _embed(self, textos: list[str]) -> np.ndarray:
        if not textos:
            return np.zeros((0, self.dimensao), dtype=np.float32)
        return _normalizar(np.array(list(self._modelo.embed(textos, batch_size=_LOTE))))

    def de_trechos(self, textos: list[str]) -> np.ndarray:
        return self._embed([f"passage: {t}" if self._e5 else t for t in textos])

    def de_consulta(self, texto: str) -> np.ndarray:
        return self._embed([f"query: {texto}" if self._e5 else texto])[0]


_instancias: dict[str, Embeddings] = {}
_falhas: set[str] = set()
_avisos: list[str] = []
_trava = threading.Lock()


def obter_embeddings(settings) -> Embeddings | None:
    """O provedor configurado (um por processo), ou None se desligado ou indisponível (sem internet na primeira vez,
    arquivo corrompido, ONNX incompatível). A falha é avisada uma vez e não volta a tentar neste processo."""
    if not getattr(settings, "embeddings", False):
        return None
    modelo = settings.modelo
    with _trava:
        if modelo in _instancias:
            return _instancias[modelo]
        if modelo in _falhas:
            return None
        try:
            _instancias[modelo] = FastEmbed(modelo, Path(settings.app_dir) / ".modelos")
            return _instancias[modelo]
        except Exception as erro:  # qualquer falha de carga: o app segue pela busca por texto
            _falhas.add(modelo)
            log.warning("modelo de embeddings %s indisponível: %s", modelo, erro)
            _avisos.append(f"modelo de embeddings indisponível ({erro}); usando a busca por texto")
            return None


def avisos_pendentes() -> list[str]:
    """Avisos de carga ainda não mostrados (a próxima sincronização os devolve uma vez)."""
    with _trava:
        pendentes = list(_avisos)
        _avisos.clear()
        return pendentes


# ------------------------------------------------------------------------------------------------------------------
# Vetores do índice em memória: carregados uma vez por arquivo e invalidados a cada sincronização

_cache_vetores: dict[str, tuple[int, np.ndarray, list[int]]] = {}
_geracao: dict[str, int] = {}


def _arquivo(indice: sqlite3.Connection) -> str:
    return str(Path(indice.execute("PRAGMA database_list").fetchone()[2]).resolve())


def invalidar_vetores(caminho: Path | str) -> None:
    chave = str(Path(caminho).resolve())
    _geracao[chave] = _geracao.get(chave, 0) + 1


def vetores_do_indice(indice: sqlite3.Connection) -> tuple[np.ndarray, list[int]]:
    """Matriz (n × dimensão) dos trechos com vetor e os ids na mesma ordem."""
    chave = _arquivo(indice)
    geracao = _geracao.get(chave, 0)
    guardado = _cache_vetores.get(chave)
    if guardado and guardado[0] == geracao:
        return guardado[1], guardado[2]
    linhas = indice.execute("SELECT id, vetor FROM trecho WHERE vetor IS NOT NULL ORDER BY id").fetchall()
    ids = [l[0] for l in linhas]
    matriz = (np.stack([np.frombuffer(l[1], dtype=np.float32) for l in linhas])
              if linhas else np.zeros((0, 0), dtype=np.float32))
    _cache_vetores[chave] = (geracao, matriz, ids)
    return matriz, ids
