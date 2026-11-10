import datetime

import pytest

from estudos.historico import operacao
from estudos.importacao import pipeline
from estudos.importacao.classificador import classificar
from estudos.importacao.parsers.calendario import dia_mes, extrair_calendario_tabelas
from estudos.importacao.pdf import abrir_pdf
from estudos.config import carregar_settings
from estudos.repos import eventos, materia as repo_materia, unidades
from pdfs_sinteticos import criar_pdf_tabela

# Planejamento de aulas: uma linha por aula (como o de Sistemas Digitais)
PLANEJAMENTO = [
    ["Data", "Dia", "Descrição", "Horas"],
    ["11-ago", "Terça", "Portas Lógicas", "2"],
    ["13-ago", "Quinta", "Álgebra Booleana", "4"],
    ["8-set", "Terça", "Prova Area 2", "6"],
    ["22-set", "Terça", "Prova 1 (SD)", "8"],
    ["6-out", "Terça", "Latches e Flip Flops", "10"],
    ["17-nov", "Terça", "Prova 2 (SD)", "12"],
    ["24-nov", "Terça", "Revisão Geral", "14"],
    ["26-nov", "Quinta", "2a Cham (SD)", "16"],
    ["8-dez", "Terça", "Prova Final (SD)", "18"],
]

# Grade de provas de um departamento: dias nas colunas, horários nas linhas, matérias nas células
GRADE = [
    ("1ª Unidade", [
        ["Horário", "08.09 (3ª feira)", "09.09 (4ª feira)"],
        ["08:00 -\n10:30", "Estatística", "Física 3\nFísica 4"],
        ["14:30 -\n17:00", "Química 1", "Cálculo 2"],
    ]),
    ("Quadro de Horário das Provas da 2ª Unidade", [
        ["Horário", "19.10 (2ª feira)", "20.10 (3ª feira)"],
        ["08:00 -\n10:30", "Cálculo 1", "Estatística"],
        ["14:30 -\n17:00", "Cálculo 2", "Química 1"],
    ]),
    ("EXAME DE SEGUNDA CHAMADA", [
        ["Horário", "09.12 (4ª feira)", "10.12 (5ª feira)"],
        ["14:30 - 17:00", "Cálculo 1, 2 e 3", "Física 1, 2, 3 e 4"],
    ]),
]


def _planejamento(tmp_path):
    return criar_pdf_tabela(tmp_path / "PlanejamentoAulas.pdf", "Sistemas Digitais (Eng. Computação)",
                            [("", PLANEJAMENTO)])


def _grade(tmp_path):
    return criar_pdf_tabela(tmp_path / "Provas.pdf", "CALENDÁRIO DAS PROVAS", GRADE)


@pytest.mark.parametrize("texto, esperado", [
    ("15/09", (15, 9)), ("08.09 (3ª feira)", (8, 9)), ("11-ago", (11, 8)), ("1-set", (1, 9)),
    ("3 de dezembro", (3, 12)), ("04/02/27 – último dia", (4, 2)),
    ("Terça", None), ("08:00 - 10:30", None), ("2", None), ("1.5 Regra da cadeia", None),
])
def test_dia_mes(texto, esperado):
    assert dia_mes(texto) == esperado


def test_pdf_le_tabelas_com_o_titulo_de_cima(tmp_path):
    tabelas = abrir_pdf(_grade(tmp_path)).tabelas()
    assert len(tabelas) == 3
    assert "1ª Unidade" in tabelas[0].titulo and "2ª Unidade" in tabelas[1].titulo
    assert [c.texto for c in tabelas[0].linhas[0]] == ["Horário", "08.09 (3ª feira)", "09.09 (4ª feira)"]
    assert tabelas[0].linhas[1][2].texto == "Física 3\nFísica 4"


def test_planejamento_uma_linha_por_aula(tmp_path):
    cal = extrair_calendario_tabelas(abrir_pdf(_planejamento(tmp_path)).tabelas(), 2026, "Sistemas Digitais")
    u1, u2 = cal.unidades
    assert [a.data for a in u1.aulas] == ["2026-08-11", "2026-08-13", "2026-09-08"]
    assert u1.aulas[0].descricao == "Portas Lógicas" and not u1.aulas[0].revisar
    assert u1.aulas[2].revisar  # "Prova Area 2" fala de prova sem dizer qual: quem decide é o usuário
    assert (u1.prova.tipo, u1.prova.data) == ("prova", "2026-09-22")
    # o que vem depois da última prova fica na última unidade
    assert [a.data for a in u2.aulas] == ["2026-10-06", "2026-11-24"] and u2.prova.data == "2026-11-17"
    assert [(e.tipo, e.data) for e in cal.eventos] == [("segunda_chamada", "2026-11-26"), ("exame_final", "2026-12-08")]


def test_grade_de_provas_pega_so_a_materia(tmp_path):
    cal = extrair_calendario_tabelas(abrir_pdf(_grade(tmp_path)).tabelas(), 2026, "Cálculo 2")
    assert [(u.numero, u.prova.data, u.prova.hora_inicio, u.prova.hora_fim) for u in cal.unidades] == [
        (1, "2026-09-09", "14:30", "17:00"), (2, "2026-10-19", "14:30", "17:00")]
    assert all(u.aulas == [] for u in cal.unidades)
    # "Cálculo 1, 2 e 3" inclui Cálculo 2
    assert [(e.tipo, e.data, e.hora_inicio) for e in cal.eventos] == [("segunda_chamada", "2026-12-09", "14:30")]


def test_grade_sem_a_materia_nao_inventa_prova(tmp_path):
    cal = extrair_calendario_tabelas(abrir_pdf(_grade(tmp_path)).tabelas(), 2026, "Sistemas Digitais")
    assert cal.unidades == [] and cal.eventos == []


def test_classifica_tabelas_de_datas_como_calendario(tmp_path):
    assert classificar(abrir_pdf(_planejamento(tmp_path))).tipo == "calendario"
    assert classificar(abrir_pdf(_grade(tmp_path))).tipo == "calendario"


def test_pipeline_usa_a_tabela_quando_o_texto_nao_tem_datas(con, materia, tmp_path):
    settings = carregar_settings(tmp_path / "_app", tmp_path)
    with operacao(con, "período", materia.pasta) as op:
        repo_materia.atualizar(op, periodo="2026.2")
    caminho = _planejamento(tmp_path / "entrada")
    imp = pipeline.receber_arquivo(con, materia.pasta, caminho, caminho.name, settings)
    assert imp.tipo == "calendario" and not imp.proposta["revisar"]
    pipeline.confirmar(con, materia.pasta, imp.id, settings)
    assert [(u.numero, u.data_prova) for u in unidades.listar(con)] == [(1, "2026-09-22"), (2, "2026-11-17")]
    assert {e.tipo for e in eventos.listar(con)} == {"aula", "prova", "segunda_chamada", "exame_final"}


def test_materia_sem_periodo_usa_o_ano_do_nome_do_arquivo(con, materia, tmp_path):
    # Sistemas Digitais e Geometria Analítica foram criadas sem período: sem ano, toda data era descartada
    settings = carregar_settings(tmp_path / "_app", tmp_path)
    caminho = criar_pdf_tabela(tmp_path / "entrada" / "PlanejamentoAulas_SD_2026_2.pdf", "Sistemas Digitais",
                               [("", PLANEJAMENTO)])
    imp = pipeline.receber_arquivo(con, materia.pasta, caminho, caminho.name, settings)
    assert imp.proposta["ano"] == 2026 and imp.proposta["unidades"][0]["prova"]["data"] == "2026-09-22"


def test_sem_ano_em_lugar_nenhum_usa_o_ano_atual(con, materia, tmp_path):
    settings = carregar_settings(tmp_path / "_app", tmp_path)
    caminho = _planejamento(tmp_path / "entrada")
    imp = pipeline.receber_arquivo(con, materia.pasta, caminho, caminho.name, settings)
    assert imp.proposta["ano"] == datetime.date.today().year and imp.proposta["unidades"]
