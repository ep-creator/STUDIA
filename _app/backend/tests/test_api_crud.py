import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.main import create_app


@pytest.fixture
def cliente(tmp_path):
    (tmp_path / "_app").mkdir()
    return TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")


@pytest.fixture
def uid(cliente):
    return cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]


@pytest.fixture
def api(cliente, uid):
    base = f"/api/materias/{uid}"

    class Api:
        def post(self, rota, corpo=None):
            return cliente.post(base + rota, json=corpo if corpo is not None else {})

        def patch(self, rota, corpo):
            return cliente.patch(base + rota, json=corpo)

        def put(self, rota, corpo):
            return cliente.put(base + rota, json=corpo)

        def delete(self, rota):
            return cliente.delete(base + rota)

        def get(self, rota):
            return cliente.get(base + rota)

        def painel(self):
            return self.get("/painel").json()

    return Api()


def test_fluxo_completo(api):
    u = api.post("/unidades", {"numero": 1, "titulo": "Derivadas"}).json()["id"]
    api.post("/eventos", {"tipo": "prova", "data": "2026-09-14", "unidade_id": u})
    t = api.post("/topicos", {"unidade_id": u, "titulo": "Limites"}).json()["id"]
    lista = api.post("/listas", {"codigo": "L1", "titulo": "Lista 1", "unidade_id": u}).json()["id"]
    assert api.post(f"/listas/{lista}/topicos/{t}").status_code == 200
    ids = api.put(f"/listas/{lista}/questoes", [{"rotulo": "1"}, {"rotulo": "2", "linha": 2}]).json()
    assert set(ids) == {"1", "2"}
    painel = api.painel()
    assert painel["listas"][0]["aberta"] is False
    assert painel["unidades"][0]["data_prova"] == "2026-09-14"
    api.patch(f"/topicos/{t}", {"status": "visto"})
    assert api.painel()["listas"][0]["aberta"] is True
    api.patch(f"/listas/{lista}", {"liberacao": "travada"})
    assert api.painel()["listas"][0]["aberta"] is False


def test_unidade_editar_e_remover(api):
    u = api.post("/unidades", {"numero": 1}).json()["id"]
    assert api.patch(f"/unidades/{u}", {"titulo": "Integrais"}).status_code == 200
    assert api.painel()["unidades"][0]["titulo"] == "Integrais"
    assert api.delete(f"/unidades/{u}").status_code == 200
    assert api.painel()["unidades"] == []


def test_unidade_numero_repetido_409(api):
    api.post("/unidades", {"numero": 1})
    assert api.post("/unidades", {"numero": 1}).status_code == 409


def test_remover_unidade_com_lista_409(api):
    u = api.post("/unidades", {"numero": 1}).json()["id"]
    api.post("/listas", {"codigo": "L1", "titulo": "Lista 1", "unidade_id": u})
    assert api.delete(f"/unidades/{u}").status_code == 409


def test_evento_tipo_invalido_422(api):
    assert api.post("/eventos", {"tipo": "palestra", "data": "2026-09-14"}).status_code == 422


def test_cronograma(api):
    u = api.post("/unidades", {"numero": 3}).json()["id"]
    lista = api.post("/listas", {"codigo": "L5", "titulo": "Lista 5", "unidade_id": u}).json()["id"]
    ids = api.put(f"/listas/{lista}/questoes", [{"rotulo": "4"}, {"rotulo": "6(a)"}]).json()
    s = api.post("/sessoes", {"unidade_id": u, "codigo": "P1", "data": "2026-10-25", "foco_md": "Polares"}).json()["id"]
    api.put(f"/sessoes/{s}/questoes", [ids["4"], ids["6(a)"]])
    api.patch(f"/sessoes/{s}", {"feito": True})
    sessao = api.painel()["sessoes"][0]
    assert sessao["feito"] is True and sessao["questao_ids"] == sorted(ids.values())
    assert api.delete(f"/sessoes/{s}").status_code == 200
    assert api.painel()["sessoes"] == []


def test_formulas(api):
    u = api.post("/unidades", {"numero": 3}).json()["id"]
    f = api.post("/formulas", {"unidade_id": u, "titulo": "Polares", "corpo_tex": "dA = r dr d\\theta"}).json()["id"]
    api.patch(f"/formulas/{f}", {"notas_md": "Não esqueça o r"})
    assert api.painel()["formulas"][0]["notas_md"] == "Não esqueça o r"
    api.delete(f"/formulas/{f}")
    assert api.painel()["formulas"] == []


def test_documento_salvar_ler_e_arquivo(cliente, uid, api):
    u = api.post("/unidades", {"numero": 3}).json()["id"]
    r = api.put("/documentos", {"tipo": "resumo", "nome_arquivo": "polares", "titulo": "Polares",
                                "corpo": "# Polares\n\n$r$", "unidade_id": u})
    d = r.json()["id"]
    assert api.get(f"/documentos/{d}").json()["corpo"] == "# Polares\n\n$r$"
    assert [x["titulo"] for x in api.get("/documentos?tipo=resumo").json()] == ["Polares"]
    arquivo = cliente.get(f"/arquivos/{uid}/conteudo/resumos/polares.md")
    assert arquivo.status_code == 200 and "# Polares" in arquivo.text
    assert api.delete(f"/documentos/{d}").status_code == 200
    assert api.get("/documentos").json() == []


def test_arquivo_traversal_422(cliente, uid):
    assert cliente.get(f"/arquivos/{uid}/..%2F..%2Fsegredo.txt").status_code == 422


def test_arquivo_inexistente_404(cliente, uid):
    assert cliente.get(f"/arquivos/{uid}/fontes/nada.pdf").status_code == 404


def test_desfazer_via_api_restaura_topico(api):
    u = api.post("/unidades", {"numero": 1}).json()["id"]
    t = api.post("/topicos", {"unidade_id": u, "titulo": "Limites"}).json()["id"]
    api.patch(f"/topicos/{t}", {"status": "visto"})
    api.post("/historico/desfazer")
    assert api.painel()["topicos"][0]["status"] == "pendente"
