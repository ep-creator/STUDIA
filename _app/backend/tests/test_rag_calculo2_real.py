"""Índice de busca sobre o Cálculo 2 migrado. O índice vai para uma pasta temporária; o materia.db real só é lido."""

from contextlib import closing

import pytest

from estudos.db.conexao import conectar
from estudos.rag.busca import buscar
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice
from pdfs_sinteticos import REAL

pytestmark = pytest.mark.skipif(not (REAL / "materia.db").is_file(), reason="Cálculo 2 migrado ausente")


@pytest.fixture(scope="module")
def indice_real(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("indice") / "indice.db"
    with closing(conectar(REAL / "materia.db")) as con:
        primeira = sincronizar(con, REAL, caminho)
        segunda = sincronizar(con, REAL, caminho)
    indice = abrir_indice(REAL, caminho)
    yield indice, primeira, segunda
    indice.close()


def test_sincronizacao(indice_real):
    _, primeira, segunda = indice_real
    assert primeira.indexadas > 40 and primeira.trechos > 500
    assert any("sem texto" in a for a in primeira.avisos)  # Leithold escaneado
    assert (segunda.indexadas, segunda.removidas) == (0, 0)


def test_cilindricas_na_unidade_3(indice_real):
    indice, _, _ = indice_real
    r = buscar(indice, "integrais triplas em coordenadas cilíndricas", unidade=3, limite=5)
    assert "15.8" in [x.secao_codigo for x in r[:3]]


def test_lagrange_resumo_e_livro(indice_real):
    indice, _, _ = indice_real
    r = buscar(indice, "multiplicadores de Lagrange", limite=10)
    assert any(x.tipo == "resumo" and "Lagrange" in x.titulo for x in r)
    assert any(x.secao_codigo == "14.8" for x in r)


def test_gabarito(indice_real):
    indice, _, _ = indice_real
    r = buscar(indice, "respostas", tipos=["gabarito"], limite=5)
    assert r and all(x.tipo == "gabarito" for x in r)
