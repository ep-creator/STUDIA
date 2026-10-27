import pytest

from estudos.historico import operacao
from estudos.rag import indexador
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice
from estudos.repos import documentos, fontes, livros
from pdfs_sinteticos import criar_pdf

PAGINAS_LIVRO = [
    "capa do livro de teste",
    "1.1 Coordenadas polares\nr e theta definem o ponto no plano.",
    "continuação de coordenadas polares com área de setores.",
    "1.2 Integrais triplas\nintegrais triplas em coordenadas cilíndricas.",
    "mais sobre integrais triplas e mudança de ordem.",
    "Exercícios 1.2\n1. exercícios de integrais triplas para resolver em casa.\n2. Mude a ordem de integração.",
    "Respostas dos exercícios ímpares\n1.1\n1. r = 2 é um círculo\n1.2\n1. resposta da integral tripla",
    "respostas continuação com valores numéricos",
]


@pytest.fixture
def base(con, materia):
    criar_pdf(materia.pasta / "fontes/livros/livro.pdf", PAGINAS_LIVRO)
    criar_pdf(materia.pasta / "fontes/listas/lista.pdf", ["Lista 1\n1. Calcule a integral dupla.", "2. Derive a função."])
    with operacao(con, "base", materia.pasta) as op:
        livro = fontes.registrar(op, "livro", "fontes/livros/livro.pdf")
        livros.criar(op, livro, "principal", gabarito_pdf_ini=7, gabarito_pdf_fim=8)
        livros.criar_secao(op, livro, "1", "Capítulo", 2, 6)
        livros.criar_secao(op, livro, "1.1", "Coordenadas polares", 2, 3)
        livros.criar_secao(op, livro, "1.2", "Integrais triplas", 4, 6)
        lista = fontes.registrar(op, "lista", "fontes/listas/lista.pdf")
        doc = documentos.salvar(op, "resumo", "polares", "Polares", "# Polares\n\n## Definição\n\nr e θ.\n\n## Área\n\nsetores.")
        documentos.salvar(op, "anotacao", "calendario", "Calendário", "Datas importantes.")
    return {"livro": livro, "lista": lista, "doc": doc}


def _trechos(materia, **filtro):
    indice = abrir_indice(materia.pasta)
    try:
        condicoes = " AND ".join(f"{k} = ?" for k in filtro) or "1 = 1"
        return [dict(r) for r in indice.execute(f"SELECT * FROM trecho WHERE {condicoes} ORDER BY id", list(filtro.values()))]
    finally:
        indice.close()


def test_primeira_sincronizacao_indexa_tudo(con, materia, base):
    r = sincronizar(con, materia.pasta)
    assert (r.indexadas, r.removidas) == (4, 0) and r.trechos > 0
    livro = _trechos(materia, fonte_id=base["livro"])
    secoes = {t["secao_id"] for t in livro if t["tipo"] == "livro"}
    codigos = {s.id: s.codigo for s in livros.listar_secoes(con, base["livro"])}
    assert {codigos[s] for s in secoes} == {"1.1", "1.2"}  # o capítulo não duplica o texto das subseções
    assert any(t["tipo"] == "gabarito" and t["pagina"] == 7 for t in livro)
    assert not any("capa do livro" in t["texto"] for t in livro)
    assert {t["tipo"] for t in _trechos(materia, fonte_id=base["lista"])} == {"lista"}
    resumo = _trechos(materia, documento_id=base["doc"])
    assert [t["titulo"] for t in resumo] == ["Polares", "Polares — Definição", "Polares — Área"]


def test_segunda_sincronizacao_nao_abre_pdf(con, materia, base, monkeypatch):
    sincronizar(con, materia.pasta)

    def proibido(*_a, **_k):
        raise AssertionError("não deveria abrir PDF")

    monkeypatch.setattr(indexador, "ler_paginas_limpas", proibido)
    r = sincronizar(con, materia.pasta)
    assert (r.indexadas, r.removidas) == (0, 0)


def test_documento_editado_e_reindexado(con, materia, base):
    sincronizar(con, materia.pasta)
    with operacao(con, "editar", materia.pasta) as op:
        documentos.salvar(op, "resumo", "polares", "Polares", "# Polares\n\nTexto novo sobre cardioides.")
    r = sincronizar(con, materia.pasta)
    assert r.indexadas == 1
    assert "cardioides" in _trechos(materia, documento_id=base["doc"])[0]["texto"]


def test_documento_apagado_some_do_indice(con, materia, base):
    sincronizar(con, materia.pasta)
    with operacao(con, "apagar", materia.pasta) as op:
        documentos.remover(op, base["doc"])
    r = sincronizar(con, materia.pasta)
    assert r.removidas == 1 and _trechos(materia, documento_id=base["doc"]) == []


def test_secoes_mudadas_reindexam_o_livro(con, materia, base):
    sincronizar(con, materia.pasta)
    with operacao(con, "nova seção", materia.pasta) as op:
        livros.criar_secao(op, base["livro"], "1.3", "Exercícios", 6, 6)
    assert sincronizar(con, materia.pasta).indexadas == 1


def test_livro_sem_secoes_por_pagina(con, materia):
    criar_pdf(materia.pasta / "fontes/livros/v1.pdf", ["página um do volume", "página dois do volume"])
    with operacao(con, "v1", materia.pasta) as op:
        f = fontes.registrar(op, "livro", "fontes/livros/v1.pdf")
        livros.criar(op, f, "complementar")
    sincronizar(con, materia.pasta)
    trechos = _trechos(materia, fonte_id=f)
    assert trechos and all(t["tipo"] == "livro" and t["secao_id"] is None for t in trechos)
    assert all(t["parte"] == "teoria" and t["numero"] is None for t in trechos)  # sem seções: igual a antes do corte


def test_livro_com_secoes_grava_partes(con, materia, base):
    sincronizar(con, materia.pasta)
    livro = _trechos(materia, fonte_id=base["livro"])
    codigos = {s.id: s.codigo for s in livros.listar_secoes(con, base["livro"])}
    assert {t["parte"] for t in livro} == {"teoria", "exercicio", "resposta"}
    [exercicio] = [t for t in livro if t["parte"] == "exercicio"]
    assert codigos[exercicio["secao_id"]] == "1.2" and exercicio["numero"] == 1 and exercicio["pagina"] == 6
    respostas = sorted((codigos[t["secao_id"]], t["numero"]) for t in livro if t["parte"] == "resposta")
    assert respostas == [("1.1", 1), ("1.2", 1)]
    assert all(t["tipo"] == "gabarito" for t in livro if t["parte"] == "resposta")


def test_gabarito_sem_formato_entra_como_antes(con, materia):
    criar_pdf(materia.pasta / "fontes/livros/g.pdf", ["capa", "1.1 Polares\nteoria", "Respostas sem código nenhum aqui"])
    with operacao(con, "g", materia.pasta) as op:
        f = fontes.registrar(op, "livro", "fontes/livros/g.pdf")
        livros.criar(op, f, "principal", gabarito_pdf_ini=3, gabarito_pdf_fim=3)
        livros.criar_secao(op, f, "1.1", "Polares", 2, 2)
    sincronizar(con, materia.pasta)
    gabarito = [t for t in _trechos(materia, fonte_id=f) if t["tipo"] == "gabarito"]
    assert gabarito and all(t["parte"] == "resposta" and t["numero"] is None for t in gabarito)


def test_pdf_sem_texto_vira_aviso(con, materia):
    criar_pdf(materia.pasta / "fontes/livros/escaneado.pdf", ["", "", ""])
    with operacao(con, "scan", materia.pasta) as op:
        f = fontes.registrar(op, "livro", "fontes/livros/escaneado.pdf")
        livros.criar(op, f, "complementar")
    r = sincronizar(con, materia.pasta)
    assert any("sem texto" in a for a in r.avisos) and _trechos(materia, fonte_id=f) == []
    assert sincronizar(con, materia.pasta).indexadas == 0  # não tenta de novo a cada sincronização


def test_arquivo_sumido_vira_aviso(con, materia, base):
    (materia.pasta / "fontes/listas/lista.pdf").unlink()
    r = sincronizar(con, materia.pasta)
    assert any("lista.pdf" in a for a in r.avisos) and _trechos(materia, fonte_id=base["lista"]) == []


def test_sincronizacoes_simultaneas_nao_quebram(con, materia, base):
    import threading

    from estudos.db.conexao import conectar

    erros = []

    def rodar():
        c = conectar(materia.db)
        try:
            sincronizar(c, materia.pasta)
        except Exception as e:  # pragma: no cover - só aparece se falhar
            erros.append(e)
        finally:
            c.close()

    threads = [threading.Thread(target=rodar) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert erros == []
    assert sincronizar(con, materia.pasta).indexadas == 0


def test_corrupcao_no_meio_do_indice_e_reconstruida(con, materia, base):
    from estudos.rag.indice import caminho_indice

    sincronizar(con, materia.pasta)
    caminho = caminho_indice(materia.pasta)
    dados = bytearray(caminho.read_bytes())
    for i in range(4096, len(dados) - 512):
        dados[i] = 0xAB
    caminho.write_bytes(bytes(dados))
    r = sincronizar(con, materia.pasta)
    assert r.indexadas == 4 and any("reconstruído" in a for a in r.avisos)


def test_livro_sem_secoes_usa_o_nome_do_arquivo(con, materia):
    criar_pdf(materia.pasta / "fontes/livros/Stewart vol 1.pdf", ["página um do volume", "página dois do volume"])
    with operacao(con, "v1", materia.pasta) as op:
        f = fontes.registrar(op, "livro", "fontes/livros/Stewart vol 1.pdf")
        livros.criar(op, f, "complementar")
    sincronizar(con, materia.pasta)
    assert {t["titulo"] for t in _trechos(materia, fonte_id=f)} == {"Stewart vol 1"}


def test_indexador_avisa_simbolos_sem_traducao(con, materia, base, monkeypatch):
    original = indexador.ler_paginas_limpas
    monkeypatch.setattr(indexador, "ler_paginas_limpas", lambda caminho: (original(caminho)[0], 3))
    r = sincronizar(con, materia.pasta)
    assert any("3 símbolos sem tradução" in a for a in r.avisos)


def test_paginas_so_do_capitulo_continuam_no_indice(con, materia):
    # Guidorizzi cap. 16: o capítulo tem páginas próprias antes da única subseção cadastrada (16.5)
    criar_pdf(materia.pasta / "fontes/livros/c.pdf", ["capa", "16 Máximos e mínimos\ntexto próprio do capítulo",
                                                     "mais texto do capítulo 16", "16.5 Lagrange\nmultiplicadores"])
    with operacao(con, "c", materia.pasta) as op:
        f = fontes.registrar(op, "livro", "fontes/livros/c.pdf")
        livros.criar(op, f, "principal")
        cap = livros.criar_secao(op, f, "16", "Máximos e mínimos", 2, 4, nivel=1)
        sub = livros.criar_secao(op, f, "16.5", "Lagrange", 4, 4, nivel=2)
    sincronizar(con, materia.pasta)
    trechos = _trechos(materia, fonte_id=f)
    texto_cap = " ".join(t["texto"] for t in trechos if t["secao_id"] == cap)
    assert "texto próprio do capítulo" in texto_cap and "mais texto do capítulo 16" in texto_cap
    assert any("multiplicadores" in t["texto"] for t in trechos if t["secao_id"] == sub)
    assert not any("multiplicadores" in t["texto"] for t in trechos if t["secao_id"] == cap)   # sem repetir a subseção
