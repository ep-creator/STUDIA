from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.db.conexao import conectar
from estudos.historico import operacao
from estudos.importacao import pipeline
from estudos.main import create_app
from estudos.rag.__main__ import main as cli
from estudos.rag.indexador import sincronizar
from estudos.repos import fontes, livros
from estudos.workspace import abrir_materia
from pdfs_sinteticos import criar_pdf


@pytest.fixture
def ambiente(tmp_path):
    (tmp_path / "_app").mkdir()
    settings = carregar_settings(tmp_path / "_app", tmp_path)
    cliente = TestClient(create_app(settings), base_url="http://127.0.0.1:8790")
    uid = cliente.post("/api/materias", json={"nome": "Cálculo 2"}).json()["uid"]
    return cliente, f"/api/materias/{uid}", abrir_materia(tmp_path, uid), settings


def test_busca_pela_api(ambiente):
    cliente, base, _, _ = ambiente
    cliente.put(f"{base}/documentos", json={"tipo": "resumo", "nome_arquivo": "lagrange", "titulo": "Lagrange",
                                            "corpo": "# Lagrange\n\nMultiplicadores de Lagrange com um vínculo."})
    r = cliente.get(f"{base}/busca", params={"q": "multiplicadores"})
    assert r.status_code == 200
    dados = r.json()
    assert dados["resultados"][0]["titulo"] == "Lagrange" and dados["sincronizacao"]["indexadas"] == 1
    assert cliente.get(f"{base}/busca", params={"q": "multiplicadores", "tipo": "lista"}).json()["resultados"] == []


def test_texto_da_secao(ambiente):
    cliente, base, materia, _ = ambiente
    criar_pdf(materia.pasta / "fontes/livros/l.pdf", ["capa do livro", "1.1 Polares\nr e theta no plano", "fim da seção polar"])
    with closing(conectar(materia.db)) as con, operacao(con, "livro", materia.pasta) as op:
        f = fontes.registrar(op, "livro", "fontes/livros/l.pdf")
        livros.criar(op, f, "principal")
        secao = livros.criar_secao(op, f, "1.1", "Polares", 2, 3)
    r = cliente.get(f"{base}/secoes/{secao}/texto").json()
    assert (r["codigo"], r["titulo"]) == ("1.1", "Polares")
    assert "r e theta" in r["texto"] and "fim da seção" in r["texto"] and "capa" not in r["texto"]
    assert cliente.get(f"{base}/secoes/999/texto").status_code == 404


def test_sincronizar_pela_api(ambiente):
    cliente, base, _, _ = ambiente
    r = cliente.post(f"{base}/busca/sincronizar")
    assert r.status_code == 200 and r.json()["indexadas"] == 0


def test_confirmar_importacao_deixa_o_indice_pronto(ambiente, tmp_path):
    _, _, materia, settings = ambiente
    pdf = criar_pdf(tmp_path / "nota.pdf", ["Anotações de aula sobre coordenadas esféricas e cilíndricas."])
    with closing(conectar(materia.db)) as con:
        imp = pipeline.receber_arquivo(con, materia.pasta, pdf, "nota.pdf", settings)
        resumo = pipeline.confirmar(con, materia.pasta, imp.id, settings)
        assert resumo["indexacao"] == "em segundo plano"
        from estudos.rag.indexador import aguardar_sincronizacoes

        assert aguardar_sincronizacoes(60)
        assert sincronizar(con, materia.pasta).indexadas == 0


def test_cli(ambiente, capsys):
    _, _, materia, _ = ambiente
    assert cli([str(materia.pasta)]) == 0
    assert "trechos" in capsys.readouterr().out
    assert cli([str(materia.pasta / "nao-existe")]) == 2


@pytest.fixture
def com_exercicios(ambiente):
    cliente, base, materia, _ = ambiente
    criar_pdf(materia.pasta / "fontes/livros/l.pdf", [
        "capa", "1.1 Polares\nÁrea de regiões em coordenadas polares.",
        "1.1 Exercícios\n1. Calcule a área dentro da cardioide.\n2. Calcule a área da rosácea de quatro pétalas.",
        "Respostas\nEXERCÍCIOS 1.1\n1. 3 sobre 2"])
    with closing(conectar(materia.db)) as con, operacao(con, "livro", materia.pasta) as op:
        f = fontes.registrar(op, "livro", "fontes/livros/l.pdf")
        livros.criar(op, f, "principal", gabarito_pdf_ini=4, gabarito_pdf_fim=4)
        secao = livros.criar_secao(op, f, "1.1", "Polares", 2, 3)
    return cliente, base, secao


def test_busca_devolve_teoria_e_exercicios(com_exercicios):
    cliente, base, _ = com_exercicios
    dados = cliente.get(f"{base}/busca", params={"q": "área cardioide polares"}).json()
    assert dados["resultados"] and all(r["parte"] == "teoria" for r in dados["resultados"])
    [ex] = dados["exercicios"]
    assert ex["exercicio"]["parte"] == "exercicio" and ex["exercicio"]["pagina"] == 3
    assert "3 sobre 2" in ex["resposta"]["trecho"]
    so_listas = cliente.get(f"{base}/busca", params={"q": "área cardioide", "tipo": "lista"}).json()
    assert so_listas["exercicios"] == []


def test_exercicio_do_livro(com_exercicios):
    cliente, base, secao = com_exercicios
    r = cliente.get(f"{base}/secoes/{secao}/exercicios/2")
    assert r.status_code == 200
    dados = r.json()
    assert "rosácea" in dados["exercicio"]["trecho"] and dados["resposta"] is None   # o 2 é curto: veio junto com o 1


def test_exercicio_inexistente_404(com_exercicios):
    cliente, base, secao = com_exercicios
    assert cliente.get(f"{base}/secoes/{secao}/exercicios/9").status_code == 404
    assert cliente.get(f"{base}/secoes/9999/exercicios/1").status_code == 404
