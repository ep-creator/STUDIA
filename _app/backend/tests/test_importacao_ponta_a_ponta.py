"""Objetivo da Fase 3: uma matéria nova montada só com os PDFs, sem cadastro manual e sem IA."""

import shutil

import pytest
from fastapi.testclient import TestClient

from estudos.config import carregar_settings
from estudos.db.conexao import aplicar_migracoes, conectar
from estudos.importacao import pipeline
from estudos.main import create_app
from pdfs_sinteticos import DISCIPLINA, LISTAS, REAL, STEWART

pytestmark = pytest.mark.skipif(
    not (STEWART.is_file() and (DISCIPLINA / "Programa.pdf").is_file()), reason="PDFs reais ausentes"
)
ORDEM = [
    STEWART,
    DISCIPLINA / "Programa.pdf",
    DISCIPLINA / "Calendario.pdf",
    DISCIPLINA / "info_S3.pdf",
    DISCIPLINA / "exercicios_1un.pdf",
    DISCIPLINA / "exercicios_2un.pdf",
    DISCIPLINA / "exercicios_3un.pdf",
    LISTAS / "Lista5_2026-1.pdf",
]


@pytest.fixture(scope="module")
def materia_nova(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("ws")
    (raiz / "_app").mkdir()
    cliente = TestClient(create_app(carregar_settings(raiz / "_app", raiz)), base_url="http://127.0.0.1:8790")
    uid = cliente.post("/api/materias", json={"nome": "Cálculo 2 (importado)"}).json()["uid"]
    base = f"/api/materias/{uid}"
    tipos = []
    for caminho in ORDEM:
        imp = cliente.post(f"{base}/importacoes", files={"arquivo": (caminho.name, caminho.read_bytes(), "application/pdf")})
        assert imp.status_code == 201, imp.text
        tipos.append(imp.json()["tipo"])
        assert cliente.post(f"{base}/importacoes/{imp.json()['id']}/confirmar").status_code == 200
    return cliente, base, tipos


def test_tipos_detectados(materia_nova):
    _, _, tipos = materia_nova
    assert tipos == ["livro", "programa", "calendario", "turma", "lista", "lista", "lista", "lista"]


def test_unidades_e_provas(materia_nova):
    cliente, base, _ = materia_nova
    unidades = cliente.get(f"{base}/painel").json()["unidades"]
    assert [(u["numero"], u["data_prova"]) for u in unidades] == [
        (1, "2026-09-14"), (2, "2026-10-19"), (3, "2026-11-30")]


def test_topicos_ligados_ao_livro(materia_nova):
    cliente, base, _ = materia_nova
    painel = cliente.get(f"{base}/painel?unidade=3").json()
    assert len(painel["topicos"]) >= 10
    uid = base.rsplit("/", 1)[1]
    raiz = next(p for p in (cliente.app.state.settings.workspace).iterdir() if (p / "materia.db").exists())
    with conectar(raiz / "materia.db") as con:
        codigos = [r[0] for r in con.execute(
            "SELECT s.codigo FROM topico t JOIN topico_secao ts ON ts.topico_id = t.id JOIN secao_livro s ON s.id = ts.secao_id "
            "WHERE t.titulo = 'Integrais triplas em coordenadas cilíndricas'")]
    assert "15.8" in codigos and uid


def test_listas_nas_unidades_certas(materia_nova):
    cliente, base, _ = materia_nova
    por_unidade = {
        n: [l["codigo"] for l in cliente.get(f"{base}/painel?unidade={n}").json()["listas"]] for n in (1, 2, 3)
    }
    assert por_unidade[1] == ["14.1", "14.2", "14.3", "14.4", "14.5"]
    assert por_unidade[2][:3] == ["14.6", "14.7", "14.8"]
    assert por_unidade[3] == ["15.4", "15.5", "15.7", "15.8", "15.9", "15.10", "L5"]
    l5 = next(l for l in cliente.get(f"{base}/painel?unidade=3").json()["listas"] if l["codigo"] == "L5")
    assert len(l5["questoes"]) == 15


def test_professor_e_criterios(materia_nova):
    cliente, base, _ = materia_nova
    m = cliente.get(f"{base}/painel").json()["materia"]
    assert m["professor"] == "Henrique Araújo"


@pytest.mark.skipif(not (REAL / "materia.db").is_file(), reason="Cálculo 2 migrado ausente")
def test_reimportar_sobre_calculo2_migrado_nao_perde_marcacoes(tmp_path):
    pasta = tmp_path / "Calculo 2"
    pasta.mkdir()
    shutil.copy2(REAL / "materia.db", pasta / "materia.db")
    settings = carregar_settings(tmp_path / "_app", tmp_path)
    with conectar(pasta / "materia.db") as con:
        aplicar_migracoes(con)  # o app faz isso ao descobrir a matéria; aqui o banco foi copiado à mão
        marcacoes_antes = dict(con.execute("SELECT questao_id, estado FROM marcacao"))
        questoes_antes = {r[0] for r in con.execute("SELECT id FROM questao")}
        imp = pipeline.receber_arquivo(con, pasta, DISCIPLINA / "exercicios_3un.pdf", "exercicios_3un.pdf", settings)
        assert imp.proposta["modo"] == "mesclar"
        assert all(l["existente"] is not None for l in imp.proposta["listas"])
        pipeline.confirmar(con, pasta, imp.id, settings)
        assert dict(con.execute("SELECT questao_id, estado FROM marcacao")) == marcacoes_antes
        assert questoes_antes <= {r[0] for r in con.execute("SELECT id FROM questao")}
