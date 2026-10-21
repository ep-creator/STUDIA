import pytest

from estudos.importacao.parsers.turma import extrair_turma
from estudos.importacao.pdf import abrir_pdf
from pdfs_sinteticos import DISCIPLINA


@pytest.fixture
def turma():
    caminho = DISCIPLINA / "info_S3.pdf"
    if not caminho.is_file():
        pytest.skip("arquivo real ausente")
    return extrair_turma(abrir_pdf(caminho).texto())


def test_professor_e_email(turma):
    assert (turma.professor, turma.email) == ("Henrique Araújo", "henrique.araujo@ufpe.br")


def test_horarios(turma):
    assert turma.horarios == [(2, "13:00", "15:00"), (4, "15:00", "17:00")]


def test_referencias(turma):
    assert [(r.papel, r.texto) for r in turma.referencias] == [
        ("principal", "J. Stewart, Cálculo, V. 2, sétima edição."),
        ("complementar", "L. Leithold, O Cálculo com Geometria Analítica, V.1"),
        ("complementar", "Guidorizzi, Um Curso de Cálculo, V.2"),
    ]


def test_criterios(turma):
    assert len(turma.criterios) == 6
    assert turma.criterios[0] == (
        "Deve ser dado o embasamento teórico para os procedimentos utilizados, com a apresentação dos resultados "
        "gerais relevantes, dentre aqueles vistos em aula"
    )
    assert turma.criterios[-1] == "Deve haver clareza e organização"


def test_texto_sem_nada():
    t = extrair_turma("Um documento qualquer\ncom texto solto.")
    assert (t.professor, t.email, t.horarios, t.referencias, t.criterios) == (None, None, [], [], [])


def test_horario_com_minutos_e_hifen():
    t = extrair_turma("Horário\nSegunda-feira: 8h30–10h10\nTerças-feiras: 10h-12h")
    assert t.horarios == [(0, "08:30", "10:10"), (1, "10:00", "12:00")]


@pytest.mark.parametrize("linha,professor", [
    ("E-mail: prof@x.com", None),
    ("Coordenação: coord@x.com", None),
    ("Prof. Fulano de Tal – fulano@ufpe.br", "Prof. Fulano de Tal"),
    ("Professor: Ana Lima - ana@x.br", "Ana Lima"),
])
def test_professor_com_rotulos(linha, professor):
    assert extrair_turma(linha).professor == professor
