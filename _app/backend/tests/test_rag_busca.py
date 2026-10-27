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
    assert "resposta da integral tripla" not in texto   # o gabarito não entra no texto da seção


def test_filtro_por_parte(cenario):
    teoria = buscar(cenario["indice"], "integrais triplas", partes=["teoria"])
    assert teoria and all(r.parte == "teoria" for r in teoria)
    todas = buscar(cenario["indice"], "integrais triplas")
    assert {"teoria", "exercicio"} <= {r.parte for r in todas}
    [ex] = buscar(cenario["indice"], "integrais triplas", partes=["exercicio"])
    assert ex.numero == 1 and ex.secao_id == cenario["s12"]


def test_resposta_e_exercicio_de(cenario):
    from estudos.rag.busca import exercicio_de, resposta_de
    ex = exercicio_de(cenario["indice"], cenario["s12"], 2)   # o 2 é curto e foi junto com o 1
    assert ex is not None and ex.parte == "exercicio" and "Mude a ordem" in ex.trecho
    assert exercicio_de(cenario["indice"], cenario["s12"], 9) is None
    assert exercicio_de(cenario["indice"], cenario["s11"], 1) is None
    r = resposta_de(cenario["indice"], cenario["s12"], 1)
    assert r is not None and "resposta da integral tripla" in r.trecho
    assert resposta_de(cenario["indice"], cenario["s12"], 3) is None


def test_cao_e_coes_casam():
    assert montar_consulta("funções") == '"func"*' == montar_consulta("função")
    assert montar_consulta("equações integração") == '"equac"* OR "integr"*'
    assert montar_consulta("derivação") == montar_consulta("derivadas") == '"deriv"*'


# ---- modos "vetor" e "hibrida" (peça B da Fase 6) ------------------------------------------------------------------

from estudos.ia.embeddings import EmbeddingsFalso  # noqa: E402
from estudos.rag.busca import buscar_modo, fundir_rrf  # noqa: E402


@pytest.fixture
def com_vetores(con, materia, cenario):
    e = EmbeddingsFalso()
    sincronizar(con, materia.pasta, embeddings=e)
    return cenario, e


def test_rrf_soma_as_posicoes_dos_dois_rankings():
    # 2 aparece bem nos dois: sobe; 1 só no primeiro; 3 só no segundo
    fundido = fundir_rrf([[1, 2], [3, 2]], k=60)
    assert [i for i, _ in fundido] == [2, 1, 3]
    assert fundido[0][1] == pytest.approx(1 / 62 + 1 / 62)


def test_vetor_e_hibrida_respeitam_os_filtros(com_vetores):
    cenario, e = com_vetores
    indice = cenario["indice"]
    for modo in ("vetor", "hibrida"):
        efetivo, r = buscar_modo(indice, "polares", tipos=["resumo"], modo=modo, embeddings=e)
        assert efetivo == modo and r and {x.tipo for x in r} == {"resumo"}
        _, r = buscar_modo(indice, "integrais", secao_id=cenario["s12"], modo=modo, embeddings=e)
        assert r and {x.secao_id for x in r} == {cenario["s12"]}
        _, r = buscar_modo(indice, "integrais triplas", unidade=1, modo=modo, embeddings=e)
        assert not any(x.secao_id == cenario["s12"] for x in r)


def test_hibrida_marca_de_onde_veio_cada_resultado(com_vetores):
    cenario, e = com_vetores
    _, r = buscar_modo(cenario["indice"], "coordenadas polares", modo="hibrida", embeddings=e, limite=20)
    assert {x.por for x in r} <= {"texto", "sentido", "ambos"} and any(x.por == "ambos" for x in r)


def test_sem_vetores_cai_para_texto(cenario):
    efetivo, r = buscar_modo(cenario["indice"], "polares", modo="hibrida", embeddings=None)
    assert efetivo == "texto" and r == buscar(cenario["indice"], "polares")


@pytest.mark.parametrize("modo", ["texto", "vetor", "hibrida"])
@pytest.mark.parametrize("consulta", ["", "  ", "de a o", "!"])
def test_consulta_vazia_ou_so_palavras_vazias_nao_traz_nada(com_vetores, modo, consulta):
    cenario, e = com_vetores
    assert buscar_modo(cenario["indice"], consulta, modo=modo, embeddings=e)[1] == []


def test_consulta_ignora_uso_privado(cenario):
    # a busca por palavras só considera letras e números: caractere de uso privado na consulta não muda nada
    from estudos.rag.busca import buscar_modo
    _, com = buscar_modo(cenario["indice"], "polares" + chr(0xE001))
    _, sem = buscar_modo(cenario["indice"], "polares")
    assert com and [r.trecho_id for r in com] == [r.trecho_id for r in sem]
