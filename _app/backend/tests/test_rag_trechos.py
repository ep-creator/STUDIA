from estudos.rag.trechos import dividir_markdown, dividir_paginas


def test_paginas_pequenas_juntas():
    trechos = dividir_paginas([(10, "Primeiro parágrafo."), (11, "Segundo parágrafo.")], "15.4 Polares", limite=200)
    assert len(trechos) == 1
    t = trechos[0]
    assert (t.titulo, t.pagina, t.ordem) == ("15.4 Polares", 10, 1)
    assert "Primeiro parágrafo." in t.texto and "Segundo parágrafo." in t.texto


def test_limite_respeitado_sem_cortar_paragrafo():
    paginas = [(n, "\n\n".join(f"Parágrafo {n}.{i} " + "x" * 80 for i in range(5))) for n in range(1, 6)]
    trechos = dividir_paginas(paginas, "T", limite=300)
    assert all(len(t.texto) <= 300 for t in trechos)
    paragrafos = [p for _, texto in paginas for p in texto.split("\n\n")]
    assert all(any(p in t.texto for t in trechos) for p in paragrafos)
    assert [t.ordem for t in trechos] == list(range(1, len(trechos) + 1))


def test_pagina_do_trecho_e_a_primeira():
    paginas = [(n, "y" * 150) for n in (7, 8, 9)]
    trechos = dividir_paginas(paginas, "T", limite=200)
    assert [t.pagina for t in trechos] == [7, 8, 9]


def test_paragrafo_gigante_cortado_em_frase():
    texto = " ".join(f"Frase número {i} sobre integrais." for i in range(60))
    trechos = dividir_paginas([(1, texto)], "T", limite=300)
    assert len(trechos) > 1 and all(len(t.texto) <= 300 for t in trechos)
    assert all(t.texto.rstrip().endswith(".") for t in trechos[:-1])


def test_paginas_vazias():
    assert dividir_paginas([(1, ""), (2, "   \n ")], "T") == []


def test_markdown_por_secao():
    texto = "---\ntipo: resumo\n---\n# Polares\n\nIntro.\n\n## 1. Definição\n\nr e θ.\n\n## 2. Área\n\nfórmula."
    trechos = dividir_markdown(texto, "Polares")
    assert [t.titulo for t in trechos] == ["Polares", "Polares — 1. Definição", "Polares — 2. Área"]
    assert "tipo: resumo" not in "".join(t.texto for t in trechos)
    assert all(t.pagina is None for t in trechos)


def test_markdown_bloco_grande_dividido():
    texto = "## Longo\n\n" + "\n\n".join("z" * 100 for _ in range(10))
    trechos = dividir_markdown(texto, "Doc", limite=250)
    assert len(trechos) > 1 and all(t.titulo == "Doc — Longo" for t in trechos)
    assert all(len(t.texto) <= 250 for t in trechos)


def test_markdown_vazio():
    assert dividir_markdown("", "X") == []
