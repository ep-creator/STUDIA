from estudos.conteudo import DocumentoMd, analisar_md, ler_md, serializar_md


def test_frontmatter_round_trip():
    doc = DocumentoMd(
        {"tipo": "resumo", "titulo": "Integrais: polares", "unidade": 3, "secao": None, "rotulo": "15", "vazio": ""},
        "# T\n\n$x^2$\n",
    )
    assert analisar_md(serializar_md(doc)) == doc


def test_sem_frontmatter():
    assert analisar_md("# Só corpo\n") == DocumentoMd({}, "# Só corpo\n")


def test_corpo_com_separador_no_meio():
    doc = DocumentoMd({"titulo": "x"}, "antes\n---\ndepois")
    assert analisar_md(serializar_md(doc)) == doc


def test_ler_md_de_arquivo(tmp_path):
    caminho = tmp_path / "a.md"
    caminho.write_text(serializar_md(DocumentoMd({"tipo": "resumo"}, "corpo")), encoding="utf-8")
    assert ler_md(caminho).meta == {"tipo": "resumo"}
