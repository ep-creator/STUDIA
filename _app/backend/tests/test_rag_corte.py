from estudos.rag.corte import SecaoCorte, cortar_gabarito, cortar_livro

SECOES = [SecaoCorte(1, "10.3", "Coordenadas polares", 1, 2), SecaoCorte(2, "10.4", "Áreas em coordenadas polares", 2, 3)]
PAGINAS = [
    (1, "10.3 Coordenadas polares\nTeoria das polares, r e theta."),
    (2, "Exercícios\n10.3\n1. As Homeworks Hints estão disponíveis\n1. Esboce r = 2.\n2. Esboce a cardioide r = 1 + cos t, "
        "com bastante texto para passar de duzentos caracteres " + "x" * 200 + "\n"
        "10.4\nÁreas em coordenadas polares\nNesta seção deduziremos a fórmula da área."),
    (3, "Mais teoria da área.\nExercícios 10.4\n1. Calcule a área " + "y" * 220 + "\n5. termo solto\n2. Ache a área 2. de dentro " + "z" * 220),
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
    assert "5. termo solto" in ex104[0].texto and "2. de dentro" in ex104[1].texto   # fora de sequência não abre
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
    ts = cortar_gabarito([(9, "99.9\n1. nada\n10.4\n1. π/2")], {"10.4": 2}, 1600)
    assert [(t.secao_id, t.numero) for t in ts] == [(2, 1)]
