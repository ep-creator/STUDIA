from datetime import date

import pytest

from estudos.erros import DadoInvalido
from estudos.historico import desfazer_ultimo, operacao
from estudos.repos import eventos, materia, topicos, unidades


def _tres_unidades(con):
    with operacao(con, "base") as op:
        for numero, prova in ((1, "2026-09-14"), (2, "2026-10-19"), (3, "2026-11-30")):
            u = unidades.criar(op, numero)
            eventos.criar(op, "prova", prova, unidade_id=u, hora_inicio="14:30", hora_fim="17:00")


def test_materia_obter_e_atualizar(con):
    with operacao(con, "x") as op:
        materia.atualizar(op, professor="Henrique Araújo")
    m = materia.obter(con)
    assert m.nome == "Matéria Teste" and m.professor == "Henrique Araújo"


def test_data_prova_vem_do_evento(con):
    with operacao(con, "x") as op:
        u = unidades.criar(op, 1)
        eventos.criar(op, "prova", "2026-09-14", unidade_id=u, hora_inicio="14:30")
    assert unidades.listar(con)[0].data_prova == "2026-09-14"


def test_unidade_sem_prova(con):
    with operacao(con, "x") as op:
        unidades.criar(op, 1, "Derivadas")
    u = unidades.listar(con)[0]
    assert (u.numero, u.titulo, u.data_prova) == (1, "Derivadas", None)


def test_unidade_atual(con):
    _tres_unidades(con)
    assert unidades.unidade_atual(con, date(2026, 10, 21)).numero == 3
    assert unidades.unidade_atual(con, date(2026, 9, 14)).numero == 1
    assert unidades.unidade_atual(con, date(2027, 1, 1)).numero == 3


def test_unidade_atual_sem_unidades(con):
    assert unidades.unidade_atual(con, date(2026, 10, 21)) is None


def test_quantidade_livre_de_unidades(con):
    with operacao(con, "x") as op:
        for n in range(1, 6):
            unidades.criar(op, n)
    assert [u.numero for u in unidades.listar(con)] == [1, 2, 3, 4, 5]


def test_eventos_ordenados_e_filtrados(con):
    _tres_unidades(con)
    with operacao(con, "x") as op:
        eventos.criar(op, "aula", "2026-08-12", unidade_id=unidades.listar(con)[0].id)
    datas = [e.data for e in eventos.listar(con, unidades.listar(con)[0].id)]
    assert datas == ["2026-08-12", "2026-09-14"]
    assert len(eventos.listar(con)) == 4


def test_topicos_ordem_e_hierarquia(con):
    with operacao(con, "x") as op:
        u = unidades.criar(op, 1)
        pai = topicos.criar(op, u, "Diferenciabilidade")
        topicos.criar(op, u, "Regra da cadeia", pai_id=pai)
        topicos.criar(op, u, "Derivação implícita", pai_id=pai)
        outro = topicos.criar(op, u, "Limites")
    lista = topicos.listar(con, u)
    assert [t.titulo for t in lista] == ["Diferenciabilidade", "Regra da cadeia", "Derivação implícita", "Limites"]
    assert [t.ordem for t in lista] == [1, 1, 2, 2]
    assert lista[-1].id == outro and lista[1].pai_id == pai


def test_status_invalido(con):
    with operacao(con, "x") as op:
        t = topicos.criar(op, unidades.criar(op, 1), "Limites")
    with operacao(con, "y") as op, pytest.raises(DadoInvalido):
        topicos.definir_status(op, t, "talvez")


def test_desfazer_status_topico(con):
    with operacao(con, "x") as op:
        t = topicos.criar(op, unidades.criar(op, 1), "Limites")
    with operacao(con, "visto") as op:
        topicos.definir_status(op, t, "visto")
    desfazer_ultimo(con)
    assert topicos.listar(con, 1)[0].status == "pendente"


def test_tipo_evento_invalido(con):
    with operacao(con, "x") as op, pytest.raises(DadoInvalido):
        eventos.criar(op, "palestra", "2026-08-12")
