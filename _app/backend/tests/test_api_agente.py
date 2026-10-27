import json
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from estudos.agente.modelo import Chamada, ModeloFalso, Texto, Uso
from estudos.config import carregar_settings
from estudos.db.conexao import conectar
from estudos.historico import operacao
from estudos.main import create_app
from estudos.modelos import QuestaoEntrada
from estudos.repos import listas, unidades
from estudos.workspace import abrir_materia


@pytest.fixture
def api(tmp_path):
    (tmp_path / "_app").mkdir()
    settings = carregar_settings(tmp_path / "_app", tmp_path)
    app = create_app(settings)
    cliente = TestClient(app, base_url="http://127.0.0.1:8790")
    uid = cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]
    materia = abrir_materia(tmp_path, uid)
    with closing(conectar(materia.db)) as con, operacao(con, "base", materia.pasta) as op:
        u = unidades.criar(op, 1)
        lid = listas.criar(op, "L1", "Lista 1", u)
        listas.sincronizar_questoes(op, lid, [QuestaoEntrada("3", enunciado_md="Calcule a integral dupla.")])
    with closing(conectar(materia.db)) as con:
        [q] = listas.listar_questoes(con, lid)
    return {"cliente": cliente, "app": app, "base": f"/api/materias/{uid}/agente", "uid": uid, "questao": q.id,
            "settings": settings}


def _com_modelo(api, rodadas):
    modelo = ModeloFalso(rodadas, nome="gemini-3.8-flash")
    api["app"].state.fabrica_modelo = lambda settings: modelo
    return modelo


def _linhas(resposta):
    return [json.loads(l) for l in resposta.text.splitlines() if l.strip()]


def test_mensagem_em_streaming(api):
    _com_modelo(api, [[Texto("Use "), Texto("polares."), Uso(100, 20)]])
    r = api["cliente"].post(f"{api['base']}/mensagem", json={"alvo": f"questao:{api['questao']}", "papel": "tutor",
                                                            "atalho": "N2"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/x-ndjson")
    eventos = _linhas(r)
    assert [e["tipo"] for e in eventos] == ["texto", "texto", "fim"] and eventos[0]["dados"]["texto"] == "Use "
    conversa = api["cliente"].get(f"{api['base']}/conversa", params={"alvo": f"questao:{api['questao']}", "papel": "tutor"}).json()
    assert [m["autor"] for m in conversa["mensagens"]] == ["voce", "agente"] and "N2" in conversa["mensagens"][0]["texto"]


def test_gravacao_vira_evento_gravado(api):
    _com_modelo(api, [[Chamada("salvar_resolucao", {"texto": "**Resposta.** 42"})], [Texto("Gravei.")]])
    eventos = _linhas(api["cliente"].post(f"{api['base']}/mensagem", json={
        "alvo": f"questao:{api['questao']}", "papel": "tutor", "atalho": "N4"}))
    [gravado] = [e for e in eventos if e["tipo"] == "gravado"]
    assert gravado["dados"]["titulo"] == "Resolução L1-3" and gravado["dados"]["grupo_id"]


def test_sem_chave_avisa(api):
    api["app"].state.fabrica_modelo = None   # usa a fábrica de verdade: sem _app/.segredos.toml
    eventos = _linhas(api["cliente"].post(f"{api['base']}/mensagem", json={"alvo": "geral", "papel": "estrategista",
                                                                          "atalho": "plano"}))
    assert eventos == [{"tipo": "erro", "dados": {"motivo": "sem_chave", "detalhe": ""}}]


def test_pedido_sem_texto_nem_atalho(api):
    r = api["cliente"].post(f"{api['base']}/mensagem", json={"alvo": "geral", "papel": "estrategista"})
    assert r.status_code == 422


def test_estado_nao_expoe_a_chave(api):
    cliente = api["cliente"]
    assert cliente.get("/api/agente/estado").json()["chave_configurada"] is False
    assert cliente.put("/api/agente/chave", json={"chave": "AIza-SEGREDO"}).status_code == 200
    estado = cliente.get("/api/agente/estado")
    assert estado.json()["chave_configurada"] is True and "SEGREDO" not in estado.text
    assert estado.json()["teto"] == 20 and estado.json()["total_mes"] == 0


def test_conversa_e_recomecar(api):
    _com_modelo(api, [[Texto("oi")]])
    alvo = {"alvo": f"questao:{api['questao']}", "papel": "tutor"}
    api["cliente"].post(f"{api['base']}/mensagem", json={**alvo, "texto": "olá"})
    nova = api["cliente"].post(f"{api['base']}/conversa/recomecar", json=alvo).json()
    assert nova["mensagens"] == []
    assert api["cliente"].get(f"{api['base']}/conversa", params=alvo).json()["id"] == nova["id"]


def test_pacote_de_contexto(api):
    r = api["cliente"].get(f"{api['base']}/contexto", params={"alvo": f"questao:{api['questao']}", "papel": "tutor",
                                                              "atalho": "N3"})
    texto = r.json()["texto"]
    assert "[Lista L1 #3]" in texto and "Calcule a integral dupla." in texto and "N3" in texto and "tutor" in texto.lower()


def test_pedido_simultaneo_na_mesma_conversa(api):
    from estudos.api import agente as rota
    _com_modelo(api, [[Texto("oi")]])
    chave = (api["uid"], f"questao:{api['questao']}", "tutor")
    rota._ocupadas.add(chave)
    try:
        eventos = _linhas(api["cliente"].post(f"{api['base']}/mensagem", json={
            "alvo": f"questao:{api['questao']}", "papel": "tutor", "texto": "de novo"}))
    finally:
        rota._ocupadas.discard(chave)
    assert eventos[0]["tipo"] == "erro" and "respondendo" in eventos[0]["dados"]["detalhe"]
