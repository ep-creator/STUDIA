import pytest

from estudos.db.conexao import conectar
from estudos.erros import DadoInvalido, NaoEncontrado
from estudos.workspace import SUBPASTAS, abrir_materia, criar_materia, descobrir_materias, nome_pasta_valido


def test_criar_e_descobrir_com_acentos(tmp_path):
    ref = criar_materia(tmp_path, "Cálculo 2", "2026.2")
    pasta = tmp_path / "Cálculo 2"
    assert (pasta / "materia.db").exists()
    assert all((pasta / p).is_dir() for p in SUBPASTAS)
    assert [m.uid for m in descobrir_materias(tmp_path)] == [ref.uid]
    linha = conectar(ref.db).execute("SELECT nome, periodo, uid FROM materia").fetchone()
    assert tuple(linha) == ("Cálculo 2", "2026.2", ref.uid)


@pytest.mark.parametrize("nome", ["", "  ", "a/b", "CON", "nul", "x:y", "fim.", "a\\b", "_oculta", ".oculta"])
def test_nome_invalido(nome):
    with pytest.raises(DadoInvalido):
        nome_pasta_valido(nome)


def test_nome_valido_remove_espacos_das_pontas():
    assert nome_pasta_valido("  Física 1 ") == "Física 1"


def test_ignora_pastas_sem_db_e_com_underscore(tmp_path):
    (tmp_path / "_app").mkdir()
    (tmp_path / "solta").mkdir()
    criar_materia(tmp_path, "Física 1")
    assert [m.nome for m in descobrir_materias(tmp_path)] == ["Física 1"]


def test_criar_duplicada(tmp_path):
    criar_materia(tmp_path, "EDO")
    with pytest.raises(DadoInvalido):
        criar_materia(tmp_path, "EDO")


def test_abrir_por_uid(tmp_path):
    ref = criar_materia(tmp_path, "EDO")
    assert abrir_materia(tmp_path, ref.uid) == ref


def test_abrir_por_uid_inexistente(tmp_path):
    with pytest.raises(NaoEncontrado):
        abrir_materia(tmp_path, "naoexiste")


def test_banco_corrompido_e_ignorado(tmp_path):
    criar_materia(tmp_path, "Boa")
    ruim = tmp_path / "Ruim"
    ruim.mkdir()
    (ruim / "materia.db").write_bytes(b"isto nao e um banco sqlite" * 100)
    assert [m.nome for m in descobrir_materias(tmp_path)] == ["Boa"]
