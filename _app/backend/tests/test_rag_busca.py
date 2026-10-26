import pytest

from estudos.historico import operacao
from estudos.rag.busca import buscar, montar_consulta, secao_completa
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice
from estudos.repos import documentos, fontes, listas, livros, topicos, unidades
from pdfs_sinteticos import criar_pdf
from test_rag_indexador import PAGINAS_LIVRO


@pytest.fixture
def cenario(cenario_busca):
    return cenario_busca


def test_montar_consulta():
    assert montar_consulta("Integrais triplas cilíndricas") == '"integr"* OR "tripl"* OR "cilindric"*'
    assert montar_consulta("área de polar") == '"area" OR "polar"*'
    assert montar_consulta("a r de") is None
    for perigosa in ('"', "a*b", "(x", "AND OR NEAR", "!!!", ""):
        consulta = montar_consulta(perigosa)
        assert consulta is None or all(op not in consulta.split() for op in ("AND", "NEAR", "NOT"))


def test_acha_a_secao_certa(cenario):
    r = buscar(cenario["indice"], "integrais triplas cilíndricas")
    assert r[0].secao_id == cenario["s12"] and r[0].secao_codigo == "1.2" and r[0].tipo == "livro"
    assert "[" in r[0].trecho


def test_singular_casa_plural(cenario):
    assert any(x.secao_id == cenario["s12"] for x in buscar(cenario["indice"], "integral tripla"))


def test_filtros_de_tipo_e_secao(cenario):
    assert {x.tipo for x in buscar(cenario["indice"], "polares", tipos=["resumo"])} == {"resumo"}
    assert {x.secao_id for x in buscar(cenario["indice"], "polares", secao_id=cenario["s11"])} == {cenario["s11"]}
    assert all(x.tipo == "gabarito" for x in buscar(cenario["indice"], "respostas", tipos=["gabarito"]))


def test_filtro_de_unidade_segue_o_vinculo_atual(con, materia, cenario):
    em_u3 = {x.origem for x in buscar(cenario["indice"], "integrais", unidade=3)}
    assert any(o.startswith("fonte:") for o in em_u3)
    assert not any(x.secao_id == cenario["s12"] for x in buscar(cenario["indice"], "integrais triplas", unidade=1))
    with operacao(con, "mudar vínculo") as op:
        topicos.atualizar(op, cenario["t3"], unidade_id=cenario["u1"])
    assert any(x.secao_id == cenario["s12"] for x in buscar(cenario["indice"], "integrais triplas", unidade=1))


def test_unidade_inclui_documentos_globais_e_da_unidade(cenario):
    titulos = {x.titulo for x in buscar(cenario["indice"], "polares integrais", unidade=1, limite=20)}
    assert "Polares" in titulos and "Geral" in titulos


@pytest.mark.parametrize("consulta", ['"', "a*b", "(x", "AND OR NEAR", "!!!", "integral)", "NOT polares"])
def test_consultas_perigosas_nao_quebram(cenario, consulta):
    buscar(cenario["indice"], consulta)


def test_sem_consulta_com_filtro(cenario):
    r = buscar(cenario["indice"], "", secao_id=cenario["s12"])
    assert r and all(x.secao_id == cenario["s12"] for x in r)


def test_secao_completa(cenario):
    texto = secao_completa(cenario["indice"], cenario["s12"])
    assert texto.index("integrais triplas em coordenadas") < texto.index("exercícios de integrais triplas")
    assert "Coordenadas polares" not in texto


def test_cao_e_coes_casam():
    assert montar_consulta("funções") == '"func"*' == montar_consulta("função")
    assert montar_consulta("equações integração") == '"equac"* OR "integr"*'
    assert montar_consulta("derivação") == montar_consulta("derivadas") == '"deriv"*'
