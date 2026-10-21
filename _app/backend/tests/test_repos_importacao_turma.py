import pytest

from estudos.erros import DadoInvalido, NaoEncontrado
from estudos.historico import desfazer_ultimo, operacao
from estudos.repos import fontes, importacoes, turma


@pytest.fixture
def fonte(con, materia):
    (materia.pasta / "fontes/documentos/p.pdf").write_bytes(b"%PDF programa")
    with operacao(con, "x", materia.pasta) as op:
        return fontes.registrar(op, "programa", "fontes/documentos/p.pdf")


def test_ciclo_da_importacao(con, fonte):
    i = importacoes.criar(con, fonte, "programa", {"unidades": []})
    imp = importacoes.obter(con, i)
    assert (imp.estado, imp.proposta, imp.confirmada_em) == ("proposta", {"unidades": []}, None)
    importacoes.atualizar_proposta(con, i, {"unidades": [{"numero": 1}]})
    assert importacoes.obter(con, i).proposta == {"unidades": [{"numero": 1}]}
    assert importacoes.por_fonte(con, fonte).id == i
    importacoes.marcar(con, i, "confirmada")
    imp = importacoes.obter(con, i)
    assert imp.estado == "confirmada" and imp.confirmada_em is not None
    with pytest.raises(DadoInvalido):
        importacoes.atualizar_proposta(con, i, {})
    assert [x.id for x in importacoes.listar(con, "confirmada")] == [i] and importacoes.listar(con, "proposta") == []


def test_importacao_nao_entra_no_historico(con, fonte):
    importacoes.criar(con, fonte, "programa", {})
    assert con.execute("SELECT count(*) FROM historico_mudanca WHERE tabela = 'importacao'").fetchone()[0] == 0


def test_importacao_inexistente(con):
    with pytest.raises(NaoEncontrado):
        importacoes.obter(con, 99)


def test_estado_invalido(con, fonte):
    i = importacoes.criar(con, fonte, "programa", {})
    with pytest.raises(DadoInvalido):
        importacoes.marcar(con, i, "talvez")


def test_apagar_fonte_apaga_importacao(con, fonte):
    importacoes.criar(con, fonte, "programa", {})
    con.execute("DELETE FROM fonte WHERE id = ?", (fonte,))
    assert importacoes.listar(con) == []


def test_horarios_e_criterios_substituidos_e_desfaziveis(con):
    with operacao(con, "v1") as op:
        turma.definir_horarios(op, [(2, "13:00", "15:00"), (4, "15:00", "17:00")])
        turma.definir_criterios(op, ["Justificar", "Não omitir passos"], origem="importado")
    with operacao(con, "v2") as op:
        turma.definir_horarios(op, [(0, "08:00", "10:00")])
    assert [(h.dia_semana, h.hora_inicio) for h in turma.listar_horarios(con)] == [(0, "08:00")]
    desfazer_ultimo(con)
    assert [(h.dia_semana, h.hora_fim) for h in turma.listar_horarios(con)] == [(2, "15:00"), (4, "17:00")]
    assert [(c.ordem, c.texto, c.origem) for c in turma.listar_criterios(con)] == [
        (1, "Justificar", "importado"), (2, "Não omitir passos", "importado")]


def test_dia_da_semana_invalido(con):
    with operacao(con, "x") as op, pytest.raises(DadoInvalido):
        turma.definir_horarios(op, [(7, "08:00", "10:00")])
