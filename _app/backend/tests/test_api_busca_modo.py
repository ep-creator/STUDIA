from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.main import create_app


def test_api_por_padrao_usa_texto_e_informa_o_modo(tmp_path):
    (tmp_path / "_app").mkdir()
    cliente = TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")
    uid = cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]
    cliente.put(f"/api/materias/{uid}/documentos", json={"tipo": "resumo", "nome_arquivo": "p.md", "titulo": "Polares",
                                                          "corpo": "# Polares\n\nCoordenadas polares e cardioides."})
    padrao = cliente.get(f"/api/materias/{uid}/busca", params={"q": "polares"}).json()
    assert padrao["modo"] == "texto" and padrao["resultados"] and padrao["resultados"][0]["por"] == "texto"
    # pedir híbrida com os embeddings desligados no config: cai para texto e diz isso
    hibrida = cliente.get(f"/api/materias/{uid}/busca", params={"q": "polares", "modo": "hibrida"}).json()
    assert hibrida["modo"] == "texto" and hibrida["resultados"] == padrao["resultados"]
