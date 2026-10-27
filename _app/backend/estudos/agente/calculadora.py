"""Calculadora segura do assistente: o modelo manda a conta, o app calcula com SymPy/SciPy. Nenhum código do modelo é
executado.

Antes de qualquer análise, cada texto passa por uma lista branca (caracteres, nomes de funções conhecidos e as
variáveis do pedido); só então vira expressão SymPy com um dicionário de nomes restrito. O cálculo roda num processo
separado com tempo limite; integral que não fecha de forma simbólica cai para a integração numérica.
"""

import builtins
import keyword
import multiprocessing
import re
from typing import Any

FUNCOES = {"sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "ln", "sqrt", "pi", "E",
           "oo", "Abs"}
OPERACOES = {"integral", "derivada", "limite", "resolver", "pontos_criticos", "avaliar"}
_MAX_CARACTERES = 500
_CARACTERES = re.compile(r"^[0-9A-Za-z +\-*/^().,=]*$")
_PONTO_EM_NOME = re.compile(r"[A-Za-z]\.|\.[A-Za-z]")   # x.real, ().__class__: acesso a atributo
_NOME = re.compile(r"[A-Za-z][A-Za-z0-9]*")
# Variável: uma letra (com até 2 dígitos: x, y1) ou o nome de uma letra grega. Nada de nomes livres: o SymPy avalia
# a expressão como Python, e uma "variável" chamada eval, chr ou for viraria código.
_VARIAVEL = re.compile(r"^[A-Za-z][0-9]{0,2}$")
_GREGAS = {"alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "kappa", "lam", "mu", "nu", "xi",
           "rho", "sigma", "tau", "phi", "chi", "psi", "omega"}
_PROIBIDOS = set(keyword.kwlist) | set(keyword.softkwlist) | set(dir(builtins)) | {"Integer", "Float", "Rational", "Symbol"}
_TEMPO_SIMBOLICO_S = 5
_TEMPO_NUMERICO_S = 5


class EntradaInvalida(ValueError):
    pass


def _conferir(texto: Any, variaveis: list[str]) -> str:
    if not isinstance(texto, str) or not texto.strip():
        raise EntradaInvalida("expressão vazia")
    if len(texto) > _MAX_CARACTERES:
        raise EntradaInvalida("expressão longa demais")
    if not _CARACTERES.match(texto) or _PONTO_EM_NOME.search(texto):
        raise EntradaInvalida("expressão inválida: só números, variáveis, operadores e funções matemáticas")
    for nome in _NOME.findall(texto):
        if nome in _PROIBIDOS:
            raise EntradaInvalida(f"nome não permitido: {nome}")
        if nome not in FUNCOES and nome not in variaveis:
            raise EntradaInvalida(f"nome desconhecido: {nome}")
    return texto


def _validar(pedido: dict) -> dict:
    """Pedido só com textos conferidos (levanta EntradaInvalida)."""
    if not isinstance(pedido, dict) or pedido.get("operacao") not in OPERACOES:
        raise EntradaInvalida(f"operação deve ser uma de: {', '.join(sorted(OPERACOES))}")
    variaveis = pedido.get("variaveis") or []
    if not isinstance(variaveis, list) or len(variaveis) > 6 or not all(
            isinstance(v, str) and (_VARIAVEL.match(v) or v in _GREGAS) and v not in FUNCOES and v not in _PROIBIDOS
            for v in variaveis):
        raise EntradaInvalida("variáveis devem ser uma letra (x, y1) ou o nome de uma letra grega (theta, phi)")
    limpo: dict = {"operacao": pedido["operacao"], "variaveis": variaveis}
    if pedido["operacao"] == "resolver":
        expressoes = pedido.get("expressoes") or []
        if not isinstance(expressoes, list) or not expressoes or len(expressoes) > 10:
            raise EntradaInvalida("resolver pede de 1 a 10 expressões")
        limpo["expressoes"] = [_conferir(e, variaveis) for e in expressoes]
    else:
        limpo["expressao"] = _conferir(pedido.get("expressao"), variaveis)
    if "=" in limpo.get("expressao", ""):
        raise EntradaInvalida("'=' só em resolver")
    if pedido["operacao"] == "integral":
        limites = pedido.get("limites") or []
        if len(limites) != len(variaveis) or not all(isinstance(l, list) and len(l) == 2 for l in limites):
            raise EntradaInvalida("integral pede um par de limites por variável, de dentro para fora")
        limpo["limites"] = [[_conferir(a, variaveis), _conferir(b, variaveis)] for a, b in limites]
    if pedido["operacao"] == "limite":
        limpo["ponto"] = _conferir(pedido.get("ponto"), variaveis)
    if pedido["operacao"] == "derivada":
        ordem = pedido.get("ordem") or variaveis[:1]
        if not all(o in variaveis for o in ordem):
            raise EntradaInvalida("a ordem da derivada usa as variáveis do pedido")
        limpo["ordem"] = ordem
    return limpo


# ---- dentro do processo separado -----------------------------------------------------------------------------------

def _analisar(texto: str, variaveis: list[str]):
    import sympy
    from sympy.parsing.sympy_parser import convert_xor, parse_expr, standard_transformations

    nomes = {n: getattr(sympy, n) for n in ("Integer", "Float", "Rational", "Symbol")}
    nomes |= {n: getattr(sympy, n) for n in FUNCOES - {"ln"}}
    nomes["ln"] = sympy.log
    nomes["__builtins__"] = {}   # sem isso o eval do SymPy injeta os builtins do Python
    simbolos = {v: sympy.Symbol(v, real=True) for v in variaveis}
    if "=" in texto:
        esquerda, direita = texto.split("=", 1)
        texto = f"({esquerda}) - ({direita})"
    return parse_expr(texto, local_dict=simbolos, global_dict=nomes, transformations=standard_transformations + (convert_xor,))


def _numero(expr) -> float | None:
    try:
        return float(expr.evalf()) if expr.is_number else None
    except (TypeError, ValueError):
        return None


def _solucoes(solucoes, variaveis, extra=None) -> str:
    partes = []
    for s in solucoes:
        texto = ", ".join(f"{v}: {s[k]}" for v in variaveis for k in s if str(k) == v)
        if extra is not None:
            texto += f" ({extra(s)})"
        partes.append(texto)
    return "; ".join(partes) or "nenhuma solução"


def _simbolico(pedido: dict) -> dict:
    import sympy

    vs = pedido["variaveis"]
    simb = {v: sympy.Symbol(v, real=True) for v in vs}
    op = pedido["operacao"]
    if op == "resolver":
        exprs = [_analisar(e, vs) for e in pedido["expressoes"]]
        sol = sympy.solve(exprs, [simb[v] for v in vs], dict=True)
        return {"resultado": _solucoes(sol, vs), "numerico": None}
    f = _analisar(pedido["expressao"], vs)
    if op == "avaliar":
        r = sympy.simplify(f)
    elif op == "derivada":
        r = sympy.diff(f, *[simb[v] for v in pedido["ordem"]])
    elif op == "limite":
        r = sympy.limit(f, simb[vs[0]], _analisar(pedido["ponto"], vs))
    elif op == "pontos_criticos":
        sol = sympy.solve([sympy.diff(f, simb[v]) for v in vs], [simb[v] for v in vs], dict=True)
        return {"resultado": _solucoes(sol, vs, lambda s: f"f = {sympy.simplify(f.subs(s))}"), "numerico": None}
    else:  # integral, de dentro para fora
        r = f
        for v, (a, b) in zip(vs, pedido["limites"]):
            r = sympy.integrate(r, (simb[v], _analisar(a, vs), _analisar(b, vs)))
        if r.has(sympy.Integral):
            return {"sem_forma_fechada": True}
    r = sympy.simplify(r)
    return {"resultado": sympy.sstr(r), "numerico": _numero(r)}


def _numerico(pedido: dict) -> dict:
    import sympy
    from scipy import integrate

    vs = pedido["variaveis"]
    simb = [sympy.Symbol(v, real=True) for v in vs]
    f = sympy.lambdify(simb, _analisar(pedido["expressao"], vs), "math")
    faixas = []
    for i, (a, b) in enumerate(pedido["limites"]):
        externas = simb[i + 1:]   # os limites de uma variável podem depender das variáveis de fora
        la = sympy.lambdify(externas, _analisar(a, vs), "math")
        lb = sympy.lambdify(externas, _analisar(b, vs), "math")
        faixas.append(lambda *fora, la=la, lb=lb: (float(la(*fora)), float(lb(*fora))))
    valor, erro = integrate.nquad(f, faixas)
    return {"resultado": f"≈ {valor:.10g} (integração numérica, erro estimado {erro:.1g})", "numerico": valor}


def _trabalho(fase: str, pedido: dict, fila) -> None:
    try:
        fila.put(_simbolico(pedido) if fase == "simbolico" else _numerico(pedido))
    except Exception as e:  # conta impossível, divisão por zero…: vira resposta de erro para o modelo
        fila.put({"erro": f"não consegui calcular: {type(e).__name__}: {e}"[:300]})


def _em_processo(fase: str, pedido: dict, tempo_s: int) -> dict | None:
    contexto = multiprocessing.get_context("spawn")
    fila = contexto.Queue()
    processo = contexto.Process(target=_trabalho, args=(fase, pedido, fila), daemon=True)
    processo.start()
    processo.join(tempo_s)
    if processo.is_alive():
        processo.terminate()
        processo.join()
        return None
    return fila.get() if not fila.empty() else {"erro": "o cálculo terminou sem resposta"}


def calcular(pedido: dict) -> dict:
    """Pedido → {"resultado", "numerico"} ou {"erro"}; nunca executa código vindo do pedido."""
    try:
        limpo = _validar(pedido)
    except EntradaInvalida as e:
        return {"erro": str(e)}
    resposta = _em_processo("simbolico", limpo, _TEMPO_SIMBOLICO_S)
    if limpo["operacao"] == "integral" and (resposta is None or resposta.get("sem_forma_fechada")):
        resposta = _em_processo("numerico", limpo, _TEMPO_NUMERICO_S)
    if resposta is None:
        return {"erro": "a conta demorou demais; tente simplificar ou dividir em partes"}
    return resposta
