from estudos.rag.corte import SecaoCorte, cortar_gabarito, cortar_livro

SECOES = [SecaoCorte(1, "10.3", "Coordenadas polares", 1, 2), SecaoCorte(2, "10.4", "Áreas em coordenadas polares", 2, 3)]
PAGINAS = [
    (1, "10.3 Coordenadas polares\nTeoria das polares, r e theta."),
    (2, "Exercícios\n10.3\n1. As Homeworks Hints estão disponíveis\n1. Esboce r = 2.\n2. Esboce a cardioide r = 1 + cos t, "
        "com bastante texto para passar de duzentos caracteres " + "x" * 200 + "\n"
        "10.4\nÁreas em coordenadas polares\nNesta seção deduziremos a fórmula da área."),
    (3, "Mais teoria da área.\nExercícios 10.4\n1. Calcule a área " + "y" * 220 + "\n25. termo solto\n2. Ache a área 2. de dentro " + "z" * 220),
]


def test_secao_comeca_no_titulo_e_sobra_vai_para_a_anterior():
    ts = cortar_livro(PAGINAS, SECOES, 1600)
    teoria_104 = [t for t in ts if t.secao_id == 2 and t.parte == "teoria"]
    assert teoria_104[0].texto.startswith("10.4") and "Nesta seção" in teoria_104[0].texto
    assert all("Esboce" not in t.texto for t in teoria_104)
    assert teoria_104[0].titulo == "10.4 Áreas em coordenadas polares"


def test_numeracao_reinicia_e_ignora_fora_de_sequencia():
    ts = cortar_livro(PAGINAS, SECOES, 1600)
    ex103 = [t for t in ts if t.secao_id == 1 and t.parte == "exercicio"]
    # "1. As Homeworks…" é prefixo; o "1." seguinte reinicia; o exercício 1 (< 200) se junta ao 2 e o trecho fica com 1
    assert [t.numero for t in ex103] == [1]
    assert "Homeworks" in ex103[0].texto and "Esboce r = 2" in ex103[0].texto and "cardioide" in ex103[0].texto
    ex104 = [t for t in ts if t.secao_id == 2 and t.parte == "exercicio"]
    assert [t.numero for t in ex104] == [1, 2]
    assert "25. termo solto" in ex104[0].texto and "2. de dentro" in ex104[1].texto   # longe do último não abre
    assert ex104[0].pagina == 3


def test_titulo_ausente_cai_para_a_pagina():
    secoes = [SecaoCorte(1, "10.3", "Coordenadas polares", 1, 1), SecaoCorte(2, "10.4", "Título que não está no texto", 2, 3)]
    ts = cortar_livro(PAGINAS, secoes, 1600)
    assert any(t.secao_id == 2 and t.pagina == 2 for t in ts)
    assert "".join(t.texto for t in ts).count("Mais teoria") == 1   # nada perdido nem repetido


def test_secao_sem_exercicios_e_toda_teoria():
    ts = cortar_livro([(1, "10.3 Coordenadas polares\nSó teoria aqui.\n1. Uma lista numerada da teoria.")],
                      [SecaoCorte(1, "10.3", "Coordenadas polares", 1, 1)], 1600)
    assert ts and all(t.parte == "teoria" and t.numero is None for t in ts)


def test_gabarito_liga_resposta_ao_exercicio():
    ts = cortar_gabarito([(9, "10.3\n1. r = 2 é um círculo\n3. cardioide\n10.4\n1. π/2")], {"10.3": 1, "10.4": 2}, 1600)
    assert [(t.secao_id, t.numero, t.parte) for t in ts] == [(1, 1, "resposta"), (1, 3, "resposta"), (2, 1, "resposta")]
    assert ts[0].titulo == "Respostas 10.3" and ts[0].pagina == 9


def test_gabarito_com_codigo_desconhecido():
    ts = cortar_gabarito([(9, "9.9\n1. nada\n10.4\n1. π/2")], {"10.4": 2}, 1600)   # 9.9 não cadastrada, na ordem do livro
    assert [(t.secao_id, t.numero) for t in ts] == [(2, 1)]


def test_formatos_do_stewart_codigo_antes_e_numero_sozinho():
    paginas = [(1, "14.2 Limites\nTeoria de limites.\n14.2 Exercícios\n1.\nCalcule o limite " + "a" * 210 + "\n2.\nMostre que não existe " + "b" * 210)]
    ts = cortar_livro(paginas, [SecaoCorte(7, "14.2", "Limites", 1, 1)], 1600)
    ex = [t for t in ts if t.parte == "exercicio"]
    assert [t.numero for t in ex] == [1, 2] and ex[1].texto.startswith("2.")
    assert not any("Exercícios" in t.texto for t in ts)


def test_paginas_entre_secoes_nao_cadastradas_ficam_fora():
    paginas = [(1, "10.4 Áreas\nteoria da área."), (2, "10.5 Cônicas\ntexto de seção não cadastrada."), (3, "14.1 Funções\nteoria de funções.")]
    ts = cortar_livro(paginas, [SecaoCorte(1, "10.4", "Áreas", 1, 1), SecaoCorte(2, "14.1", "Funções", 3, 3)], 1600)
    assert not any("não cadastrada" in t.texto for t in ts)
    assert {t.secao_id for t in ts} == {1, 2}


def test_gabarito_com_cabecalho_exercicios_maiusculo():
    ts = cortar_gabarito([(9, "EXERCÍCIOS 10.4\n1.\n(a) 100\n3. π/2\nEXERCÍCIOS 9.9\n1. fora")], {"10.4": 2}, 1600)
    assert [(t.secao_id, t.numero) for t in ts] == [(2, 1), (2, 3)] and "(a) 100" in ts[0].texto


def test_rodape_numerado_nao_reinicia_a_contagem():
    corpo = "\n".join(f"{n}. r = sen {n}θ " + "w" * 210 for n in (53, 54))
    paginas = [(1, "10.4 Áreas\nteoria.\n10.4 Exercícios\n" + "\n".join(f"{n}. item {n} " + "v" * 210 for n in range(1, 53))
                + "\n" + corpo + "\n1. AsHomework Hints estão disponíveis em www.stewartcalculus.com"),
               (2, "55. r = cos θ " + "k" * 210 + "\n56. r = 1 " + "q" * 210)]
    ts = cortar_livro(paginas, [SecaoCorte(1, "10.4", "Áreas", 1, 2)], 1600)
    numeros = [t.numero for t in ts if t.parte == "exercicio"]
    assert numeros[-2:] == [55, 56] and numeros.count(1) == 1


def _exercicios(ordem):
    corpo = "\n".join(f"{n}. exercício {n} " + "e" * 210 for n in ordem)
    ts = cortar_livro([(1, "14.7 Máximos\nteoria.\n14.7 Exercícios\n" + corpo)], [SecaoCorte(1, "14.7", "Máximos", 1, 1)], 1600)
    return [t.numero for t in ts if t.parte == "exercicio"]


def test_item_fora_de_ordem_nao_derruba_a_numeracao():
    # leitura com um item trocado (Stewart 14.7: "1, 4, 2, 3, 5…") e colunas fora de ordem (14.8: "22, 29, 31, 23, 25")
    assert _exercicios([1, 4, 2, 3, 5, 6, 7]) == [1, 4, 2, 3, 5, 6, 7]
    colunas = list(range(1, 23)) + [29, 31, 23, 25]
    assert _exercicios(colunas) == colunas


def test_numero_repetido_ou_longe_nao_abre_exercicio():
    assert _exercicios([1, 2, 3, 1, 40, 4]) == [1, 2, 3, 4]   # "1." repetido (sem 2 depois) e um salto de 40


def test_resposta_decimal_sozinha_nao_e_cabecalho_do_gabarito():
    # Stewart: "2.6" (uma resposta) sozinha na linha não fecha a seção 10.3; código de seção não cadastrada mais
    # adiante (10.5) fecha, para as respostas dela não irem para a anterior
    paginas = [(9, "10.3\n1.\n2.6\n3. x\n10.4\n1. y\n3.₂\n5. z\n10.5\n1. de seção não cadastrada\n14.1\n1. w\n0.2\n3. v")]
    ts = cortar_gabarito(paginas, {"10.3": 1, "10.4": 2, "14.1": 3}, 1600)
    assert [(t.secao_id, t.numero) for t in ts] == [(1, 1), (1, 3), (2, 1), (2, 5), (3, 1), (3, 3)]
    assert "2.6" in ts[0].texto
