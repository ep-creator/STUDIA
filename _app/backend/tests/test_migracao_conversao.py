import pytest

from estudos.migracao.conversao import (
    data_curta_para_iso,
    html_para_md,
    nota_de_tags,
    periodo_e_instituicao,
    referencias_exercicios,
    tabela_markdown,
)


def test_html_negrito_com_simbolos():
    md, avisos = html_para_md("Máximo <b>absolutos</b> em <b>D = {(x, y) : x² + y² ≤ 1}</b> — fronteira")
    assert md == "Máximo **absolutos** em **D = {(x, y) : x² + y² ≤ 1}** — fronteira" and avisos == []


def test_html_subscrito_vira_tex():
    assert html_para_md("isto é, f<sub>xy</sub> = f<sub>yx</sub>.")[0] == "isto é, $f_{xy}$ = $f_{yx}$."


def test_html_italico_strong_br_small():
    md, avisos = html_para_md("<i>Dica:</i> <strong>ordem</strong><br>linha <small>nota</small>")
    assert md == "*Dica:* **ordem**\nlinha — nota" and avisos == []


def test_html_tag_desconhecida_mantem_texto_e_avisa():
    md, avisos = html_para_md('<span class="x">texto</span> fim')
    assert md == "texto fim" and avisos == ["tag <span> removida"]


def test_caracteres_especiais_intactos():
    texto = "∬_D x²y dA · θ ⭐ — ≤ ∛ ação"
    assert html_para_md(texto) == (texto, [])


@pytest.mark.parametrize("texto,esperado", [
    ("seg 31/08", "2026-08-31"),
    ("Qua 04/11", "2026-11-04"),
    ("sáb 05/09", "2026-09-05"),
    ("30/11", "2026-11-30"),
    ("06 e 11/11", None),
    ("Bloco 1", None),
    ("Prio 1", None),
    ("31/02", None),
])
def test_data_curta(texto, esperado):
    assert data_curta_para_iso(texto, 2026) == esperado


@pytest.mark.parametrize("texto,esperado", [
    ("14.6: 4, 8, 12", [("14.6", "4"), ("14.6", "8"), ("14.6", "12")]),
    ("L5 #1, #2, ⭐#4", [("L5", "1"), ("L5", "2"), ("L5", "4")]),
    ("68 (pendente) + 20, 26", []),
    ("15.4: 11, 29 | L5 #6(a), #7", [("15.4", "11"), ("15.4", "29"), ("L5", "6(a)"), ("L5", "7")]),
    ("15.4, 15.5", []),
    ("—", []),
])
def test_referencias(texto, esperado):
    assert referencias_exercicios(texto) == esperado


def test_nota_de_tags():
    assert nota_de_tags(["Prova feita em 14/09", "Nota: 8,0"]) == 8.0
    assert nota_de_tags(["Nota: 7.5"]) == 7.5
    assert nota_de_tags(["Nota ainda não saiu"]) is None


def test_periodo_e_instituicao():
    assert periodo_e_instituicao("UFPE · 2026.2") == ("2026.2", "UFPE")
    assert periodo_e_instituicao("2026.2") == ("2026.2", None)
    assert periodo_e_instituicao("") == (None, None)


def test_tabela_markdown_escapa_barra():
    tabela = tabela_markdown(["A", "B"], [["1", "x | y"]])
    assert tabela == "| A | B |\n|---|---|\n| 1 | x \\| y |"


def test_html_subscrito_apos_simbolo():
    md, avisos = html_para_md("Expresse ∭<sub>E</sub> f(x, y, z) dV")
    assert md == "Expresse $∭_{E}$ f(x, y, z) dV" and avisos == []


def test_html_span_mono_vira_codigo():
    md, avisos = html_para_md('retas <span class="mono">y = mx</span> → parábolas <span class="mono">y = mx²</span>')
    assert md == "retas `y = mx` → parábolas `y = mx²`" and avisos == []
