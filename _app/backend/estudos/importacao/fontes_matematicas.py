"""Tabelas das fontes de matemática que guardam símbolos no lugar de letras (o PDF não traz a tradução).

Nome da fonte (sem o prefixo de subconjunto "ABCDEF+") → caractere que o PDF entrega → texto Unicode. Montadas
desenhando cada caractere de cada fonte encontrada nos livros e conferindo um a um.
"""

TABELAS: dict[str, dict[str, str]] = {}
