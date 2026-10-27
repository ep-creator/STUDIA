"""Leitura do PDF por fonte e posição (só o índice usa).

As páginas sintéticas reproduzem os casos achados nos livros e slides reais. As amostras reais (pedaços salvos com
`python -m estudos.avaliacao.amostras`) ficam só no computador do usuário, em tests/fixtures/paginas/ (fora do Git:
são texto de livros e slides de terceiros); sem a pasta, esses testes são pulados.
"""

import json
import re
from pathlib import Path

import pytest

from estudos.importacao import pdf
from estudos.importacao.fontes_matematicas import TABELAS
from estudos.importacao.pdf import ler_paginas_limpas, montar_texto, remover_repetidos
from pdfs_sinteticos import criar_pdf

LARGURA, ALTURA = 600, 800


def s(texto, x0, y0, x1, y1, fonte="Times-Roman", tamanho=10):
    return {"font": fonte, "size": tamanho, "bbox": [x0, y0, x1, y1], "text": texto}


def linhas(spans, tabelas=None):
    texto, _ = montar_texto(spans, LARGURA, ALTURA, tabelas or {})
    return texto.split("\n")


def coluna(x0, x1, y_ini, n, prefixo):
    return [s(f"{prefixo} linha {i} do texto corrido", x0, y_ini + 14 * i, x1, y_ini + 14 * i + 10) for i in range(n)]


# ---- páginas sintéticas ------------------------------------------------------------------------------------------

def test_formula_no_meio_da_frase_volta_para_o_lugar():
    frase = "a norma de um vetor  do   é definida por"   # o PDF deixa espaços onde a fórmula entra
    # 8,125 por letra: "vetor" acaba em 254, " do " vai de 271 a 287 e o resto recomeça em 311
    spans = [s(frase, 100, 100, 425, 112), s("u", 258, 99, 266, 113, "STIXGeneral-Italic", 10.2),
             s("ℝ", 290, 99, 299, 112, "STIXGeneral-Regular"), s("n", 299, 97, 305, 105, "STIXGeneral-Italic", 6.5)]
    assert linhas(spans) == ["a norma de um vetor u do ℝⁿ é definida por"]


def test_glifo_entra_antes_da_pontuacao():
    spans = [s("de geradores para , isto é, ", 100, 100, 340, 112), s("W", 222, 99, 232, 113, "STIXGeneral-Italic")]
    assert linhas(spans) == ["de geradores para W , isto é,"]


def test_expoente_e_indice():
    spans = [s("seja ", 100, 100, 130, 112), s("λ", 130, 100, 137, 112, "STIXGeneral-Italic"),
             s("2", 137, 97, 141, 105, "STIXGeneral-Regular", 6.5), s(" e ", 141, 100, 155, 112),
             s("v", 155, 100, 161, 112, "STIXGeneral-Bold"), s("k", 161, 106, 165, 115, "STIXGeneral-Italic", 6.5)]
    assert linhas(spans) == ["seja λ² e vₖ"]


def test_duas_colunas_saem_uma_depois_da_outra():
    spans = coluna(40, 280, 100, 6, "esquerda") + coluna(320, 560, 100, 6, "direita")
    saida = linhas(spans)
    assert saida == [f"esquerda linha {i} do texto corrido" for i in range(6)] + \
                    [f"direita linha {i} do texto corrido" for i in range(6)]


def test_margem_vai_depois_do_texto_e_o_titulo_fica_no_texto():
    # título maior que passa por cima da margem; parágrafos separados por vãos onde a margem não tem nada (sem a regra
    # do título, a página seria cortada em faixas e cada rótulo da margem cairia no meio do texto)
    titulo = s("Áreas e Comprimentos", 60, 60, 400, 76, "Univers-CondensedBold", 14)
    texto = [s(f"parágrafo {p} linha {i} do texto corrido", 150, y + 14 * i, 560, y + 14 * i + 10)
             for p, y in enumerate((100, 150, 200)) for i in range(2)]
    margem = [s("FIGURA 1", 20, 102, 90, 110, "Univers", 7), s("θ = b", 30, 202, 70, 210, "Univers", 7)]
    saida = linhas([titulo, *margem, *texto])
    assert saida[0] == "Áreas e Comprimentos" and saida[1] == "parágrafo 0 linha 0 do texto corrido"
    assert saida[-2:] == ["FIGURA 1", "θ = b"]


def test_icone_no_vao_nao_junta_as_colunas():
    spans = coluna(40, 290, 100, 12, "esquerda") + coluna(302, 560, 100, 12, "direita")   # vão de 12
    spans.append(s(";", 293, 156, 299, 166, "BeaconDingbats"))   # ícone da calculadora no meio do vão
    saida = linhas(spans)
    assert saida.index("direita linha 0 do texto corrido") > saida.index("esquerda linha 11 do texto corrido")


def test_cabecalho_e_numero_da_pagina_ficam_nas_bordas_e_saem_por_repeticao():
    paginas = []
    for n in range(5):
        spans = [s(f"{602 + 2 * n} CÁLCULO", 40, 20, 140, 30), *coluna(40, 560, 100, 4, f"página {n}"),
                 s(str(n + 1), 295, 775, 305, 785)]
        texto, _ = montar_texto(spans, LARGURA, ALTURA, {})
        assert texto.split("\n")[0].endswith("CÁLCULO") and texto.split("\n")[-1] == str(n + 1)
        paginas.append(texto)
    assert not any("CÁLCULO" in p for p in remover_repetidos(paginas))


def test_uso_privado_sai_e_e_contado():
    texto, sem_traducao = montar_texto([s("x = y\x03", 100, 100, 200, 112)], LARGURA, ALTURA, {})
    assert texto == "x = y" and sem_traducao == 2


def test_tabela_da_fonte_traduz_sem_o_prefixo_de_subconjunto():
    spans = [s("o raio e ", 100, 100, 150, 112), s("u", 150, 100, 156, 112, "ABCDEF+LTSGreek-Italic")]
    assert linhas(spans, {"LTSGreek-Italic": {"u": "θ"}}) == ["o raio e θ"]
    assert linhas(spans) == ["o raio e u"]   # fonte sem tabela: passa como está


def test_pagina_com_erro_usa_a_leitura_atual(tmp_path, monkeypatch):
    caminho = criar_pdf(tmp_path / "a.pdf", ["primeira página de texto", "segunda página de texto"])
    original = pdf.montar_texto
    chamadas = []

    def falha_na_primeira(*args):
        chamadas.append(1)
        if len(chamadas) == 1:
            raise ValueError("estrutura estranha")
        return original(*args)

    monkeypatch.setattr(pdf, "montar_texto", falha_na_primeira)
    paginas, _ = ler_paginas_limpas(caminho, {})
    assert "primeira página de texto" in paginas[0].texto and "segunda página de texto" in paginas[1].texto


# ---- amostras reais (só locais) ----------------------------------------------------------------------------------

AMOSTRAS = Path(__file__).parent / "fixtures" / "paginas"
ESPERADOS = sorted((AMOSTRAS / "esperado").glob("*.txt")) if AMOSTRAS.is_dir() else []
reais = pytest.mark.skipif(not ESPERADOS, reason="amostras reais só existem no computador do usuário")


def _amostra(nome: str) -> str:
    d = json.loads((AMOSTRAS / f"{nome}.json").read_text(encoding="utf-8"))
    return montar_texto(d["spans"], d["largura"], d["altura"], d.get("tabelas", TABELAS))[0]


def _sem_espaco(t: str) -> str:
    return re.sub(r"\s+", "", t)


@reais
@pytest.mark.parametrize("esperado", ESPERADOS, ids=lambda p: p.stem)
def test_amostra_real_sai_na_ordem_de_leitura(esperado):
    texto = _sem_espaco(_amostra(esperado.stem))
    pos = 0
    for linha in esperado.read_text(encoding="utf-8").splitlines():
        if not linha.strip() or (linha.startswith("§ ") and not TABELAS):  # "§": precisa das tabelas das fontes
            continue
        trecho = _sem_espaco(linha.removeprefix("§ "))
        achado = texto.find(trecho, pos)
        assert achado >= 0, f"{esperado.stem}: não achei (na ordem) {linha!r}"
        pos = achado + len(trecho)


@reais
def test_amostras_reais_sem_uso_privado():
    for json_ in AMOSTRAS.glob("*.json"):
        assert not re.search(r"[-]", _amostra(json_.stem)), json_.stem


@reais
def test_coluna_de_margem_separada():
    texto = _amostra("st-113")
    assert texto.index("FIGURA 2") > texto.index("Dessa forma, a Fórmula 4 fornece")


@reais
def test_cabecalho_fora():
    nomes = ["st-113", "st-116", "st-303", "st-342", "st-631"]
    limpas = dict(zip(nomes, remover_repetidos([_amostra(n) for n in nomes])))
    assert not any(l.endswith("CÁLCULO") for n in ("st-113", "st-303") for l in limpas[n].split("\n"))


# ---- tabelas das fontes (Task 6) ---------------------------------------------------------------------------------

def test_traducao_pela_lista_de_glifos_da_pagina():
    # MathematicalPi: o código muda de um PDF para outro, o nome do glifo (H11005 = "=") não
    from estudos.importacao.pdf import traducao_por_nomes
    assert traducao_por_nomes({2: "H11005", 3: "H11002", 4: "Hdesconhecido"}, "MathematicalPi-One") == {"\x02": "=", "\x03": "−"}
    assert traducao_por_nomes({2: "H11005"}, "Times-Roman") == {}


def test_tabelas_por_letra_das_fontes_gregas():
    assert TABELAS["LTSGreek-Italic"]["u"] == "θ" and TABELAS["LTSGreek-Italic"]["p"] == "π"
    assert TABELAS["TECHMath-Mix"]["¨"] == "θ" and TABELAS["MATH"]["h"] == "∫"


@reais
def test_simbolos_traduzidos_na_pagina_do_stewart():
    texto = _amostra("st-113")
    assert "θ" in texto and "π" in texto and " u, a medida" not in texto


def test_espaco_largo_do_stewart_depois_da_virgula():
    # a Times-Roman do Stewart desenha "M" em branco como espaço largo nas fórmulas, num pedaço separado da vírgula
    spans = [s("r = sen 2,", 100, 100, 160, 112), s("Mr = cos 2", 160, 100, 220, 112)]
    assert linhas(spans) == ["r = sen 2, r = cos 2"]


def test_m_de_verdade_depois_da_virgula_fica():
    assert linhas([s("os pontos (A,M,B) e o ponto M", 100, 100, 300, 112, "BodoniSvtyTwoITCTT-Book")]) ==         ["os pontos (A,M,B) e o ponto M"]
    assert linhas([s("(A,", 100, 100, 120, 112, "STIXGeneral-Italic"), s("M,B)", 120, 100, 150, 112, "STIXGeneral-Italic")]) ==         ["(A,M,B)"]


def test_leitura_limpa_nao_pede_as_imagens(tmp_path, monkeypatch):
    # em PDF escaneado o modo "dict" com imagens custa ~70x mais (devolve os bytes de cada imagem) e elas não são usadas
    import pymupdf
    caminho = criar_pdf(tmp_path / "a.pdf", ["texto da página"])
    pedidos = []
    original = pymupdf.Page.get_text

    def espiao(self, opcao="text", *args, **kwargs):
        if opcao == "dict":
            pedidos.append(kwargs.get("flags"))
        return original(self, opcao, *args, **kwargs)

    monkeypatch.setattr(pymupdf.Page, "get_text", espiao)
    ler_paginas_limpas(caminho, {})
    assert pedidos and all(f is not None and not f & pymupdf.TEXT_PRESERVE_IMAGES for f in pedidos)


def test_pagina_densa_e_rapida():
    # página de exercícios do Stewart: ~3 mil pedaços pequenos; a montagem não pode ser quadrática
    import time
    spans = [s(f"p{i}", x0 + 14 * (i % 16), 20 + 9 * (i // 16) % 760, x0 + 14 * (i % 16) + 12, 28 + 9 * (i // 16) % 760, tamanho=7)
             for x0 in (30, 320) for i in range(1500)]
    inicio = time.perf_counter()
    montar_texto(spans, LARGURA, ALTURA, {})
    assert time.perf_counter() - inicio < 1.0
