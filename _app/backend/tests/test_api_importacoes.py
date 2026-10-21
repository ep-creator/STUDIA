import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.main import create_app
from pdfs_sinteticos import DISCIPLINA

pytestmark = pytest.mark.skipif(not (DISCIPLINA / "Programa.pdf").is_file(), reason="PDFs reais ausentes")


@pytest.fixture
def cliente(tmp_path):
    (tmp_path / "_app").mkdir()
    return TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")


@pytest.fixture
def base(cliente):
    uid = cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]
    return f"/api/materias/{uid}/importacoes"


def _enviar(cliente, base, nome, conteudo=None):
    dados = conteudo if conteudo is not None else (DISCIPLINA / nome).read_bytes()
    return cliente.post(base, files={"arquivo": (nome, dados, "application/pdf")})


def test_upload_proposta_e_reenvio(cliente, base):
    r = _enviar(cliente, base, "Programa.pdf")
    assert r.status_code == 201
    imp = r.json()
    assert imp["tipo"] == "programa" and len(imp["proposta"]["unidades"]) == 3 and "pendencias" in imp
    again = _enviar(cliente, base, "Programa.pdf")
    assert again.status_code == 200 and again.json()["id"] == imp["id"]
    assert [i["id"] for i in cliente.get(base).json()] == [imp["id"]]


def test_arquivo_que_nao_e_pdf(cliente, base):
    r = _enviar(cliente, base, "notas.pdf", b"apenas texto")
    assert r.status_code == 422 and "erro" in r.json()


def test_pdf_corrompido(cliente, base):
    r = _enviar(cliente, base, "x.pdf", b"%PDF-1.7\n isto quebra")
    assert r.status_code == 422


def test_confirmar_e_confirmar_de_novo(cliente, base):
    imp = _enviar(cliente, base, "Programa.pdf").json()
    r = cliente.post(f"{base}/{imp['id']}/confirmar")
    assert r.status_code == 200 and r.json()["unidades"] == 3
    assert cliente.post(f"{base}/{imp['id']}/confirmar").status_code == 409
    assert cliente.get(f"{base}/{imp['id']}").json()["estado"] == "confirmada"


def test_editar_proposta(cliente, base):
    imp = _enviar(cliente, base, "Programa.pdf").json()
    proposta = imp["proposta"]
    proposta["unidades"] = proposta["unidades"][:1]
    assert cliente.put(f"{base}/{imp['id']}", json=proposta).status_code == 200
    assert cliente.post(f"{base}/{imp['id']}/confirmar").json()["unidades"] == 1


def test_editar_proposta_invalida(cliente, base):
    imp = _enviar(cliente, base, "Programa.pdf").json()
    assert cliente.put(f"{base}/{imp['id']}", json={"listas": []}).status_code == 422


def test_trocar_tipo_e_descartar(cliente, base):
    imp = _enviar(cliente, base, "Programa.pdf").json()
    r = cliente.post(f"{base}/{imp['id']}/tipo", json={"tipo": "outro"})
    assert r.status_code == 200 and r.json()["tipo"] == "outro"
    assert cliente.post(f"{base}/{imp['id']}/descartar").status_code == 200
    assert cliente.post(f"{base}/{imp['id']}/confirmar").status_code == 409


def test_tipo_desconhecido(cliente, base):
    imp = _enviar(cliente, base, "Programa.pdf").json()
    assert cliente.post(f"{base}/{imp['id']}/tipo", json={"tipo": "receita"}).status_code == 422


def test_upload_acima_do_limite(tmp_path):
    app_dir = tmp_path / "_app"
    app_dir.mkdir()
    (app_dir / "config.toml").write_text("[importacao]\nlimite_upload_mb = 0\n", encoding="utf-8")
    cliente = TestClient(create_app(carregar_settings(app_dir, tmp_path)), base_url="http://127.0.0.1:8790")
    uid = cliente.post("/api/materias", json={"nome": "X"}).json()["uid"]
    r = _enviar(cliente, f"/api/materias/{uid}/importacoes", "Programa.pdf")
    assert r.status_code == 413


def test_upload_nao_bloqueia_o_servidor():
    import inspect

    from estudos.api import importacoes as rotas

    assert not inspect.iscoroutinefunction(rotas.enviar)
