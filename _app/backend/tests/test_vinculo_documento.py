import pytest

from estudos.conteudo import ler_md
from estudos.historico import desfazer_ultimo, operacao
from estudos.importacao.vinculo import secao_do_documento
from estudos.modelos import QuestaoEntrada
from estudos.repos import documentos, fontes, listas, livros, unidades
from pdfs_sinteticos import criar_pdf

LIMIAR = 0.35


@pytest.fixture
def dois_livros(con, materia):
    """Stewart principal e Guidorizzi complementar, os dois com uma seção "14.1" de títulos diferentes."""
    for nome in ("stewart", "guidorizzi"):
        criar_pdf(materia.pasta / f"fontes/livros/{nome}.pdf", ["capa", "texto"])
    with operacao(con, "base", materia.pasta) as op:
        u1 = unidades.criar(op, 1)
        stewart = fontes.registrar(op, "livro", "fontes/livros/stewart.pdf")
        livros.criar(op, stewart, "principal")
        guid = fontes.registrar(op, "livro", "fontes/livros/guidorizzi.pdf")
        livros.criar(op, guid, "complementar")
        s = {
            "10.3": livros.criar_secao(op, stewart, "10.3", "Coordenadas Polares", 1, 1),
            "14.1": livros.criar_secao(op, stewart, "14.1", "Funções de Várias Variáveis", 1, 1),
            "14.7": livros.criar_secao(op, stewart, "14.7", "Valores Máximo e Mínimo", 2, 2),
            "g14.1": livros.criar_secao(op, guid, "14.1", "Derivadas parciais de ordens superiores", 1, 1),
            "g16": livros.criar_secao(op, guid, "16", "Máximos e mínimos e Multiplicadores de Lagrange", 2, 2),
        }
    return {"u1": u1, "secoes": s, "stewart": stewart, "guidorizzi": guid}


def _doc(con, materia, tipo, titulo, **extra):
    with operacao(con, f"doc {titulo}", materia.pasta) as op:
        nome = "".join(c for c in titulo.lower() if c.isalnum()) or "doc"
        return documentos.obter(con, documentos.salvar(op, tipo, nome, titulo, "corpo", **extra))


@pytest.fixture
def resolucao_com_questao(con, materia, dois_livros):
    with operacao(con, "lista", materia.pasta) as op:
        lista = listas.criar(op, "14.7", "Valores Máximo e Mínimo", dois_livros["u1"])
        listas.vincular_secao(op, lista, dois_livros["secoes"]["14.7"])
        listas.sincronizar_questoes(op, lista, [QuestaoEntrada("12")])
    questao = con.execute("SELECT id FROM questao WHERE lista_id = ?", (lista,)).fetchone()["id"]
    return _doc(con, materia, "resolucao", "Resolução sem código", questao_id=questao), dois_livros


def test_resolucao_herda_a_secao_da_lista_da_questao(con, resolucao_com_questao):
    doc, dados = resolucao_com_questao
    s = secao_do_documento(con, doc, LIMIAR)
    assert s.secao_id == dados["secoes"]["14.7"] and s.por == "questao" and s.confianca == 1.0


def test_codigo_prefere_livro_principal(con, materia, dois_livros):
    s = secao_do_documento(con, _doc(con, materia, "resumo", "14.1 Funções de várias variáveis"), LIMIAR)
    assert s.secao_id == dois_livros["secoes"]["14.1"] and s.titulo.startswith("Funções")
    assert s.por == "codigo" and s.confianca >= 0.75


def test_codigo_da_resolucao_no_titulo(con, materia, dois_livros):
    s = secao_do_documento(con, _doc(con, materia, "resolucao", "Resolução 14.7-12"), LIMIAR)
    assert s.secao_id == dois_livros["secoes"]["14.7"] and s.por == "codigo"


def test_codigo_que_bate_so_em_complementar_com_titulo_diferente_nao_e_confiante(con, materia, dois_livros):
    with operacao(con, "sem principal", materia.pasta) as op:
        livros.criar_secao(op, dois_livros["guidorizzi"], "9.9", "Teorema do valor médio", 3, 3)
    s = secao_do_documento(con, _doc(con, materia, "resumo", "9.9 Integrais triplas"), LIMIAR)
    assert s is None or s.confianca < 0.75


def test_sem_codigo_usa_semelhanca_de_titulo(con, materia, dois_livros):
    s = secao_do_documento(con, _doc(con, materia, "resumo", "Coordenadas polares"), LIMIAR)
    assert s.secao_id == dois_livros["secoes"]["10.3"] and s.por == "palavras"


def test_sem_candidato_devolve_none(con, materia, dois_livros):
    assert secao_do_documento(con, _doc(con, materia, "resumo", "Séries de Fourier"), LIMIAR) is None


def test_anotacao_nao_tem_secao(con, materia, dois_livros):
    assert secao_do_documento(con, _doc(con, materia, "anotacao", "14.7 Valores máximo e mínimo"), LIMIAR) is None


def test_sem_livro_principal_so_sugere(con, materia):
    criar_pdf(materia.pasta / "fontes/livros/g.pdf", ["capa"])
    with operacao(con, "base", materia.pasta) as op:
        g = fontes.registrar(op, "livro", "fontes/livros/g.pdf")
        livros.criar(op, g, "complementar")
        livros.criar_secao(op, g, "14.7", "Valores Máximo e Mínimo", 1, 1)
    s = secao_do_documento(con, _doc(con, materia, "resumo", "14.7 Valores máximo e mínimo"), LIMIAR)
    assert s is not None and s.confianca < 0.75


def test_ligar_sem_secao_grava_so_confiantes_e_pode_ser_desfeita(con, materia, dois_livros):
    certo = _doc(con, materia, "resumo", "14.7 Valores máximo e mínimo")
    duvidoso = _doc(con, materia, "resumo", "Mínimos")
    with operacao(con, "Ligar documentos às seções do livro", materia.pasta) as op:
        assert documentos.ligar_sem_secao(op, materia.pasta, LIMIAR, 0.75) == 1
    assert documentos.obter(con, certo.id).secao_id == dois_livros["secoes"]["14.7"]
    assert documentos.obter(con, duvidoso.id).secao_id is None
    assert ler_md(materia.pasta / certo.caminho).meta["secao"] == "14.7"
    desfazer_ultimo(con, materia.pasta)
    assert documentos.obter(con, certo.id).secao_id is None


def test_decisao_manual_nao_e_sobrescrita(con, materia, dois_livros):
    doc = _doc(con, materia, "resumo", "14.7 Valores máximo e mínimo")
    with operacao(con, "sem seção", materia.pasta) as op:
        documentos.ligar_secao(op, materia.pasta, doc.id, None)
    with operacao(con, "ligar", materia.pasta) as op:
        assert documentos.ligar_sem_secao(op, materia.pasta, LIMIAR, 0.75) == 0
    assert documentos.obter(con, doc.id).secao_id is None and documentos.obter(con, doc.id).secao_decidida


def test_renomear_documento_ligado_a_mao_mantem_a_secao(con, materia, dois_livros):
    doc = _doc(con, materia, "resumo", "Polares")
    with operacao(con, "à mão", materia.pasta) as op:
        documentos.ligar_secao(op, materia.pasta, doc.id, dois_livros["secoes"]["14.7"])
    with operacao(con, "renomear", materia.pasta) as op:
        documentos.salvar(op, "resumo", doc.caminho.rsplit("/", 1)[1], "14.1 Funções", "corpo",
                          secao_id=dois_livros["secoes"]["14.7"])
    with operacao(con, "ligar", materia.pasta) as op:
        documentos.ligar_sem_secao(op, materia.pasta, LIMIAR, 0.75)
    assert documentos.obter(con, doc.id).secao_id == dois_livros["secoes"]["14.7"]


def test_listar_traz_codigo_e_posicao_na_ordem_do_livro(con, materia, dois_livros):
    s = dois_livros["secoes"]
    a = _doc(con, materia, "resumo", "A", secao_id=s["14.7"])
    b = _doc(con, materia, "resumo", "B", secao_id=s["10.3"])
    c = _doc(con, materia, "resumo", "C", secao_id=s["g14.1"])
    d = _doc(con, materia, "resumo", "D")
    por_id = {x.id: x for x in documentos.listar(con)}
    assert por_id[a.id].secao_codigo == "14.7"
    # livro principal primeiro, na ordem das páginas; depois o complementar; sem seção → None
    assert por_id[b.id].secao_posicao < por_id[a.id].secao_posicao < por_id[c.id].secao_posicao
    assert por_id[d.id].secao_posicao is None


def test_documento_sem_codigo_pelo_sentido(con, materia, dois_livros):
    from test_importacao_vinculo import SentidoFixo
    doc = _doc(con, materia, "resumo", "Extremos")
    assert secao_do_documento(con, doc, LIMIAR) is None
    sentido = SentidoFixo({"Valores Máximo e Mínimo": 0.95}, padrao=0.3)
    s = secao_do_documento(con, doc, LIMIAR, semantica=sentido, peso=0.5)
    assert s.secao_id == dois_livros["secoes"]["14.7"] and s.por == "sentido"
