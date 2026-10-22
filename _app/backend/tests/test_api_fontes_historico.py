from contextlib import closing
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.db.conexao import conectar
from estudos.historico import operacao
from estudos.main import create_app
from estudos.repos import fontes, livros
from estudos.workspace import abrir_materia


@pytest.fixture
def cliente(tmp_path):
    (tmp_path / "_app").mkdir()
    return TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")


@pytest.fixture
def uid(cliente):
    return cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]


@pytest.fixture
def livro(cliente, uid, tmp_path):
    ref = abrir_materia(tmp_path, uid)
    for rel, conteudo in (("fontes/livros/stewart.pdf", b"%PDF livro"), ("fontes/listas/l1.pdf", b"%PDF lista")):
        (ref.pasta / rel).parent.mkdir(parents=True, exist_ok=True)
        (ref.pasta / rel).write_bytes(conteudo)
    with closing(conectar(ref.db)) as con, operacao(con, "dados", ref.pasta) as op:
        fonte_livro = fontes.registrar(op, "livro", "fontes/livros/stewart.pdf", "Stewart", 600)
        livros.criar(op, fonte_livro, "principal")
        livros.criar_secao(op, fonte_livro, "14.1", "Funções de Várias Variáveis", 380, 395, nivel=2)
        livros.criar_secao(op, fonte_livro, "14.2", "Limites e Continuidade", 396, 405, nivel=2)
        fonte_lista = fontes.registrar(op, "lista", "fontes/listas/l1.pdf", "Lista 1")
    return SimpleNamespace(uid=uid, fonte_lista_id=fonte_lista)


def test_fontes_e_sumario(cliente, livro):
    fontes_ = cliente.get(f"/api/materias/{livro.uid}/fontes?tipo=livro").json()
    assert [(f["caminho"], f["paginas"]) for f in fontes_] == [("fontes/livros/stewart.pdf", 600)]
    assert len(cliente.get(f"/api/materias/{livro.uid}/fontes").json()) == 2
    secoes = cliente.get(f"/api/materias/{livro.uid}/fontes/{fontes_[0]['id']}/secoes").json()
    assert [s["codigo"] for s in secoes] == ["14.1", "14.2"]


def test_sumario_de_fonte_que_nao_e_livro_da_404(cliente, livro):
    assert cliente.get(f"/api/materias/{livro.uid}/fontes/{livro.fonte_lista_id}/secoes").status_code == 404
    assert cliente.get(f"/api/materias/{livro.uid}/fontes/999/secoes").status_code == 404


def test_diferenca_de_documento_editado_duas_vezes(cliente, uid):
    doc = {"tipo": "resumo", "nome_arquivo": "a.md", "titulo": "A", "corpo": "v1"}
    for corpo in ("v1", "v2", "v3"):
        assert cliente.put(f"/api/materias/{uid}/documentos", json={**doc, "corpo": corpo}).status_code == 200
    grupos = cliente.get(f"/api/materias/{uid}/historico").json()
    meio = cliente.get(f"/api/materias/{uid}/historico/{grupos[1]['id']}").json()
    assert meio["grupo"]["id"] == grupos[1]["id"]
    [arq] = meio["arquivos"]
    assert "v1" in arq["antes"] and "v2" in arq["depois"] and arq["caminho"].endswith("a.md")
    assert any(m["tabela"] == "documento" for m in meio["mudancas"])
    ultimo = cliente.get(f"/api/materias/{uid}/historico/{grupos[0]['id']}").json()
    assert "v3" in ultimo["arquivos"][0]["depois"]
    criacao = cliente.get(f"/api/materias/{uid}/historico/{grupos[2]['id']}").json()
    assert criacao["arquivos"][0]["antes"] is None


def test_grupo_inexistente_da_404(cliente, uid):
    assert cliente.get(f"/api/materias/{uid}/historico/999").status_code == 404
