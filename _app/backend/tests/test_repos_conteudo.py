import pytest

from estudos.conteudo import ler_md
from estudos.erros import DadoInvalido
from estudos.historico import desfazer_ultimo, operacao
from estudos.modelos import QuestaoEntrada
from estudos.repos import cronograma, documentos, formulas, listas, unidades
from estudos.seguranca import CaminhoInvalido


@pytest.fixture
def u(con):
    with operacao(con, "base") as op:
        return unidades.criar(op, 3)


def test_salvar_resumo_nao_altera_corpo(con, materia, u):
    corpo = "# 15.4\n\n> Referência\n\ntexto"
    with operacao(con, "x", materia.pasta) as op:
        documentos.salvar(op, "resumo", "polares", "Polares", corpo, unidade_id=u)
    doc = documentos.listar(con, "resumo")[0]
    assert doc.caminho == "conteudo/resumos/polares.md"
    assert documentos.ler_corpo(materia.pasta, doc) == corpo
    meta = ler_md(materia.pasta / doc.caminho).meta
    assert meta["tipo"] == "resumo" and meta["unidade"] == 3 and meta["titulo"] == "Polares"


def test_salvar_mesmo_nome_atualiza(con, materia, u):
    with operacao(con, "v1", materia.pasta) as op:
        id1 = documentos.salvar(op, "resumo", "polares.md", "Polares", "v1")
    with operacao(con, "v2", materia.pasta) as op:
        id2 = documentos.salvar(op, "resumo", "polares.md", "Polares", "v2")
    assert id1 == id2 and len(documentos.listar(con)) == 1


def test_desfazer_sobrescrita_restaura_arquivo(con, materia, u):
    with operacao(con, "v1", materia.pasta) as op:
        documentos.salvar(op, "resolucao", "15-4-22", "15.4 #22", "v1")
    with operacao(con, "v2", materia.pasta) as op:
        documentos.salvar(op, "resolucao", "15-4-22", "15.4 #22", "v2")
    doc = documentos.listar(con)[0]
    desfazer_ultimo(con, materia.pasta)
    assert documentos.ler_corpo(materia.pasta, doc) == "v1"
    desfazer_ultimo(con, materia.pasta)
    assert not (materia.pasta / doc.caminho).exists()
    assert documentos.listar(con) == []


def test_desfazer_remocao_de_documento(con, materia, u):
    with operacao(con, "v1", materia.pasta) as op:
        d = documentos.salvar(op, "plano", "plano-u3", "Plano", "conteúdo")
    with operacao(con, "apagar", materia.pasta) as op:
        documentos.remover(op, d)
    assert not (materia.pasta / "conteudo/planos/plano-u3.md").exists()
    desfazer_ultimo(con, materia.pasta)
    assert documentos.ler_corpo(materia.pasta, documentos.listar(con)[0]) == "conteúdo"


def test_desfazer_arquivo_sem_raiz(con, materia, u):
    with operacao(con, "v1", materia.pasta) as op:
        documentos.salvar(op, "resumo", "a", "A", "x")
    with pytest.raises(DadoInvalido):
        desfazer_ultimo(con)


@pytest.mark.parametrize("nome", ["../../x", "../resolucoes/x", "a/b"])
def test_documento_fora_da_pasta(con, materia, u, nome):
    with operacao(con, "x", materia.pasta) as op, pytest.raises(CaminhoInvalido):
        documentos.salvar(op, "resumo", nome, "X", "x")


def test_tipo_invalido(con, materia, u):
    with operacao(con, "x", materia.pasta) as op, pytest.raises(DadoInvalido):
        documentos.salvar(op, "receita", "a", "A", "x")


def test_sessao_questoes_e_feito(con, u):
    with operacao(con, "x") as op:
        lista = listas.criar(op, "L5", "Lista 5", u)
        ids = listas.sincronizar_questoes(op, lista, [QuestaoEntrada("1"), QuestaoEntrada("2"), QuestaoEntrada("3")])
        s = cronograma.criar_sessao(op, u, "P1", data="2026-10-25", foco_md="**Polares**")
        cronograma.vincular_questoes(op, s, [ids["1"], ids["3"]])
        cronograma.vincular_questoes(op, s, [ids["1"], ids["2"]])
        cronograma.definir_feito(op, s, True)
    sessao = cronograma.listar(con, u)[0]
    assert sessao.questao_ids == (ids["1"], ids["2"])
    assert sessao.feito is True and sessao.codigo == "P1" and sessao.ordem == 1


def test_formula_crud_e_desfazer(con, u):
    with operacao(con, "criar") as op:
        f = formulas.criar(op, u, "Polares", r"dA = r\,dr\,d\theta")
    with operacao(con, "editar") as op:
        formulas.atualizar(op, f, notas_md="Nunca esqueça o r")
    assert formulas.listar(con, u)[0].notas_md == "Nunca esqueça o r"
    desfazer_ultimo(con)
    assert formulas.listar(con, u)[0].notas_md == ""
    with operacao(con, "remover") as op:
        formulas.remover(op, f)
    assert formulas.listar(con, u) == []


def test_podar_remove_versoes_de_arquivo(con, materia, u):
    from estudos.historico import podar

    for n in range(3):
        with operacao(con, f"v{n}", materia.pasta) as op:
            documentos.salvar(op, "resumo", "a", "A", f"v{n}")
    versoes = [p for p in (materia.pasta / ".versoes").rglob("*.md") if p.is_file()]
    assert len(versoes) == 2
    podar(con, 1, materia.pasta)
    assert len([p for p in (materia.pasta / ".versoes").rglob("*.md") if p.is_file()]) == 1
