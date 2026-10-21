from estudos.config import carregar_settings


def test_defaults_sem_arquivo(tmp_path):
    s = carregar_settings(tmp_path / "_app")
    assert s.porta == 8790 and s.host == "127.0.0.1"
    assert s.workspace == tmp_path


def test_config_toml_sobrescreve(tmp_path):
    app = tmp_path / "_app"
    app.mkdir()
    (app / "config.toml").write_text(
        "[servidor]\nporta = 9001\n[historico]\nmax_grupos = 10\n", encoding="utf-8"
    )
    s = carregar_settings(app)
    assert s.porta == 9001 and s.historico_max_grupos == 10 and s.limiar_vinculo == 0.35


def test_workspace_explicito(tmp_path):
    assert carregar_settings(tmp_path / "_app", tmp_path / "ws").workspace == tmp_path / "ws"
