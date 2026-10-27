import dataclasses
import sqlite3
from pathlib import Path

import numpy as np
import pytest

from estudos.config import Settings
from estudos.ia import embeddings as modulo
from estudos.ia.embeddings import EmbeddingsFalso, obter_embeddings, vetores_do_indice
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import VERSAO_INDICE, abrir_indice, caminho_indice


def test_falso_aproxima_textos_com_palavras_em_comum():
    e = EmbeddingsFalso()
    a, b, c = e.de_trechos(["integral dupla polar", "integrais duplas em polares", "regra da cadeia"])
    assert a @ b > a @ c
    assert np.linalg.norm(e.de_consulta("integral")) == pytest.approx(1.0)


def test_sincronizar_grava_vetores_e_meta(con, materia, cenario_busca):
    e = EmbeddingsFalso()
    sincronizar(con, materia.pasta, embeddings=e)
    indice = abrir_indice(materia.pasta)
    try:
        sem = indice.execute("SELECT count(*) FROM trecho WHERE vetor IS NULL").fetchone()[0]
        meta = dict(indice.execute("SELECT chave, valor FROM meta").fetchall())
        matriz, ids = vetores_do_indice(indice)
    finally:
        indice.close()
    assert sem == 0 and meta == {"modelo": e.nome, "dimensao": str(e.dimensao)}
    assert matriz.shape == (len(ids), e.dimensao) and len(ids) > 0


def test_trocar_de_modelo_refaz_os_vetores(con, materia, cenario_busca):
    sincronizar(con, materia.pasta, embeddings=EmbeddingsFalso(dimensao=16))
    outro = EmbeddingsFalso(dimensao=24)
    sincronizar(con, materia.pasta, embeddings=outro)
    indice = abrir_indice(materia.pasta)
    try:
        matriz, _ = vetores_do_indice(indice)
        meta = dict(indice.execute("SELECT chave, valor FROM meta").fetchall())
    finally:
        indice.close()
    assert matriz.shape[1] == 24 and meta["dimensao"] == "24"


def test_sem_embeddings_indice_fica_valido_e_sem_vetores(con, materia, cenario_busca):
    indice = abrir_indice(materia.pasta)
    try:
        assert indice.execute("SELECT count(*) FROM trecho").fetchone()[0] > 0
        assert indice.execute("SELECT count(*) FROM trecho WHERE vetor IS NOT NULL").fetchone()[0] == 0
        matriz, ids = vetores_do_indice(indice)
    finally:
        indice.close()
    assert matriz.shape[0] == 0 and ids == []


def test_indice_versao_1_e_refeito_sem_erro(con, materia):
    caminho = caminho_indice(materia.pasta)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    antigo = sqlite3.connect(caminho)
    antigo.execute("CREATE TABLE trecho (id INTEGER PRIMARY KEY, texto TEXT)")
    antigo.execute("PRAGMA user_version = 1")
    antigo.commit()
    antigo.close()
    resumo = sincronizar(con, materia.pasta)
    indice = abrir_indice(materia.pasta)
    try:
        assert indice.execute("PRAGMA user_version").fetchone()[0] == VERSAO_INDICE
    finally:
        indice.close()
    assert resumo is not None


def test_falha_ao_carregar_modelo_devolve_none_e_avisa_uma_vez(tmp_path, monkeypatch, caplog):
    def quebra(*_a, **_k):
        raise OSError("sem internet")
    monkeypatch.setattr(modulo, "FastEmbed", quebra)
    modulo._instancias.clear()
    modulo._falhas.clear()
    settings = dataclasses.replace(Settings(workspace=tmp_path, app_dir=tmp_path), embeddings=True)
    assert obter_embeddings(settings) is None
    assert obter_embeddings(settings) is None
    assert sum("sem internet" in r.message for r in caplog.records) == 1
    assert modulo.avisos_pendentes() == ["modelo de embeddings indisponível (sem internet); usando a busca por texto"]
    assert modulo.avisos_pendentes() == []


def test_desligado_devolve_none(tmp_path):
    assert obter_embeddings(Settings(workspace=tmp_path, app_dir=tmp_path)) is None


@pytest.mark.modelo
def test_fastembed_real_gera_vetor(tmp_path):
    app_dir = Path(__file__).resolve().parents[2]  # _app/ (o cache do modelo fica em _app/.modelos/)
    e = obter_embeddings(Settings(workspace=tmp_path, app_dir=app_dir, embeddings=True))
    assert e is not None and e.dimensao == 384
    v = e.de_consulta("centro de massa")
    assert v.shape == (384,) and np.linalg.norm(v) == pytest.approx(1.0, abs=1e-3)
