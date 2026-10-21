import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from estudos.seguranca import CaminhoInvalido, OrigemLocalMiddleware, caminho_seguro


@pytest.mark.parametrize(
    "rel",
    ["../Calculo 2 - backup/x.pdf", "..\\x", "C:\\Windows\\x", "\\\\srv\\x", "/etc/passwd", "a/../../b"],
)
def test_caminho_seguro_rejeita(tmp_path, rel):
    base = tmp_path / "Calculo 2"
    base.mkdir()
    with pytest.raises(CaminhoInvalido):
        caminho_seguro(base, rel)


def test_caminho_seguro_aceita_subpasta(tmp_path):
    assert caminho_seguro(tmp_path, "fontes/livros/a b.pdf") == (tmp_path / "fontes/livros/a b.pdf").resolve()


@pytest.fixture
def cliente():
    app = FastAPI()

    @app.get("/x")
    def ler():
        return {"ok": True}

    @app.post("/x")
    def gravar():
        return {"ok": True}

    app.add_middleware(OrigemLocalMiddleware, porta=8790)
    return TestClient(app, base_url="http://127.0.0.1:8790")


def test_post_origem_estrangeira_bloqueado(cliente):
    r = cliente.post("/x", json={}, headers={"Origin": "https://malicioso.com"})
    assert r.status_code == 403


def test_post_text_plain_bloqueado(cliente):
    assert cliente.post("/x", content=b"{}", headers={"Content-Type": "text/plain"}).status_code == 403


def test_host_estrangeiro_bloqueado(cliente):
    assert cliente.get("/x", headers={"Host": "evil.com"}).status_code == 403


def test_post_local_json_permitido(cliente):
    assert cliente.post("/x", json={}, headers={"Origin": "http://127.0.0.1:8790"}).status_code == 200


def test_post_sem_corpo_permitido(cliente):
    assert cliente.post("/x").status_code == 200
