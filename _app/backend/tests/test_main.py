from estudos.__main__ import main


def test_argumentos(monkeypatch, tmp_path):
    chamado = {}
    monkeypatch.setattr("uvicorn.run", lambda app, host, port: chamado.update(host=host, port=port))
    main(["--porta", "8801", "--sem-navegador"], app_dir=tmp_path / "_app")
    assert chamado == {"host": "127.0.0.1", "port": 8801}


def test_porta_padrao_vem_da_config(monkeypatch, tmp_path):
    app_dir = tmp_path / "_app"
    app_dir.mkdir()
    (app_dir / "config.toml").write_text("[servidor]\nporta = 8999\n", encoding="utf-8")
    chamado = {}
    monkeypatch.setattr("uvicorn.run", lambda app, host, port: chamado.update(port=port))
    main(["--sem-navegador"], app_dir=app_dir)
    assert chamado == {"port": 8999}
