"""Tabelas das fontes de matemática que guardam símbolos no lugar de letras (o PDF não traz a tradução).

Montadas desenhando cada glifo de cada fonte encontrada nos livros e slides do usuário e conferindo um a um; glifos
ambíguos ficaram de fora (passam como estão).

- `POR_NOME`: fontes MathematicalPi (Stewart). O código de cada glifo muda de um subconjunto para outro, mas o nome
  do glifo na lista /Differences da fonte não ("H11005" é sempre "="): a tradução de cada página sai dessa lista.
- `TABELAS` (por letra): fontes com codificação fixa — LTSGreek ("u" desenha θ), TECHMath (rótulos das figuras: o
  glifo "¨" desenha θ, "ƒ" desenha "f(x)"), MATH, e os pedaços de parênteses grandes do CMEX10/Symbol (saem).
"""

_PI = {
    "H33527": "=", "H11005": "=", "H11349": "=", "H11002": "−", "H11546": "−", "H11001": "+", "H11006": "±",
    "H11007": "∓", "H11003": "×", "H11080": "·", "H11554": "·", "H11015": "≈", "H11014": "≠", "HS33527": "≠",
    "H11021": "<", "H11022": ">", "H33355": "≤", "H11088": "≤", "H33356": "≥", "H11091": "≥", "H11350": "≥",
    "H11009": "∞", "H11557": "∞", "H11032": "′", "H11033": "″", "H11630": "‴", "H11635": "⁗", "H11034": "°",
    "H11568": "°", "H11128": "∂", "H11612": "∇", "H11938": "ℝ", "H5118": "ℛ", "H5129": "ℓ", "H5133": "ℓ",
    "H11028": "∠", "H11036": "⊥", "H20678": "∈", "H33528": "∈", "HS20678": "∉", "H20668": "∪", "H20669": "∩",
    "H20666": "⊂", "H20848": "∫", "H20858": "∑", "H20888": "∑", "H20881": "√", "H20857": "√", "H20648": "‖",
    "H11341": "|", "H20895": "|", "H20919": "|", "H20862": "/", "H11408": "/", "l": "→", "question": "⇒",
    "ampersand": "⇐",
    "H20849": "(", "H20873": "(", "H20898": "(", "H20850": ")", "H20874": ")", "H20899": ")", "H9012": ")",
    "H20851": "[", "H20875": "[", "H20864": "[", "H20915": "[", "H20852": "]", "H20876": "]", "H20865": "]",
    "H20916": "]", "H20853": "{", "H20877": "{", "H20854": "}", "H20878": "}", "H20855": "⟨", "H20883": "⟨",
    "H20908": "⟨", "H20856": "⟩", "H20884": "⟩", "H20909": "⟩",
    "H9251": "α", "H9252": "β", "H9253": "γ", "H9254": "δ", "H9004": "Δ", "H9255": "ε", "H9256": "ζ", "H9257": "η",
    "H9258": "θ", "H9260": "κ", "H9261": "λ", "H9262": "μ", "H9266": "π", "H9267": "ρ", "H9268": "σ", "H9270": "τ",
    "H9278": "φ", "H17034": "Φ", "H9275": "ω", "H9024": "Ω",
    "H5007": "",   # traço de fração (numerador e denominador já saem em linhas separadas)
}
_FAMILIAS_POR_NOME = ("MathematicalPi", "MathPi", "Universal")


def por_nome(familia: str) -> dict[str, str]:
    """Tabela por nome de glifo da família (vazia se a família não usa nomes próprios)."""
    return _PI if familia.startswith(_FAMILIAS_POR_NOME) else {}


_GREGO = {"u": "θ", "p": "π", "f": "φ", "a": "α", "l": "λ", "b": "β", "r": "ρ", "m": "μ", "d": "δ", "g": "γ",
          "c": "ψ", "k": "κ", "v": "ω", "s": "σ"}
_PEDACOS_DE_PARENTESES = {chr(c): "" for c in (0xF8E9, 0xF8EB, 0xF8ED, 0xF8EE, 0xF8EF, 0xF8F0, 0xF8F1, 0xF8F2, 0xF8F3,
                                                 0xF8F4, 0xF8F6, 0xF8F8, 0xF8F9, 0xF8FA, 0xF8FB)}

TABELAS: dict[str, dict[str, str]] = {
    "LTSGreek-Italic": {k: v for k, v in _GREGO.items() if k != "s"},
    "Greek-Italic": {k: _GREGO[k] for k in "abkmprsuv"},
    "TECHMath-Mix": {
        "_": "−", "¨": "θ", "œ": "√", "≈": "x²", "Î": "Δ", "”": "(", "’": ")", "{": "(", "}": ")", "ƒ": "f(x)",
        "ª": "′", "·": "″", "¥": "y²", "@": "²", "¸": "₀", "£": "₃", "å": "α", "˙": "φ", "⁄": "x₁", "¯": "≤",
        "∏": "ρ", "`": "∞", "Å": "≈", "∑": "ε", "˛": "x³", "©": "g(x)", "´": "eˣ", "˘": "≥", "›": "y₁", "±": "∇",
        "‹": "x₃", "∂": "δ", "ﬁ": "y₂", "μ": "∑", "¤": "x₂", "Œ": "∛", "ÿ": "ψ", "ç": "γ", "Á": "y³",
        "ﬂ": "f(x₁)", "‡": "f(x₂)",
    },
    "MATH": {"h": "∫", "j": "∫", "g": "∮", "k": "⟨", "l": "⟩", "m": "→", "e": "ε", "R": "ℝ", "T": "ℛ", "x": "×",
             "s": "{", "d": "}", "L": "ℓ", "a": "α", "!": "①", "@": "②", "#": "③", "$": "④", "%": "⑤", "^": "⑥",
             "&": "⑦", "*": "⑧"},
    "CMEX10": dict(_PEDACOS_DE_PARENTESES),
    "Symbol": dict(_PEDACOS_DE_PARENTESES),
    "EUEX10": dict(_PEDACOS_DE_PARENTESES),
}
