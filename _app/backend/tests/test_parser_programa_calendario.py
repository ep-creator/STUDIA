import pytest

from estudos.importacao.parsers.calendario import extrair_calendario
from estudos.importacao.parsers.programa import extrair_programa
from estudos.importacao.pdf import abrir_pdf
from pdfs_sinteticos import DISCIPLINA


def _texto(nome):
    caminho = DISCIPLINA / nome
    if not caminho.is_file():
        pytest.skip("arquivo real ausente")
    return abrir_pdf(caminho).texto()


def test_programa_real():
    unidades = extrair_programa(_texto("Programa.pdf"))
    assert [(u.numero, u.titulo) for u in unidades] == [
        (1, "Primeira Unidade"), (2, "Segunda Unidade"), (3, "Terceira Unidade")]
    u1 = unidades[0]
    assert [t.titulo for t in u1.topicos] == ["Funções de várias variáveis a valores reais", "Diferenciabilidade"]
    assert [f.titulo for f in u1.topicos[0].filhos] == [
        "Gráficos", "Coordenadas polares", "Limite", "Continuidade", "Derivadas parciais", "Derivadas de ordens superiores"]
    assert len(u1.topicos[1].filhos) == 4
    u3 = unidades[2]
    assert u3.topicos[0].titulo == "Integrais duplas em coordenadas polares" and u3.topicos[0].filhos == []
    assert len(u3.topicos[1].filhos) == 9
    assert "Integrais duplas em domínios mais gerais" in [f.titulo for t in unidades[1].topicos for f in t.filhos]


def test_programa_variacoes():
    texto = "Ementa\nUnidade II\n○ Séries\n• Convergência\nabsoluta e condicional\n1ª Unidade\n• Limites"
    unidades = extrair_programa(texto)
    assert [(u.numero, u.titulo) for u in unidades] == [(2, "Unidade II"), (1, "1ª Unidade")]
    assert unidades[0].topicos[0].filhos[0].titulo == "Convergência absoluta e condicional"
    assert unidades[1].topicos[0].titulo == "Limites"  # subtópico sem pai vira tópico


def test_calendario_real():
    cal = extrair_calendario(_texto("Calendario.pdf"))
    assert cal.ano == 2026 and [u.numero for u in cal.unidades] == [1, 2, 3]
    u1 = cal.unidades[0]
    assert len(u1.aulas) == 9 and u1.aulas[0].data == "2026-08-12" and u1.aulas[0].tipo == "aula"
    extra = u1.aulas[-1]
    assert (extra.tipo, extra.data, extra.hora_inicio, extra.hora_fim) == ("extra", "2026-09-12", "10:00", "12:00")
    assert "sábado" in extra.descricao
    p = u1.prova
    assert (p.tipo, p.data, p.hora_inicio, p.hora_fim) == ("prova", "2026-09-14", "14:30", "17:00")
    assert cal.unidades[1].aulas[-1].hora_inicio == "08:00" and cal.unidades[2].prova.data == "2026-11-30"
    assert [(e.tipo, e.data) for e in cal.eventos] == [("segunda_chamada", "2026-12-09"), ("exame_final", "2026-12-14")]


def test_calendario_sem_ano_usa_padrao_e_vira_o_ano():
    cal = extrair_calendario("Primeira Unidade\n10/11\n15/12\n02/02\nPrimeira prova: 10/02", ano_padrao=2026)
    assert [a.data for a in cal.unidades[0].aulas] == ["2026-11-10", "2026-12-15", "2027-02-02"]
    assert cal.unidades[0].prova.data == "2027-02-10" and cal.unidades[0].prova.hora_inicio is None


def test_calendario_sem_ano_nenhum():
    cal = extrair_calendario("Unidade 1\n10/11")
    assert cal.ano is None and cal.unidades[0].aulas == []
