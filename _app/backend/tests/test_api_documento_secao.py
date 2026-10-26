import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.db.conexao import conectar
from estudos.historico import operacao
from estudos.main import create_app
from estudos.repos import fontes, livros
from estudos.workspace import abrir_materia
from pdfs_sinteticos import criar_pdf


@pytest.fixture
def cenario(tmp_path):
    (tmp_path / "_app").mkdir()
    cliente = TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")
    uid = cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]
    pasta = abrir_materia(tmp_path, uid).pasta
    criar_pdf(pasta / "fontes/livros/stewart.pdf", ["capa", "texto"])
    con = conectar(pasta / "materia.db")
    with operacao(con, "base", pasta) as op:
        stewart = fontes.registrar(op, "livro", "fontes/livros/stewart.pdf")
        livros.criar(op, stewart, "principal")
        s147 = livros.criar_secao(op, stewart, "14.7", "Valores Máximo e Mínimo", 1, 1)
        s103 = livros.criar_secao(op, stewart, "10.3", "Coordenadas Polares", 2, 2)
    con.close()
    return cliente, f"/api/materias/{uid}/documentos", {"14.7": s147, "10.3": s103}


def _criar(cliente, base, titulo, **extra):
    return cliente.put(base, json={"tipo": "resumo", "nome_arquivo": f"{abs(hash(titulo))}.md", "titulo": titulo, "corpo": "x", **extra}).json()["id"]


def test_criar_documento_confiante_ja_sai_ligado(cenario):
    cliente, base, s = cenario
    did = _criar(cliente, base, "14.7 Valores máximo e mínimo")
    doc = cliente.get(f"{base}/{did}").json()
    assert doc["secao_id"] == s["14.7"] and doc["secao_codigo"] == "14.7"


def test_sugestao_nao_grava(cenario):
    cliente, base, s = cenario
    did = _criar(cliente, base, "Coordenadas polares")
    sugestao = cliente.get(f"{base}/{did}/sugestao-secao").json()
    assert sugestao["secao_id"] == s["10.3"] and sugestao["por"] in ("palavras", "codigo")
    assert cliente.get(f"{base}/{did}/sugestao-secao").status_code == 200


def test_sem_sugestao_devolve_null(cenario):
    cliente, base, _ = cenario
    did = _criar(cliente, base, "Séries de Fourier")
    assert cliente.get(f"{base}/{did}/sugestao-secao").json() is None


def test_escolher_e_remover_secao_a_mao(cenario):
    cliente, base, s = cenario
    did = _criar(cliente, base, "Anotações soltas")
    assert cliente.put(f"{base}/{did}/secao", json={"secao_id": s["10.3"]}).json() == {"ok": True}
    assert cliente.get(f"{base}/{did}").json()["secao_id"] == s["10.3"]
    cliente.put(f"{base}/{did}/secao", json={"secao_id": None})
    doc = cliente.get(f"{base}/{did}").json()
    assert doc["secao_id"] is None and doc["secao_decidida"] is True


def test_ligar_secoes_liga_os_confiantes_que_faltam(cenario):
    cliente, base, s = cenario
    did = _criar(cliente, base, "Sem título útil")
    # simula um documento antigo, salvo antes da ligação existir, com título confiante
    cliente.put(base, json={"tipo": "resumo", "nome_arquivo": "velho.md", "titulo": "14.7 Valores máximo e mínimo",
                            "corpo": "x", "secao_id": None})
    resposta = cliente.post(f"{base}/ligar-secoes").json()
    assert resposta["ligados"] >= 0
    assert cliente.get(f"{base}/{did}").json()["secao_id"] is None
    assert any(d["secao_codigo"] == "14.7" for d in cliente.get(base).json())
