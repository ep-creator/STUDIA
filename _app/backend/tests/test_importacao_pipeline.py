import pytest

from estudos.config import carregar_settings
from estudos.erros import DadoInvalido
from estudos.historico import desfazer_ultimo
from estudos.importacao import pipeline
from estudos.importacao.pdf import PdfInvalido
from estudos.repos import eventos, fontes, importacoes, listas, livros, topicos, unidades
from pdfs_sinteticos import DISCIPLINA, STEWART

pytestmark = pytest.mark.skipif(not (DISCIPLINA / "Programa.pdf").is_file(), reason="PDFs reais ausentes")


@pytest.fixture
def settings(tmp_path):
    return carregar_settings(tmp_path / "_app", tmp_path)


def _receber(con, materia, settings, caminho):
    return pipeline.receber_arquivo(con, materia.pasta, caminho, caminho.name, settings)


def test_programa_propoe_e_confirma(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    assert imp.tipo == "programa" and imp.estado == "proposta"
    assert [u["numero"] for u in imp.proposta["unidades"]] == [1, 2, 3]
    assert (materia.pasta / "fontes/documentos/Programa.pdf").is_file()
    resumo = pipeline.confirmar(con, materia.pasta, imp.id)
    assert resumo["unidades"] == 3 and resumo["topicos"] >= 30
    u3 = next(u for u in unidades.listar(con) if u.numero == 3)
    titulos = [t.titulo for t in topicos.listar(con, u3.id)]
    assert "Integração em três variáveis" in titulos and "Coordenadas esféricas" in titulos
    assert importacoes.obter(con, imp.id).estado == "confirmada"


def test_calendario_depois_do_programa(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id)
    imp = _receber(con, materia, settings, DISCIPLINA / "Calendario.pdf")
    pipeline.confirmar(con, materia.pasta, imp.id)
    assert [(u.numero, u.data_prova) for u in unidades.listar(con)] == [
        (1, "2026-09-14"), (2, "2026-10-19"), (3, "2026-11-30")]
    prova = [e for e in eventos.listar(con) if e.tipo == "prova"][0]
    assert (prova.hora_inicio, prova.hora_fim) == ("14:30", "17:00")
    assert {e.tipo for e in eventos.listar(con)} >= {"aula", "extra", "prova", "segunda_chamada", "exame_final"}


def test_calendario_reimportado_nao_duplica(con, materia, settings, tmp_path):
    copia = tmp_path / "outro" / "Calendario.pdf"
    copia.parent.mkdir()
    copia.write_bytes((DISCIPLINA / "Calendario.pdf").read_bytes() + b"\n%fim")  # sha diferente, mesmo conteúdo
    for caminho in (DISCIPLINA / "Calendario.pdf", copia):
        pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, caminho).id)
    assert len([e for e in eventos.listar(con) if e.tipo == "prova"]) == 3


def test_mesmo_arquivo_duas_vezes(con, materia, settings):
    a = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    b = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    assert a.id == b.id and len(fontes.listar(con)) == 1


def test_reprocessar_com_outro_tipo(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    novo = pipeline.reprocessar(con, materia.pasta, imp.id, "outro", settings)
    assert novo.tipo == "outro" and "unidades" not in novo.proposta
    assert fontes.listar(con)[0].tipo == "outro"


def test_confirmar_duas_vezes(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    pipeline.confirmar(con, materia.pasta, imp.id)
    with pytest.raises(DadoInvalido):
        pipeline.confirmar(con, materia.pasta, imp.id)


def test_descartar(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    pipeline.descartar(con, imp.id)
    assert importacoes.obter(con, imp.id).estado == "descartada" and unidades.listar(con) == []
    with pytest.raises(DadoInvalido):
        pipeline.confirmar(con, materia.pasta, imp.id)


def test_desfazer_a_importacao(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id)
    desfazer_ultimo(con, materia.pasta)
    assert unidades.listar(con) == []


def test_turma(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "info_S3.pdf")
    assert imp.tipo == "turma" and len(imp.proposta["criterios"]) == 6
    pipeline.confirmar(con, materia.pasta, imp.id)
    m = con.execute("SELECT professor, email_professor FROM materia").fetchone()
    assert tuple(m) == ("Henrique Araújo", "henrique.araujo@ufpe.br")
    assert con.execute("SELECT count(*) FROM criterio_correcao").fetchone()[0] == 6
    assert con.execute("SELECT count(*) FROM horario_aula").fetchone()[0] == 2


def test_pdf_invalido(con, materia, settings, tmp_path):
    falso = tmp_path / "falso.pdf"
    falso.write_text("não é pdf", encoding="utf-8")
    with pytest.raises(PdfInvalido):
        _receber(con, materia, settings, falso)
    assert fontes.listar(con) == []


@pytest.mark.skipif(not STEWART.is_file(), reason="Stewart ausente")
def test_livro_programa_e_lista_se_ligam(con, materia, settings):
    livro = _receber(con, materia, settings, STEWART)
    assert livro.tipo == "livro" and livro.proposta["papel"] == "principal"
    pipeline.confirmar(con, materia.pasta, livro.id)
    principal = livros.principal(con)
    assert livros.secao_por_codigo(con, principal.fonte_id, "15.8").pagina_pdf_ini == 433

    programa = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    u3 = next(u for u in programa.proposta["unidades"] if u["numero"] == 3)
    triplas = next(t for t in u3["topicos"] if t["titulo"] == "Integração em três variáveis")
    cilindricas = next(f for f in triplas["filhos"] if f["titulo"] == "Integrais triplas em coordenadas cilíndricas")
    assert cilindricas["secoes"][0]["codigo"] == "15.8"
    pipeline.confirmar(con, materia.pasta, programa.id)

    lista = _receber(con, materia, settings, DISCIPLINA / "exercicios_3un.pdf")
    assert lista.tipo == "lista" and lista.proposta["unidade"]["numero"] == 3
    pipeline.confirmar(con, materia.pasta, lista.id)
    u3_id = next(u.id for u in unidades.listar(con) if u.numero == 3)
    codigos = [l.codigo for l in listas.listar(con, u3_id)]
    assert codigos == ["15.4", "15.5", "15.7", "15.8", "15.9", "15.10"]
    l158 = next(l for l in listas.listar(con, u3_id) if l.codigo == "15.8")
    assert con.execute("SELECT count(*) FROM lista_secao WHERE lista_id = ?", (l158.id,)).fetchone()[0] == 1
    assert len(listas.listar_questoes(con, l158.id)) == 8
