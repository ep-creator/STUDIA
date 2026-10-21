from pathlib import Path

import pytest

from estudos.migracao.legado import ItemLegado, SecaoLegado, carregar
from estudos.migracao.regras import (
    fase_eh_cronograma,
    liberacao,
    mapa_secao_unidade,
    status_topico,
    tipo_documento_config,
    unidade_do_resumo,
    unificar_itens,
)

FIXTURE = Path(__file__).parent / "fixtures" / "legado_minimo"

# Mapa real de Cálculo 2 (exercicios.json: sec -> un)
MAPA_REAL = {
    **{f"14.{n}": 1 for n in range(1, 6)},
    **{s: 2 for s in ("14.6", "14.7", "14.8", "15.2", "15.3", "L3", "L4")},
    **{s: 3 for s in ("15.4", "15.5", "15.7", "15.8", "15.9", "15.10", "L5", "L6")},
}

# Cabeçalhos reais dos 12 resumos (H1 + linha de referência)
CABECALHOS_REAIS = [
    ("# Coordenadas polares\n\n> Stewart 10.3 e 10.4 · pré-requisito da 1ª unidade", 1),
    ("# 14.1 Funções de várias variáveis\n\n> Funções de várias variáveis reais a valores reais · Stewart 14.1 · Guidorizzi cap. 8", 1),
    ("# 14.2 Limite e continuidade\n\n> Stewart 14.2 · Guidorizzi cap. 9", 1),
    ("# 14.3 Derivadas parciais\n\n> Derivadas parciais e de ordens superiores · Stewart 14.3", 1),
    ("# 14.4 Plano tangente e diferencial\n\n> Diferenciabilidade · Stewart 14.4 · Guidorizzi 11.1–11.4", 1),
    ("# 14.5 Regra da cadeia e derivação implícita\n\n> Stewart 14.5 (e o início do 14.6)\n> **Aulas de 02/09 e 04/09** — é o que fecha o programa da 1ª unidade.", 1),
    ("# 14.6 Derivada direcional e vetor gradiente\n\n> Stewart 14.6 · Guidorizzi 11.5 e 13.1–13.4", 2),
    ("# 14.7 Valores máximo e mínimo\n\n> Pontos críticos · Stewart 14.7 · Guidorizzi 16.1–16.4", 2),
    ("# 14.8 Multiplicadores de Lagrange\n\n> Extremos condicionados · Stewart 14.8", 2),
    ("# 15.4 Integrais Duplas em Coordenadas Polares\n\n> Referência · 3ª unidade · Stewart 15.4 (com base em 10.3–10.4)", 3),
    ("# 15.5 Aplicações de Integrais Duplas\n\n> Densidade superficial, massa, centro de massa", 3),
    ("# 15.7 Integrais Triplas\n\n> Somas triplas de Riemann, Teorema de Fubini · 3ª unidade", 3),
]


@pytest.mark.parametrize("texto,esperado", CABECALHOS_REAIS)
def test_unidade_dos_resumos_reais(texto, esperado):
    assert unidade_do_resumo(texto, MAPA_REAL).valor == esperado


def test_marcador_tem_prioridade_sobre_secao():
    decisao = unidade_do_resumo("# 14.1 Funções\n\n> revisão para a 3ª unidade", MAPA_REAL)
    assert decisao.valor == 3 and "marcador" in decisao.regra


def test_secao_do_titulo_cita_a_regra():
    decisao = unidade_do_resumo("# 14.7 Máximos\n\ntexto", MAPA_REAL)
    assert decisao.valor == 2 and "14.7" in decisao.regra


def test_resumo_sem_regra():
    decisao = unidade_do_resumo("# Assunto livre\n\nsem seção", MAPA_REAL)
    assert decisao.valor is None and decisao.regra == "sem marcador nem seção conhecida"


def test_mapa_da_fixture():
    assert mapa_secao_unidade(carregar(FIXTURE)) == {"14.1": 1, "15.4": 3, "L5": 3}


@pytest.mark.parametrize("legado,novo", [("seen", "visto"), ("next", "proxima"), ("later", "pendente"), ("prova", None)])
def test_status_topico(legado, novo):
    assert status_topico(legado) == novo


def _fase(datas):
    return {"colunas": ["Sessão", "Data", "Foco"], "linhas": [{"s": str(i), "d": d, "t": "", "x": []} for i, d in enumerate(datas)]}


def test_fases_reais_da_unidade_3():
    assert fase_eh_cronograma(_fase(["dom 25/10", "ter 27/10", "qui 29/10", "sáb 31/10"]), 2026) is True
    assert fase_eh_cronograma(_fase(["Bloco 1", "Bloco 2", "Bloco 3"]), 2026) is False
    assert fase_eh_cronograma(_fase(["Prio 1", "Prio 2"]), 2026) is False
    assert fase_eh_cronograma(_fase([]), 2026) is False


@pytest.mark.parametrize("locked,aberta_auto,esperado", [
    (False, True, "auto"), (True, False, "auto"), (False, False, "aberta"), (True, True, "travada"),
])
def test_liberacao(locked, aberta_auto, esperado):
    assert liberacao(locked, aberta_auto) == esperado


def test_unificar_itens_repetidos():
    secao = SecaoLegado("14.7", 2, "Máximos", None, False, (
        ItemLegado("33", "A", None, None, 1), ItemLegado("35", "B", None, None, 1),
        ItemLegado("7", "C", None, None, 2), ItemLegado("33", "A", None, None, 2), ItemLegado("35", "B", None, None, 2),
    ))
    itens, avisos = unificar_itens(secao)
    assert [(i.numero, i.linha) for i in itens] == [("33", 1), ("35", 1), ("7", 2)]
    assert len(avisos) == 2 and "14.7 #33" in avisos[0]


def test_tipo_documento_config():
    assert tipo_documento_config("plano-estudos-unidade3.md") == "plano"
    assert tipo_documento_config("exercicios/stewart-un3.md") == "anotacao"
    assert tipo_documento_config("00-INDICE.md") == "anotacao"
