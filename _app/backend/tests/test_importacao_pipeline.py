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
    resumo = pipeline.confirmar(con, materia.pasta, imp.id, settings)
    assert resumo["unidades"] == 3 and resumo["topicos"] >= 30
    u3 = next(u for u in unidades.listar(con) if u.numero == 3)
    titulos = [t.titulo for t in topicos.listar(con, u3.id)]
    assert "Integração em três variáveis" in titulos and "Coordenadas esféricas" in titulos
    assert importacoes.obter(con, imp.id).estado == "confirmada"


def test_calendario_depois_do_programa(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id, settings)
    imp = _receber(con, materia, settings, DISCIPLINA / "Calendario.pdf")
    pipeline.confirmar(con, materia.pasta, imp.id, settings)
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
        pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, caminho).id, settings)
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
    pipeline.confirmar(con, materia.pasta, imp.id, settings)
    with pytest.raises(DadoInvalido):
        pipeline.confirmar(con, materia.pasta, imp.id, settings)


def test_descartar(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    pipeline.descartar(con, imp.id)
    assert importacoes.obter(con, imp.id).estado == "descartada" and unidades.listar(con) == []
    with pytest.raises(DadoInvalido):
        pipeline.confirmar(con, materia.pasta, imp.id, settings)


def test_desfazer_a_importacao(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id, settings)
    desfazer_ultimo(con, materia.pasta)
    assert unidades.listar(con) == []


def test_turma(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "info_S3.pdf")
    assert imp.tipo == "turma" and len(imp.proposta["criterios"]) == 6
    pipeline.confirmar(con, materia.pasta, imp.id, settings)
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
    pipeline.confirmar(con, materia.pasta, livro.id, settings)
    principal = livros.principal(con)
    assert livros.secao_por_codigo(con, principal.fonte_id, "15.8").pagina_pdf_ini == 433

    programa = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    u3 = next(u for u in programa.proposta["unidades"] if u["numero"] == 3)
    triplas = next(t for t in u3["topicos"] if t["titulo"] == "Integração em três variáveis")
    cilindricas = next(f for f in triplas["filhos"] if f["titulo"] == "Integrais triplas em coordenadas cilíndricas")
    assert cilindricas["secoes"][0]["codigo"] == "15.8"
    pipeline.confirmar(con, materia.pasta, programa.id, settings)

    lista = _receber(con, materia, settings, DISCIPLINA / "exercicios_3un.pdf")
    assert lista.tipo == "lista" and lista.proposta["unidade"]["numero"] == 3
    pipeline.confirmar(con, materia.pasta, lista.id, settings)
    u3_id = next(u.id for u in unidades.listar(con) if u.numero == 3)
    codigos = [l.codigo for l in listas.listar(con, u3_id)]
    assert codigos == ["15.4", "15.5", "15.7", "15.8", "15.9", "15.10"]
    l158 = next(l for l in listas.listar(con, u3_id) if l.codigo == "15.8")
    assert con.execute("SELECT count(*) FROM lista_secao WHERE lista_id = ?", (l158.id,)).fetchone()[0] == 1
    assert len(listas.listar_questoes(con, l158.id)) == 8


def test_reenviar_depois_de_descartar(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    pipeline.descartar(con, imp.id)
    novo = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    assert novo.id != imp.id and novo.estado == "proposta" and len(fontes.listar(con)) == 1


def test_reenviar_depois_de_desfazer_a_confirmacao(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    pipeline.confirmar(con, materia.pasta, imp.id, settings)
    desfazer_ultimo(con, materia.pasta)
    novo = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    assert novo.estado == "proposta"
    pipeline.confirmar(con, materia.pasta, novo.id, settings)
    assert len(unidades.listar(con)) == 3


@pytest.mark.parametrize("estrago", ["numero_texto", "sem_codigo", "listas_texto"])
def test_proposta_inconsistente_vira_dado_invalido(con, materia, settings, estrago):
    imp = _receber(con, materia, settings, DISCIPLINA / "exercicios_3un.pdf")
    proposta = imp.proposta
    if estrago == "numero_texto":
        proposta["listas"][0]["unidade"]["numero"] = "abc"
    elif estrago == "sem_codigo":
        del proposta["listas"][0]["codigo"]
    else:
        proposta["listas"] = "x"
    pipeline.editar(con, imp.id, proposta)  # proposta editada não é recalculada: o erro chega ao confirmar
    with pytest.raises(DadoInvalido, match="inconsistente"):
        pipeline.confirmar(con, materia.pasta, imp.id, settings)
    assert importacoes.obter(con, imp.id).estado == "proposta"


def test_lista_sem_questoes_pede_revisao(con, materia, settings, tmp_path):
    from pdfs_sinteticos import criar_pdf

    caminho = criar_pdf(tmp_path / "vazia.pdf", ["Lista de exercícios de revisão\nSem questões numeradas aqui."])
    imp = pipeline.reprocessar(con, materia.pasta, _receber(con, materia, settings, caminho).id, "lista", settings)
    assert imp.proposta["listas"][0]["revisar"] is True


def _vinculos_topico_secao(con):
    return con.execute("SELECT count(*) FROM topico_secao").fetchone()[0]


@pytest.mark.skipif(not STEWART.is_file(), reason="Stewart ausente")
def test_tudo_enviado_antes_de_confirmar_da_o_mesmo_resultado(con, materia, settings):
    """Ordem não importa: as propostas pendentes são recalculadas com o banco de quando são lidas/confirmadas."""
    programa = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    livro = _receber(con, materia, settings, STEWART)
    lista = _receber(con, materia, settings, DISCIPLINA / "listas-2026-1/Lista3_2026-1.pdf")
    assert lista.proposta["listas"][0]["unidade"]["numero"] is None  # ainda não há tópicos no banco

    pipeline.confirmar(con, materia.pasta, programa.id, settings)
    assert _vinculos_topico_secao(con) == 0  # o livro ainda não foi confirmado
    pendente = pipeline.atualizar_derivados(con, importacoes.obter(con, lista.id), settings)
    assert pendente.proposta["listas"][0]["unidade"]["numero"] == 2

    resumo = pipeline.confirmar(con, materia.pasta, livro.id, settings)  # livro depois do programa liga os tópicos
    assert resumo["vinculos"] >= 20 and _vinculos_topico_secao(con) >= 20
    pipeline.confirmar(con, materia.pasta, lista.id, settings)
    u2 = next(u.id for u in unidades.listar(con) if u.numero == 2)
    assert [l.codigo for l in listas.listar(con, u2)] == ["L3"]


@pytest.mark.skipif(not STEWART.is_file(), reason="Stewart ausente")
def test_topicos_do_programa_ganham_secao(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, STEWART).id, settings)
    programa = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")

    def achatar(itens):
        for t in itens:
            yield t
            yield from achatar(t["filhos"])

    todos = [t for u in programa.proposta["unidades"] for t in achatar(u["topicos"])]
    codigo = {t["titulo"]: t["secoes"][0]["codigo"] for t in todos if t["secoes"]}
    assert len(codigo) >= 20
    assert codigo["Integrais duplas em retângulos"] == "15.1" and codigo["Derivada direcional"] == "14.6"


def test_lista_1_cai_na_unidade_1(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id, settings)
    lista = _receber(con, materia, settings, DISCIPLINA / "listas-2026-1/Lista1_2026-1.pdf")
    assert lista.proposta["listas"][0]["unidade"]["numero"] == 1


def test_unidade_escolhida_na_revisao_sobrevive_e_o_resto_acompanha(con, materia, settings):
    lista = _receber(con, materia, settings, DISCIPLINA / "listas-2026-1/Lista3_2026-1.pdf")
    proposta = lista.proposta
    proposta["listas"][0]["unidade"]["numero"] = 3
    pipeline.editar(con, lista.id, proposta)
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id, settings)
    item = pipeline.atualizar_derivados(con, importacoes.obter(con, lista.id), settings).proposta["listas"][0]
    assert item["unidade"]["numero"] == 3 and item["unidade"]["manual"] is True
    # Os tópicos continuam sendo recalculados, agora só os da unidade escolhida
    assert all(t["unidade"] == 3 for t in item["topicos"])


def test_vinculo_recusado_continua_recusado(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id, settings)
    lista = _receber(con, materia, settings, DISCIPLINA / "listas-2026-1/Lista3_2026-1.pdf")
    proposta = lista.proposta
    recusado = proposta["listas"][0]["topicos"][0]["topico_id"]
    proposta["listas"][0]["topicos"][0]["aceito"] = False
    pipeline.editar(con, lista.id, proposta)
    pipeline.confirmar(con, materia.pasta, lista.id, settings)
    vinculados = {r[0] for r in con.execute("SELECT topico_id FROM lista_topico")}
    assert recusado not in vinculados


@pytest.mark.skipif(not STEWART.is_file(), reason="Stewart ausente")
def test_editar_sem_mudar_nada_nao_congela_a_proposta(con, materia, settings):
    """Achado da revisão: salvar a revisão não pode fazer a ordem dos envios voltar a importar."""
    programa = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    livro = _receber(con, materia, settings, STEWART)
    lista = _receber(con, materia, settings, DISCIPLINA / "exercicios_3un.pdf")
    for imp in (livro, lista):
        pipeline.editar(con, imp.id, importacoes.obter(con, imp.id).proposta)
    for imp in (programa, livro, lista):
        pipeline.confirmar(con, materia.pasta, imp.id, settings)
    assert con.execute("SELECT count(*) FROM topico_secao").fetchone()[0] >= 20
    assert con.execute("SELECT count(*) FROM lista_secao").fetchone()[0] == 6


def test_leitura_de_proposta_malformada_nao_quebra(con, materia, settings):
    imp = _receber(con, materia, settings, DISCIPLINA / "Programa.pdf")
    estragada = {**imp.proposta, "unidades": [{"numero": 1, "topicos": [{"filhos": []}]}]}  # tópico sem título
    importacoes.atualizar_proposta(con, imp.id, estragada)
    assert pipeline.para_leitura(con, importacoes.obter(con, imp.id), settings).proposta == estragada
    with pytest.raises(DadoInvalido, match="inconsistente"):
        pipeline.confirmar(con, materia.pasta, imp.id, settings)


def test_recalculo_nao_sobrescreve_edicao_concorrente(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id, settings)
    lista = _receber(con, materia, settings, DISCIPLINA / "listas-2026-1/Lista3_2026-1.pdf")
    lida_antes = importacoes.obter(con, lista.id)  # leitura de um GET...
    editada = lida_antes.proposta
    editada["modo"] = "substituir"
    pipeline.editar(con, lista.id, editada)  # ...um PUT grava no meio...
    lida_antes.proposta["listas"][0]["unidade"]["numero"] = None  # ...e o GET tinha algo a recalcular
    pipeline.atualizar_derivados(con, lida_antes, settings)
    assert importacoes.obter(con, lista.id).proposta["modo"] == "substituir"


@pytest.mark.skipif(not STEWART.is_file(), reason="Stewart ausente")
def test_lista_por_secao_antes_do_livro_ganha_a_secao_depois(con, materia, settings):
    lista = _receber(con, materia, settings, DISCIPLINA / "exercicios_3un.pdf")
    pipeline.confirmar(con, materia.pasta, lista.id, settings)
    assert con.execute("SELECT count(*) FROM lista_secao").fetchone()[0] == 0
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, STEWART).id, settings)
    ligadas = con.execute(
        "SELECT l.codigo, s.codigo FROM lista_secao ls JOIN lista l ON l.id = ls.lista_id "
        "JOIN secao_livro s ON s.id = ls.secao_id ORDER BY ls.lista_id").fetchall()
    assert [tuple(r) for r in ligadas] == [(c, c) for c in ["15.4", "15.5", "15.7", "15.8", "15.9", "15.10"]]


def test_topico_repetido_entre_conteudos_vira_um_vinculo(con, materia, settings):
    pipeline.confirmar(con, materia.pasta, _receber(con, materia, settings, DISCIPLINA / "Programa.pdf").id, settings)
    lista = _receber(con, materia, settings, DISCIPLINA / "listas-2026-1/Lista3_2026-1.pdf")
    ids = [t["topico_id"] for t in lista.proposta["listas"][0]["topicos"]]
    assert ids and len(ids) == len(set(ids))
