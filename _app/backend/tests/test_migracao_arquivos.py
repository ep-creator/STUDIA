import os

import pytest

from estudos.erros import DadoInvalido
from estudos.migracao.arquivos import vincular_arquivo


@pytest.fixture
def origem(tmp_path):
    caminho = tmp_path / "legado" / "livros" / "Cálculo — Stewart.pdf"
    caminho.parent.mkdir(parents=True)
    caminho.write_bytes(b"%PDF stewart")
    return caminho


def test_hardlink_mesmo_arquivo(origem, tmp_path):
    destino = tmp_path / "Calculo 2" / "fontes" / "livros" / origem.name
    modo = vincular_arquivo(origem, destino)
    if modo == "copia":
        pytest.skip("sistema de arquivos sem hardlink")
    assert modo == "hardlink"
    assert os.stat(origem).st_ino == os.stat(destino).st_ino


def test_fallback_copia(origem, tmp_path, monkeypatch):
    def falhar(*_args, **_kwargs):
        raise OSError("sem suporte a hardlink")

    monkeypatch.setattr(os, "link", falhar)
    destino = tmp_path / "dest" / "a.pdf"
    assert vincular_arquivo(origem, destino) == "copia"
    assert destino.read_bytes() == origem.read_bytes()


def test_existente_igual(origem, tmp_path):
    destino = tmp_path / "dest" / "a.pdf"
    destino.parent.mkdir()
    destino.write_bytes(origem.read_bytes())
    assert vincular_arquivo(origem, destino) == "existente"


def test_destino_diferente_recusa(origem, tmp_path):
    destino = tmp_path / "dest" / "a.pdf"
    destino.parent.mkdir()
    destino.write_bytes(b"outro conteudo")
    with pytest.raises(DadoInvalido):
        vincular_arquivo(origem, destino)
    assert destino.read_bytes() == b"outro conteudo"
