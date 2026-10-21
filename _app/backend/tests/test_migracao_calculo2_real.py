"""Migra a pasta real de Cálculo 2 para uma pasta temporária. O esperado é calculado dos próprios arquivos legados."""

import json
from contextlib import closing
from pathlib import Path

import pytest

from estudos.db.conexao import conectar
from estudos.migracao.__main__ import main
from estudos.repos import documentos, listas, unidades

REAL = Path(__file__).resolve().parents[3] / "Calculo 2"
pytestmark = pytest.mark.skipif(
    not (REAL / "_app/dados/curso.json").is_file(), reason="pasta real de Cálculo 2 ausente"
)


@pytest.fixture(scope="module")
def migrada(tmp_path_factory):
    destino = tmp_path_factory.mktemp("ws") / "Calculo 2"
    codigo = main([str(REAL), "--destino", str(destino)])
    con = conectar(destino / "materia.db")
    yield codigo, destino, con
    con.close()


def _legado(nome):
    caminho = REAL / ("status.json" if nome == "status" else f"_app/dados/{nome}.json")
    return json.loads(caminho.read_text(encoding="utf-8"))


def test_codigo_de_saida_zero(migrada):
    codigo, destino, _ = migrada
    assert codigo == 0
    assert "contagens batem" in (destino / ".migracao/relatorio.md").read_text(encoding="utf-8")


def test_unidades_e_nota(migrada):
    _, _, con = migrada
    curso = _legado("curso")
    assert [u.numero for u in unidades.listar(con)] == sorted(int(n) for n in curso["unidades"])
    notas = dict(con.execute("SELECT u.numero, n.nota FROM nota_avaliacao n JOIN unidade u ON u.id = n.unidade_id"))
    assert notas.get(1) == 8.0


def test_todas_as_marcacoes(migrada):
    _, _, con = migrada
    assert con.execute("SELECT count(*) FROM marcacao").fetchone()[0] == len(_legado("status")["marcacoes"])


def test_resolucoes_com_questao(migrada):
    _, _, con = migrada
    resolucoes = documentos.listar(con, "resolucao")
    assert len(resolucoes) == len(list((REAL / "resolucoes").glob("*.md")))
    assert all(r.questao_id is not None for r in resolucoes)


def test_resumos_com_unidade(migrada):
    _, _, con = migrada
    resumos = documentos.listar(con, "resumo")
    assert len(resumos) == len(list((REAL / "resumos").glob("*.md")))
    assert all(r.unidade_id is not None for r in resumos)


def test_estado_das_listas_igual_ao_legado(migrada):
    _, _, con = migrada
    legado = {s["sec"]: not s.get("locked", False) for s in _legado("exercicios")}
    novo = {l.codigo: l.aberta for u in unidades.listar(con) for l in listas.listar(con, u.id)}
    assert novo == legado


def test_cli_recusa_com_historico(migrada):
    _, destino, _ = migrada
    with closing(conectar(destino / "materia.db")) as con:
        con.execute("INSERT INTO historico_grupo (momento, descricao) VALUES ('x', 'ação')")
    try:
        assert main([str(REAL), "--destino", str(destino)]) == 2
    finally:
        with closing(conectar(destino / "materia.db")) as con:
            con.execute("DELETE FROM historico_grupo")
