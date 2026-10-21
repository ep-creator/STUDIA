import pytest

from estudos.erros import DadoInvalido
from estudos.historico import desfazer_ultimo, operacao
from estudos.modelos import QuestaoEntrada
from estudos.repos import listas, marcacoes, topicos, unidades


@pytest.fixture
def base(con):
    """Unidade 1, tópico pendente e lista 'auto' vinculada a ele."""
    with operacao(con, "base") as op:
        u = unidades.criar(op, 1)
        t = topicos.criar(op, u, "Limites")
        lista = listas.criar(op, "L1", "Lista 1", u)
        listas.vincular_topico(op, lista, t)
    return {"u": u, "t": t, "lista": lista}


def test_lista_auto_abre_quando_topico_visto(con, base):
    assert listas.obter(con, base["lista"]).aberta is False
    with operacao(con, "visto") as op:
        topicos.definir_status(op, base["t"], "visto")
    assert listas.obter(con, base["lista"]).aberta is True
    with operacao(con, "pendente") as op:
        topicos.definir_status(op, base["t"], "pendente")
    assert listas.obter(con, base["lista"]).aberta is False


def test_lista_auto_abre_pela_secao_do_topico(con, base):
    with operacao(con, "livro") as op:
        con.execute("INSERT INTO fonte (tipo, caminho, sha256, importada_em, origem) VALUES ('livro', 'l.pdf', 'h', 'x', 'manual')")
        con.execute("INSERT INTO livro (fonte_id, papel) VALUES (1, 'principal')")
        con.execute("INSERT INTO secao_livro (livro_id, codigo, titulo, pagina_pdf_ini, pagina_pdf_fim, origem) VALUES (1, '15.4', 'Polares', 1, 2, 'manual')")
        con.execute("INSERT INTO topico_secao (topico_id, secao_id) VALUES (?, 1)", (base["t"],))
        outra = listas.criar(op, "15.4", "Seção 15.4", base["u"])
        listas.vincular_secao(op, outra, 1)
        topicos.definir_status(op, base["t"], "visto")
    assert listas.obter(con, outra).aberta is True


def test_liberacao_manual_tem_precedencia(con, base):
    with operacao(con, "x") as op:
        topicos.definir_status(op, base["t"], "visto")
        listas.definir_liberacao(op, base["lista"], "travada")
    assert listas.obter(con, base["lista"]).aberta is False
    with operacao(con, "y") as op:
        topicos.definir_status(op, base["t"], "pendente")
        listas.definir_liberacao(op, base["lista"], "aberta")
    assert listas.obter(con, base["lista"]).aberta is True


def test_sincronizar_preserva_marcacao(con, base):
    lista = base["lista"]
    with operacao(con, "v1") as op:
        ids = listas.sincronizar_questoes(op, lista, [QuestaoEntrada("6(a)"), QuestaoEntrada("7", linha=2)])
        marcacoes.definir(op, ids["7"], "err")
    with operacao(con, "v2") as op:
        ids2 = listas.sincronizar_questoes(
            op, lista, [QuestaoEntrada("7", linha=2, enunciado_md="novo"), QuestaoEntrada("8")]
        )
    assert ids2["7"] == ids["7"]
    assert marcacoes.estados(con, base["u"])[ids["7"]] == "err"
    questoes = listas.listar_questoes(con, lista)
    assert [(q.rotulo, q.ordem, q.enunciado_md) for q in questoes] == [("7", 1, "novo"), ("8", 2, "")]


def test_desfazer_sincronizacao_restaura_questao_e_marcacao(con, base):
    lista = base["lista"]
    with operacao(con, "v1") as op:
        ids = listas.sincronizar_questoes(op, lista, [QuestaoEntrada("6(a)"), QuestaoEntrada("7")])
        marcacoes.definir(op, ids["6(a)"], "ok")
    with operacao(con, "v2 sem 6(a)") as op:
        listas.sincronizar_questoes(op, lista, [QuestaoEntrada("7")])
    desfazer_ultimo(con)
    rotulos = {q.rotulo: q.id for q in listas.listar_questoes(con, lista)}
    assert rotulos["6(a)"] == ids["6(a)"]
    assert marcacoes.estados(con, base["u"])[ids["6(a)"]] == "ok"


def test_rotulo_duplicado_na_entrada(con, base):
    with operacao(con, "x") as op, pytest.raises(DadoInvalido):
        listas.sincronizar_questoes(op, base["lista"], [QuestaoEntrada("1"), QuestaoEntrada("1")])


def test_linha_invalida(con, base):
    with operacao(con, "x") as op, pytest.raises(DadoInvalido):
        listas.sincronizar_questoes(op, base["lista"], [QuestaoEntrada("1", linha=3)])


def test_desmarcar(con, base):
    with operacao(con, "x") as op:
        q = listas.sincronizar_questoes(op, base["lista"], [QuestaoEntrada("1")])["1"]
        marcacoes.definir(op, q, "dub")
        marcacoes.definir(op, q, None)
    assert marcacoes.estados(con, base["u"]) == {}


def test_placar(con, base):
    with operacao(con, "x") as op:
        listas.definir_liberacao(op, base["lista"], "aberta")
        ids = listas.sincronizar_questoes(op, base["lista"], [
            QuestaoEntrada("1"), QuestaoEntrada("2"), QuestaoEntrada("3"),
            QuestaoEntrada("4", linha=2), QuestaoEntrada("5", linha=2),
        ])
        for rotulo, estado in (("1", "ok"), ("2", "err"), ("3", "dub"), ("4", "ok")):
            marcacoes.definir(op, ids[rotulo], estado)
        travada = listas.criar(op, "L2", "Lista 2", base["u"], liberacao="travada")
        q = listas.sincronizar_questoes(op, travada, [QuestaoEntrada("1")])["1"]
        marcacoes.definir(op, q, "ok")
    p = marcacoes.placar(con, base["u"])
    assert (p.ok, p.err, p.dub, p.total) == (2, 1, 1, 5)
    assert (p.feitos_linha1, p.total_linha1, p.feitos_linha2, p.total_linha2) == (3, 3, 1, 2)
    assert p.taxa_acerto == pytest.approx(2 / 3)


def test_placar_vazio(con, base):
    p = marcacoes.placar(con, base["u"])
    assert (p.total, p.taxa_acerto) == (0, None)


def test_estado_invalido(con, base):
    with operacao(con, "x") as op:
        q = listas.sincronizar_questoes(op, base["lista"], [QuestaoEntrada("1")])["1"]
    with operacao(con, "y") as op, pytest.raises(DadoInvalido):
        marcacoes.definir(op, q, "talvez")


def test_listar_por_unidade_em_ordem(con, base):
    with operacao(con, "x") as op:
        listas.criar(op, "L2", "Lista 2", base["u"])
    assert [l.codigo for l in listas.listar(con, base["u"])] == ["L1", "L2"]
