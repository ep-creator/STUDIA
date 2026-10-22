from contextlib import closing
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.db.conexao import conectar
from estudos.historico import operacao
from estudos.main import create_app
from estudos.repos import eventos, fontes, importacoes, listas, livros, topicos, unidades
from estudos.workspace import abrir_materia


@pytest.fixture
def cliente(tmp_path):
    (tmp_path / "_app").mkdir()
    return TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")


@pytest.fixture
def dados(cliente, tmp_path):
    """Matéria com 2 unidades, prova futura na 2ª, um tópico e uma lista ligados à seção 15.4 e uma importação pendente."""
    uid = cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]
    ref = abrir_materia(tmp_path, uid)
    pdf = ref.pasta / "fontes" / "livros" / "stewart.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(b"%PDF-1.4 livro")
    with closing(conectar(ref.db)) as con:
        with operacao(con, "dados", ref.pasta) as op:
            u1 = unidades.criar(op, 1, "Primeira")
            u2 = unidades.criar(op, 2, "Segunda")
            eventos.criar(op, "aula", "2099-03-01", unidade_id=u1)
            eventos.criar(op, "aula", "2099-05-01", unidade_id=u2)
            eventos.criar(op, "prova", "2099-05-10", unidade_id=u2, hora_inicio="14:30", hora_fim="17:00")
            eventos.criar(op, "exame_final", "2099-06-20")
            fonte_id = fontes.registrar(op, "livro", "fontes/livros/stewart.pdf", "Stewart")
            livros.criar(op, fonte_id, "principal", titulo_obra="Stewart")
            secao = livros.criar_secao(op, fonte_id, "15.4", "Integrais Duplas em Coordenadas Polares", 431, 440, nivel=2)
            topico_id = topicos.criar(op, u2, "Integrais duplas em coordenadas polares")
            livros.vincular_topico(op, topico_id, secao, confianca=1.0, confirmado=True)
            lista_id = listas.criar(op, "15.4", "Seção 15.4", u2)
            listas.vincular_secao(op, lista_id, secao)
            listas.vincular_topico(op, lista_id, topico_id)
        importacoes.criar(con, fonte_id, "livro", {"secoes": []})
    return SimpleNamespace(uid=uid, topico_id=topico_id, lista_id=lista_id)


def test_lista_de_materias_traz_resumo(cliente, dados):
    [m] = cliente.get("/api/materias").json()
    assert m["unidades"] == 2 and m["importacoes_pendentes"] == 1
    assert m["proxima_prova"] == {"data": "2099-05-10", "hora_inicio": "14:30", "unidade": 2}


def test_materia_vazia_no_resumo_e_no_painel(cliente):
    uid = cliente.post("/api/materias", json={"nome": "Nova"}).json()["uid"]
    [m] = cliente.get("/api/materias").json()
    assert m["proxima_prova"] is None and m["unidades"] == 0 and m["importacoes_pendentes"] == 0
    p = cliente.get(f"/api/materias/{uid}/painel").json()
    assert p["unidade"] is None and p["eventos"] == [] and p["vinculos"] == {"topicos": {}, "listas": {}}
    assert p["importacoes_pendentes"] == 0


def test_painel_traz_eventos_da_unidade_e_gerais(cliente, dados):
    p = cliente.get(f"/api/materias/{dados.uid}/painel?unidade=2").json()
    assert [e["tipo"] for e in p["eventos"]] == ["aula", "prova", "exame_final"]
    assert p["importacoes_pendentes"] == 1


def test_painel_traz_vinculos_de_topico_e_lista(cliente, dados):
    v = cliente.get(f"/api/materias/{dados.uid}/painel?unidade=2").json()["vinculos"]
    [s] = v["topicos"][str(dados.topico_id)]
    assert (s["codigo"], s["pagina_pdf_ini"], s["caminho"]) == ("15.4", 431, "fontes/livros/stewart.pdf")
    lista = v["listas"][str(dados.lista_id)]
    assert lista["secao"]["codigo"] == "15.4" and lista["topicos"] == [dados.topico_id]
