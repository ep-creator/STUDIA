import pytest

from estudos.db.conexao import conectar
from estudos.workspace import criar_materia


@pytest.fixture
def materia(tmp_path):
    return criar_materia(tmp_path, "Matéria Teste")


@pytest.fixture
def con(materia):
    conexao = conectar(materia.db)
    yield conexao
    conexao.close()
