import subprocess
from pathlib import Path

import pytest

from estudos.agente.custo import custo_brl
from estudos.agente.segredos import gravar_chave, ler_chave
from estudos.config import carregar_settings

RAIZ_REPO = Path(__file__).resolve().parents[3]


def test_config_le_a_secao_agente(tmp_path):
    app = tmp_path / "_app"
    app.mkdir()
    (app / "config.toml").write_text(
        '[agente]\nmodelo = "gemini-x"\nteto_mensal_brl = 35\ncotacao_dolar = 5.2\nmax_rodadas = 4\ntempo_limite_s = 30\n'
        '[agente.precos]\n"gemini-x" = { entrada = 1.0, saida = 4.0 }\n', encoding="utf-8")
    s = carregar_settings(app)
    assert (s.agente_modelo, s.teto_mensal_brl, s.cotacao_dolar, s.max_rodadas, s.tempo_limite_s) == ("gemini-x", 35, 5.2, 4, 30)
    assert s.agente_precos == {"gemini-x": {"entrada": 1.0, "saida": 4.0}}


def test_padroes_do_agente(tmp_path):
    s = carregar_settings(tmp_path / "_app")
    assert (s.agente_modelo, s.teto_mensal_brl, s.max_rodadas, s.tempo_limite_s) == ("gemini-3.8-flash", 20.0, 6, 60)
    assert "gemini-3.8-flash" in s.agente_precos


def test_chave_gravada_fora_do_git(tmp_path):
    assert ler_chave(tmp_path) is None
    gravar_chave(tmp_path, "AIza-teste")
    assert ler_chave(tmp_path) == "AIza-teste"
    ignorado = subprocess.run(["git", "check-ignore", "-q", "_app/.segredos.toml"], cwd=RAIZ_REPO)
    assert ignorado.returncode == 0


def test_custo_em_reais(tmp_path):
    s = carregar_settings(tmp_path / "_app")
    s = s.__class__(**{**s.__dict__, "agente_precos": {"m": {"entrada": 0.30, "saida": 2.50}}, "cotacao_dolar": 5.6,
                       "agente_modelo": "m"})
    assert custo_brl(s, "m", 1_000_000, 1_000_000) == pytest.approx(round(2.8 * 5.6, 4))


def test_modelo_sem_preco_usa_o_padrao(tmp_path):
    s = carregar_settings(tmp_path / "_app")
    assert custo_brl(s, "modelo-desconhecido", 1000, 1000) == custo_brl(s, s.agente_modelo, 1000, 1000) > 0
