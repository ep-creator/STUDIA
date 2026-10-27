import math
import time

import pytest

from estudos.agente.calculadora import calcular


def test_integral_dupla_em_polares():
    # área do disco unitário: ∫₀^{2π} ∫₀^1 r dr dθ = π (limites de dentro para fora)
    r = calcular({"operacao": "integral", "expressao": "r", "variaveis": ["r", "theta"],
                  "limites": [["0", "1"], ["0", "2*pi"]]})
    assert r["resultado"] == "pi" and r["numerico"] == pytest.approx(math.pi)


def test_derivada_parcial():
    r = calcular({"operacao": "derivada", "expressao": "x^2*y + sin(y)", "variaveis": ["x", "y"], "ordem": ["x"]})
    assert r["resultado"] == "2*x*y"


def test_limite():
    assert calcular({"operacao": "limite", "expressao": "sin(x)/x", "variaveis": ["x"], "ponto": "0"})["resultado"] == "1"


def test_pontos_criticos_de_lagrange():
    # extremos de f = x*y em x² + y² = 2: ∇f = λ∇g e g = 0
    r = calcular({"operacao": "resolver", "expressoes": ["y = 2*l*x", "x = 2*l*y", "x^2 + y^2 = 2"],
                  "variaveis": ["x", "y", "l"]})
    for ponto in ("x: -1, y: -1", "x: 1, y: 1", "x: -1, y: 1", "x: 1, y: -1"):
        assert ponto in r["resultado"]


def test_pontos_criticos():
    r = calcular({"operacao": "pontos_criticos", "expressao": "x^2 + y^2 - 2*x", "variaveis": ["x", "y"]})
    assert "x: 1, y: 0" in r["resultado"]


def test_avaliar_numerico():
    assert calcular({"operacao": "avaliar", "expressao": "sqrt(2)*pi", "variaveis": []})["numerico"] == pytest.approx(
        math.sqrt(2) * math.pi)


@pytest.mark.parametrize("perigosa", [
    "__import__('os').system('echo x > sentinela.txt')", "().__class__", "open('sentinela.txt', 'w')",
    "x.real", "lambda: 1", "x" * 600, "exec(1)", "eval(x)",
])
def test_calculadora_recusa_entrada_perigosa(perigosa, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = calcular({"operacao": "avaliar", "expressao": perigosa, "variaveis": ["x"]})
    assert "erro" in r and not (tmp_path / "sentinela.txt").exists()


def test_operacao_desconhecida():
    assert "erro" in calcular({"operacao": "apagar", "expressao": "x", "variaveis": ["x"]})


def test_calculadora_tem_tempo_limite():
    inicio = time.perf_counter()
    r = calcular({"operacao": "integral", "expressao": "exp(sin(x)*x^3)*cos(x^5)", "variaveis": ["x"],
                  "limites": [["0", "1"]]})
    assert time.perf_counter() - inicio < 12
    assert r.get("numerico") is not None or "erro" in r
