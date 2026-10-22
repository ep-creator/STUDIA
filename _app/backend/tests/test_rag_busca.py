import pytest

from estudos.historico import operacao
from estudos.rag.busca import buscar, montar_consulta, secao_completa
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice
from estudos.repos import documentos, fontes, listas, livros, topicos, unidades
from pdfs_sinteticos import criar_pdf
from test_rag_indexador import PAGINAS_LIVRO


@pytest.fixture
def cenario(con, materia):
    criar_pdf(materia.pasta / "fontes/livros/livro.pdf", PAGINAS_LIVRO)
    criar_pdf(materia.pasta / "fontes/listas/lista.pdf", ["Lista 5\n1. Calcule a integral dupla em polares.", "2. Área da cardioide."])
    with operacao(con, "base", materia.pasta) as op:
        u1, u3 = unidades.criar(op, 1), unidades.criar(op, 3)
        livro = fontes.registrar(op, "livro", "fontes/livros/livro.pdf")
        livros.criar(op, livro, "principal", gabarito_pdf_ini=7, gabarito_pdf_fim=8)
        s11 = livros.criar_secao(op, livro, "1.1", "Coordenadas polares", 2, 3)
        s12 = livros.criar_secao(op, livro, "1.2", "Integrais triplas", 4, 6)
        t3 = topicos.criar(op, u3, "Integrais triplas em coordenadas cilíndricas")
        livros.vincular_topico(op, t3, s12, confianca=1.0, confirmado=True)
        fl = fontes.registrar(op, "lista", "fontes/listas/lista.pdf")
        listas.criar(op, "L5", "Lista 5", u3, fonte_id=fl)
        documentos.salvar(op, "resumo", "polares", "Polares", "# Polares\n\nCoordenadas polares e cardioides.", unidade_id=u1)
        documentos.salvar(op, "anotacao", "geral", "Geral", "Integrais em geral.")
    sincronizar(con, materia.pasta)
    indice = abrir_indice(materia.pasta)
    yield {"indice": indice, "s11": s11, "s12": s12, "t3": t3, "u1": u1}
    indice.close()


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
    assert montar_consulta("equações integração") == '"equac"* OR "integrac"*'
