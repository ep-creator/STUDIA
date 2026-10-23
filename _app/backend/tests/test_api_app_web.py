from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.main import create_app


def _cliente(raiz, com_dist: bool) -> TestClient:
    app_dir = raiz / "_app"
    app_dir.mkdir()
    if com_dist:
        dist = app_dir / "frontend" / "dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text('<html><body><div id="app"></div></body></html>', encoding="utf-8")
        (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    return TestClient(create_app(carregar_settings(app_dir, raiz)), base_url="http://127.0.0.1:8790")


def test_app_servido_e_api_intacta(tmp_path):
    c = _cliente(tmp_path, com_dist=True)
    assert '<div id="app">' in c.get("/").text
    assert '<div id="app">' in c.get("/qualquer/rota").text
    assert c.get("/assets/app.js").text == "console.log(1)"
    assert c.get("/api/materias").json() == []
    assert c.get("/api/nao-existe").status_code == 404
    assert c.get("/arquivos/sem-materia/x.pdf").status_code == 404


def test_caminho_fora_do_dist_nao_vaza(tmp_path):
    c = _cliente(tmp_path, com_dist=True)
    r = c.get("/..%2F..%2Fconfig.toml")
    assert r.status_code in (200, 404, 422) and "[" not in r.text.split("<")[0]


def test_sem_build_mostra_instrucao(tmp_path):
    r = _cliente(tmp_path, com_dist=False).get("/")
    assert r.status_code == 200 and "Frontend ainda não compilado" in r.text


def test_api_sem_barra_nao_vira_a_pagina_do_app(tmp_path):
    c = _cliente(tmp_path, com_dist=True)
    r = c.get("/api")
    assert r.status_code == 404 and '<div id="app">' not in r.text
