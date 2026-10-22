import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.main import create_app


@pytest.fixture(scope="module")
def openapi(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("ws")
    (raiz / "_app").mkdir()
    cliente = TestClient(create_app(carregar_settings(raiz / "_app", raiz)), base_url="http://127.0.0.1:8790")
    return cliente.get("/openapi.json").json()


ROTAS_DO_FRONTEND = [
    ("get", "/api/materias"), ("post", "/api/materias"),
    ("get", "/api/materias/{materia_uid}/painel"),
    ("get", "/api/materias/{materia_uid}/importacoes"), ("get", "/api/materias/{materia_uid}/importacoes/{importacao_id}"),
    ("post", "/api/materias/{materia_uid}/importacoes/{importacao_id}/confirmar"),
    ("get", "/api/materias/{materia_uid}/historico"), ("get", "/api/materias/{materia_uid}/historico/{grupo_id}"),
    ("post", "/api/materias/{materia_uid}/historico/desfazer"),
    ("get", "/api/materias/{materia_uid}/documentos"), ("get", "/api/materias/{materia_uid}/documentos/{documento_id}"),
    ("put", "/api/materias/{materia_uid}/documentos"),
    ("get", "/api/materias/{materia_uid}/fontes"), ("get", "/api/materias/{materia_uid}/fontes/{fonte_id}/secoes"),
    ("put", "/api/materias/{materia_uid}/marcacoes/{questao_id}"),
    ("get", "/api/materias/{materia_uid}/busca"), ("post", "/api/materias/{materia_uid}/busca/sincronizar"),
    ("post", "/api/materias/{materia_uid}/topicos"), ("post", "/api/materias/{materia_uid}/sessoes"),
    ("post", "/api/materias/{materia_uid}/formulas"),
]
_SEM_TIPO = ({}, {"type": "object"}, {"additionalProperties": True, "type": "object"}, {"title": "Response"})


def _esquema(openapi, metodo, rota):
    respostas = openapi["paths"][rota][metodo]["responses"]
    codigo = "201" if "201" in respostas else "200"
    return respostas[codigo]["content"]["application/json"]["schema"]


@pytest.mark.parametrize("metodo,rota", ROTAS_DO_FRONTEND)
def test_resposta_tem_esquema(openapi, metodo, rota):
    esquema = _esquema(openapi, metodo, rota)
    sem_titulo = {k: v for k, v in esquema.items() if k != "title"}
    assert sem_titulo not in _SEM_TIPO
    if esquema.get("type") == "array":
        assert esquema["items"] not in _SEM_TIPO


def test_painel_documenta_os_blocos(openapi):
    comp = openapi["components"]["schemas"]["Painel"]["properties"]
    assert {"topicos", "listas", "marcacoes", "eventos", "vinculos", "importacoes_pendentes", "placar"} <= comp.keys()
