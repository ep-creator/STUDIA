import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.main import create_app
from estudos.workspace import abrir_materia


@pytest.fixture
def cliente(tmp_path):
    (tmp_path / "_app").mkdir()
    return TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")


@pytest.fixture
def uid(cliente):
    return cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]


DOC = {"tipo": "resumo", "nome_arquivo": "a.md", "titulo": "A", "corpo": "v1"}


def _abrir(cliente, uid):
    did = cliente.put(f"/api/materias/{uid}/documentos", json=DOC).json()["id"]
    return cliente.get(f"/api/materias/{uid}/documentos/{did}").json()


def test_documento_aberto_traz_versao(cliente, uid):
    aberto = _abrir(cliente, uid)
    assert len(aberto["versao"]) == 64


def test_salvar_com_versao_antiga_da_conflito(cliente, uid, tmp_path):
    aberto = _abrir(cliente, uid)
    (abrir_materia(tmp_path, uid).pasta / aberto["caminho"]).write_text("mudado por fora", encoding="utf-8")
    r = cliente.put(f"/api/materias/{uid}/documentos", json={**DOC, "corpo": "v2", "versao_esperada": aberto["versao"]})
    assert r.status_code == 409 and "mudou" in r.json()["erro"]
    assert cliente.get(f"/api/materias/{uid}/documentos/{aberto['id']}").json()["corpo"] == "mudado por fora"


def test_salvar_com_versao_atual_funciona(cliente, uid):
    aberto = _abrir(cliente, uid)
    r = cliente.put(f"/api/materias/{uid}/documentos", json={**DOC, "corpo": "v2", "versao_esperada": aberto["versao"]})
    assert r.status_code == 200
    novo = cliente.get(f"/api/materias/{uid}/documentos/{aberto['id']}").json()
    assert novo["corpo"].strip() == "v2" and novo["versao"] != aberto["versao"]


def test_salvar_sem_versao_continua_como_antes(cliente, uid):
    _abrir(cliente, uid)
    assert cliente.put(f"/api/materias/{uid}/documentos", json={**DOC, "corpo": "v2"}).status_code == 200


def test_criar_com_nome_que_ja_existe_da_conflito_e_nao_apaga(cliente, uid):
    aberto = _abrir(cliente, uid)  # "a.md" com "v1"
    r = cliente.put(f"/api/materias/{uid}/documentos", json={**DOC, "corpo": "", "versao_esperada": ""})
    assert r.status_code == 409 and "existe um documento" in r.json()["erro"]
    assert cliente.get(f"/api/materias/{uid}/documentos/{aberto['id']}").json()["corpo"].strip() == "v1"


def test_criar_com_nome_livre_funciona(cliente, uid):
    r = cliente.put(f"/api/materias/{uid}/documentos", json={**DOC, "nome_arquivo": "novo.md", "versao_esperada": ""})
    assert r.status_code == 200
