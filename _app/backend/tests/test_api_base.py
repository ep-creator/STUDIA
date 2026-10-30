from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.db.conexao import conectar
from estudos.historico import operacao
from estudos.main import create_app
from estudos.modelos import QuestaoEntrada
from estudos.repos import listas, unidades
from estudos.workspace import criar_materia


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "_app").mkdir()
    return tmp_path


@pytest.fixture
def cliente(workspace):
    app = create_app(carregar_settings(workspace / "_app", workspace))
    return TestClient(app, base_url="http://127.0.0.1:8790")


@pytest.fixture
def materia_com_lista(workspace):
    ref = criar_materia(workspace, "Cálculo 2")
    with closing(conectar(ref.db)) as con, operacao(con, "base") as op:
        u = unidades.criar(op, 1)
        lista = listas.criar(op, "L1", "Lista 1", u, liberacao="aberta")
        qid = listas.sincronizar_questoes(op, lista, [QuestaoEntrada("1"), QuestaoEntrada("2", linha=2)])["1"]
    return ref.uid, qid


def test_criar_e_listar_materia(cliente):
    r = cliente.post("/api/materias", json={"nome": "Física 1"})
    assert r.status_code == 201 and r.json()["nome"] == "Física 1"
    assert [m["nome"] for m in cliente.get("/api/materias").json()] == ["Física 1"]


def test_criar_materia_nome_invalido_422(cliente):
    r = cliente.post("/api/materias", json={"nome": "a/b"})
    assert r.status_code == 422 and "erro" in r.json()


def test_materia_inexistente_404(cliente):
    r = cliente.get("/api/materias/naoexiste/painel")
    assert r.status_code == 404 and "erro" in r.json()


def test_painel_materia_vazia(cliente):
    uid = cliente.post("/api/materias", json={"nome": "EDO"}).json()["uid"]
    painel = cliente.get(f"/api/materias/{uid}/painel").json()
    assert painel["materia"]["nome"] == "EDO"
    assert painel["unidade"] is None and painel["listas"] == [] and painel["unidades"] == []


def test_painel_com_lista(cliente, materia_com_lista):
    uid, qid = materia_com_lista
    painel = cliente.get(f"/api/materias/{uid}/painel").json()
    assert painel["unidade"] == 1 and painel["unidade_atual"] == 1
    assert [q["rotulo"] for q in painel["listas"][0]["questoes"]] == ["1", "2"]
    assert painel["placar"]["total"] == 2


def test_painel_unidade_inexistente_404(cliente, materia_com_lista):
    uid, _ = materia_com_lista
    assert cliente.get(f"/api/materias/{uid}/painel?unidade=9").status_code == 404


def test_marcar_e_desfazer(cliente, materia_com_lista):
    uid, qid = materia_com_lista
    r = cliente.put(f"/api/materias/{uid}/marcacoes/{qid}", json={"estado": "ok"})
    assert r.status_code == 200 and r.json()["placar"]["ok"] == 1
    assert cliente.get(f"/api/materias/{uid}/painel").json()["marcacoes"] == {str(qid): "ok"}
    desfeito = cliente.post(f"/api/materias/{uid}/historico/desfazer", json={}).json()["desfeito"]
    assert desfeito["descricao"].startswith("Marcar questão")
    assert cliente.get(f"/api/materias/{uid}/painel").json()["marcacoes"] == {}


def test_historico_lista_acoes(cliente, materia_com_lista):
    uid, qid = materia_com_lista
    cliente.put(f"/api/materias/{uid}/marcacoes/{qid}", json={"estado": "err"})
    grupos = cliente.get(f"/api/materias/{uid}/historico").json()
    assert grupos[0]["descricao"].startswith("Marcar questão") and grupos[1]["descricao"] == "base"


def test_estado_invalido_422(cliente, materia_com_lista):
    uid, qid = materia_com_lista
    assert cliente.put(f"/api/materias/{uid}/marcacoes/{qid}", json={"estado": "talvez"}).status_code == 422


def test_questao_inexistente_404(cliente, materia_com_lista):
    uid, _ = materia_com_lista
    assert cliente.put(f"/api/materias/{uid}/marcacoes/999", json={"estado": "ok"}).status_code == 404


def test_post_text_plain_403(cliente):
    r = cliente.post("/api/materias", content=b'{"nome": "X"}', headers={"Content-Type": "text/plain"})
    assert r.status_code == 403


def test_apagar_materia_move_a_pasta_para_a_lixeira(cliente):
    uid = cliente.post("/api/materias", json={"nome": "Sistemas Digitais"}).json()["uid"]
    r = cliente.delete(f"/api/materias/{uid}")
    assert r.status_code == 200
    destino = r.json()["movida_para"]
    assert destino.startswith("_lixeira/Sistemas Digitais")
    assert all(m["uid"] != uid for m in cliente.get("/api/materias").json())
    raiz = Path(cliente.app.state.settings.workspace)
    assert not (raiz / "Sistemas Digitais").exists() and (raiz / destino / "materia.db").is_file()


def test_apagar_materia_inexistente_404(cliente):
    assert cliente.delete("/api/materias/nao-existe").status_code == 404


def test_apagar_duas_materias_de_mesmo_nome_no_mesmo_segundo_nao_colide(cliente):
    destinos = []
    for _ in range(2):
        uid = cliente.post("/api/materias", json={"nome": "Sistemas Digitais"}).json()["uid"]
        destinos.append(cliente.delete(f"/api/materias/{uid}").json()["movida_para"])
    raiz = Path(cliente.app.state.settings.workspace)
    assert destinos[0] != destinos[1] and all((raiz / d / "materia.db").is_file() for d in destinos)


def test_apagar_materia_sendo_indexada_409(cliente, monkeypatch):
    from estudos.api import materias as rota
    monkeypatch.setattr(rota, "sincronizando", lambda raiz: True)
    uid = cliente.post("/api/materias", json={"nome": "Sistemas Digitais"}).json()["uid"]
    assert cliente.delete(f"/api/materias/{uid}").status_code == 409
    assert any(m["uid"] == uid for m in cliente.get("/api/materias").json())
