import pytest

from estudos.importacao.vinculo import Candidato, construir_idf, melhores, similaridade, unidade_majoritaria

STEWART = [
    "14.1 Funções de Várias Variáveis", "14.2 Limites e Continuidade", "14.3 Derivadas Parciais",
    "14.4 Planos Tangentes e Aproximações Lineares", "14.5 A Regra da Cadeia", "14.6 Derivadas Direcionais e o Vetor Gradiente",
    "14.7 Valores Máximo e Mínimo", "14.8 Multiplicadores de Lagrange", "15.4 Integrais Duplas em Coordenadas Polares",
    "15.7 Integrais Triplas", "15.8 Integrais Triplas em Coordenadas Cilíndricas", "15.9 Integrais Triplas em Coordenadas Esféricas",
    "15.10 Mudança de Variáveis em Integrais Múltiplas",
]
CANDIDATOS = [Candidato(t.split()[0], t) for t in STEWART]


def test_identicos_a_menos_do_codigo():
    idf = construir_idf(STEWART)
    assert similaridade("Integrais triplas em coordenadas cilíndricas", STEWART[10], idf) == pytest.approx(1.0)


def test_topico_do_programa_acha_a_secao():
    [v] = melhores("Integrais triplas em coordenadas cilíndricas", CANDIDATOS, 0.35)
    assert v.chave == "15.8" and v.confianca > 0.8
    assert melhores("Multiplicadores de Lagrange", CANDIDATOS, 0.35)[0].chave == "14.8"
    assert melhores("Plano tangente a um gráfico", CANDIDATOS, 0.35)[0].chave == "14.4"


def test_sem_candidato_acima_do_limiar():
    assert melhores("Gráficos", CANDIDATOS, 0.35) == []


def test_singular_e_plural_casam():
    topicos = [Candidato(1, "Integrais duplas em coordenadas polares"), Candidato(2, "Integrais triplas em caixas")]
    assert melhores("Integral dupla em coordenadas polares", topicos, 0.35)[0].chave == 1


def test_empate_reduz_confianca():
    empatados = [Candidato("a", "Integrais triplas"), Candidato("b", "Integrais triplas")]
    v = melhores("Integrais triplas", empatados, 0.35)[0]
    assert v.confianca == pytest.approx(0.5)


def test_maximo_de_resultados():
    assert len(melhores("Integrais triplas em coordenadas", CANDIDATOS, 0.1, maximo=3)) == 3


def test_unidade_majoritaria():
    assert unidade_majoritaria([3, 3, 2]) == (3, pytest.approx(2 / 3))
    assert unidade_majoritaria([]) == (None, 0.0)
