import pytest

from estudos.importacao.parsers.lista import extrair_listas
from estudos.importacao.pdf import abrir_pdf
from pdfs_sinteticos import DISCIPLINA, criar_pdf


def _arquivo(rel):
    caminho = DISCIPLINA / rel
    if not caminho.is_file():
        pytest.skip("arquivo real ausente")
    return extrair_listas(abrir_pdf(caminho), caminho.name)


def test_lista_por_secao_real():
    a = _arquivo("exercicios_3un.pdf")
    assert (a.formato, a.unidade, a.titulo) == ("por_secao", 3, "Exercícios da terceira unidade")
    assert a.referencia_livro == "J. Stewart, Cálculo, V.II, sétima edição"
    assert [l.codigo for l in a.listas] == ["15.4", "15.5", "15.7", "15.8", "15.9", "15.10"]
    l154 = a.listas[0]
    assert (l154.titulo, l154.secao_livro) == ("Seção 15.4", "15.4")
    assert [q.rotulo for q in l154.questoes if q.linha == 1] == ["7", "8", "11", "17", "21", "22", "25", "29"]
    assert [q.rotulo for q in l154.questoes if q.linha == 2] == ["9", "13", "19", "30", "38"]
    assert "38(a)" in [q.rotulo for q in a.listas[4].questoes]
    assert "20(primeira parte)" in [q.rotulo for q in a.listas[5].questoes]


def test_lista_por_secao_rotulo_composto():
    a = _arquivo("exercicios_1un.pdf")
    assert a.unidade == 1 and "101(b)(c)(d)" in [q.rotulo for q in a.listas[2].questoes]


def test_lista_numerada_real():
    a = _arquivo("listas-2026-1/Lista5_2026-1.pdf")
    assert (a.formato, a.unidade) == ("numerada", None)
    [lista] = a.listas
    assert lista.codigo == "L5" and lista.titulo.startswith("Quinta Lista de Exercícios")
    assert [q.rotulo for q in lista.questoes] == [str(n) for n in range(1, 16)]
    assert a.conteudos == ["Coordenadas polares", "Integral dupla em coordenadas polares", "Mudança de varíaveis"]
    q5 = lista.questoes[4]
    assert q5.enunciado_md.startswith("Calcule a área da região") and q5.pagina_pdf is not None
    assert "a. r = cos(3θ)" in lista.questoes[3].enunciado_md


@pytest.mark.parametrize("n", range(1, 7))
def test_todas_as_listas_ufpe_numeradas_sem_buracos(n):
    a = _arquivo(f"listas-2026-1/Lista{n}_2026-1.pdf")
    rotulos = [int(q.rotulo) for q in a.listas[0].questoes]
    assert a.listas[0].codigo == f"L{n}" and rotulos == list(range(1, len(rotulos) + 1)) and len(rotulos) >= 5


def test_repetido_nas_duas_linhas(tmp_path):
    texto = "Exercícios da segunda unidade\n•\nSeção 14.7\no 5,33,35\no 7,33"
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "e.pdf", [texto])), "e.pdf")
    assert [(q.rotulo, q.linha) for q in a.listas[0].questoes] == [("5", 1), ("33", 1), ("35", 1), ("7", 2)]
    assert any("14.7 #33" in aviso for aviso in a.avisos)


def test_codigo_pelo_nome_do_arquivo(tmp_path):
    texto = "Exercícios de revisão\n1. Calcule.\n2. Derive.\n3. Integre."
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "Lista 9 - revisão.pdf", [texto])), "Lista 9 - revisão.pdf")
    assert a.listas[0].codigo == "L9" and len(a.listas[0].questoes) == 3


def test_numeracao_fora_de_sequencia_e_ignorada(tmp_path):
    texto = "Lista de exercícios\n1. Primeira.\nvalor 3. não é questão\n2. Segunda.\n5. pulo\n3. Terceira."
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "x.pdf", [texto])), "x.pdf")
    q = a.listas[0].questoes
    assert [x.rotulo for x in q] == ["1", "2", "3"] and "5. pulo" in q[1].enunciado_md


@pytest.mark.parametrize("n", [3, 6])
def test_conteudos_que_quebram_linha(n):
    a = _arquivo(f"listas-2026-1/Lista{n}_2026-1.pdf")
    assert len(a.conteudos) >= 2 and not any(c.split()[-1] in ("e", "em", "de") for c in a.conteudos)


def test_questao_n_e_parenteses_e_reinicio(tmp_path):
    texto = "Lista de exercícios\nQuestão 1. Calcule.\nQuestão 2) Derive.\n3) Integre.\nParte B\n1. Outra"
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "q.pdf", [texto])), "q.pdf")
    assert [q.rotulo for q in a.listas[0].questoes] == ["1", "2", "3"]
    assert any("reinicia" in aviso for aviso in a.avisos)


def test_conteudos_param_no_cabecalho_seguinte(tmp_path):
    texto = ("Lista de exercícios\nConteúdos: Funções de duas variáveis, Limite e continuidade\n"
             "Equipe de professores responsáveis:\nProf. Fulano (f@x.br)\n1. Calcule.")
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "c.pdf", [texto])), "c.pdf")
    assert a.conteudos == ["Funções de duas variáveis", "Limite e continuidade"]


def test_expoente_quebrado_nao_vira_questao(tmp_path):
    texto = ("Lista de exercícios\n1. Considere o gráfico z = k(1-x2-y2)\n1\n2. Desenhe-o nos casos k = 0.\n"
             "2.\nPara cada função, desenhe curvas de nível.\n3. Determine o domínio.")
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "e.pdf", [texto])), "e.pdf")
    q = a.listas[0].questoes
    assert [x.rotulo for x in q] == ["1", "2", "3"]
    assert "Desenhe-o" in q[0].enunciado_md and q[1].enunciado_md.startswith("Para cada função")
    assert any("número repetido" in aviso for aviso in a.avisos)


def test_numero_repetido_sem_numero_solto_nao_mexe(tmp_path):
    texto = "Lista de exercícios\n1. Primeira.\n2. Segunda, com itens:\n2. item que repete\n3. Terceira."
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "r.pdf", [texto])), "r.pdf")
    q = a.listas[0].questoes
    assert [x.rotulo for x in q] == ["1", "2", "3"] and "item que repete" in q[1].enunciado_md


def test_lista1_real_conteudos_e_questoes():
    a = _arquivo("listas-2026-1/Lista1_2026-1.pdf")
    assert a.conteudos == ["Funções de duas variáveis", "Limite e continuidade"]
    q = a.listas[0].questoes
    assert "Desenhe-o" in q[0].enunciado_md and q[1].enunciado_md.startswith("Para cada uma das funções")


def test_numero_de_pagina_e_gabarito_nao_disparam_a_regra(tmp_path):
    paginas = ["Lista de exercícios\n1. Calcule a primeira.\n2. Calcule a segunda.\n1",
               "3. Calcule a terceira integral.\n2", "Respostas\n1. 4\n2. 7\n3. 12"]
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "g.pdf", paginas)), "g.pdf")
    q = a.listas[0].questoes
    assert [x.rotulo for x in q] == ["1", "2", "3"]
    assert q[2].enunciado_md.startswith("Calcule a terceira integral") and "Calcule a terceira" not in q[1].enunciado_md
    assert not any("número repetido" in aviso for aviso in a.avisos)


def test_conteudo_com_dois_pontos_no_meio_continua(tmp_path):
    texto = "Lista de exercícios\nConteúdos: Integrais duplas, mudança de\nvariáveis: polares e cilíndricas.\n1. Calcule."
    a = extrair_listas(abrir_pdf(criar_pdf(tmp_path / "d.pdf", [texto])), "d.pdf")
    assert a.conteudos == ["Integrais duplas", "mudança de variáveis: polares e cilíndricas"]
