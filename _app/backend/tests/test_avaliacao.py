import datetime

import pytest

from estudos.avaliacao.busca import Configuracao, avaliar
from estudos.avaliacao.gabarito import PerguntaBusca, ler_busca
from estudos.avaliacao.metricas import acerto_em, mrr
from estudos.avaliacao.relatorio import gravar, tabela_busca
from estudos.rag.indice import caminho_indice


def test_acerto_e_mrr():
    assert acerto_em([1, 3, None, 6], k=5) == 0.5
    assert mrr([1, 2, None], k=10) == pytest.approx((1 + 0.5 + 0) / 3)
    assert mrr([11], k=10) == 0
    assert acerto_em([], k=5) == 0


def test_ler_busca_valida_estilo_e_aceitas(tmp_path):
    arq = tmp_path / "g.toml"
    arq.write_text('[[pergunta]]\ntexto = "x"\nestilo = "parafrase"\naceitas = ["secao:15.4"]\n', encoding="utf-8")
    [p] = ler_busca(arq)
    assert p.aceitas == ("secao:15.4",) and p.unidade is None and p.estilo == "parafrase"
    arq.write_text('[[pergunta]]\ntexto = "x"\nestilo = "outro"\naceitas = ["secao:1"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="pergunta 1"):
        ler_busca(arq)
    arq.write_text('[[pergunta]]\ntexto = "x"\nestilo = "exata"\naceitas = ["capitulo:1"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="pergunta 1"):
        ler_busca(arq)


def test_avaliar_usa_indice_temporario_e_nao_toca_o_real(con, materia, cenario_busca, tmp_path):
    real = caminho_indice(materia.pasta)
    antes = real.stat().st_mtime_ns
    perguntas = [
        PerguntaBusca("coordenadas polares", "exata", ("secao:1.1",), None),
        PerguntaBusca("cardioide em polares", "parafrase", ("documento:Polares",), None),
        PerguntaBusca("assunto que não existe", "parafrase", ("secao:9.9",), None),
    ]
    [linha] = avaliar(con, materia.pasta, perguntas, [Configuracao("texto", "texto", None)], tmp_path / "temp")
    assert linha.nome == "texto"
    assert linha.acerto5 == pytest.approx(2 / 3)
    assert linha.por_estilo == {"exata": 1.0, "parafrase": 0.5}
    assert linha.indexacao_s >= 0 and linha.p95_ms >= linha.p50_ms >= 0
    assert real.stat().st_mtime_ns == antes


def test_relatorio_grava_tabela_com_a_data(tmp_path):
    from estudos.avaliacao.busca import LinhaBusca
    linhas = [LinhaBusca("texto", 0.5, 0.4, {"exata": 1.0, "parafrase": 0.0}, {"claude": 0.5}, None, 0, 1.2, 3.0, 9.0, 12.5)]
    tabela = tabela_busca(linhas)
    assert "| texto |" in tabela and "50%" in tabela
    caminho = gravar(tabela, tmp_path, "busca", datetime.date(2026, 10, 26))
    assert caminho.name == "2026-10-26-busca.md" and "texto" in caminho.read_text(encoding="utf-8")


def test_ler_vinculos(tmp_path):
    from estudos.avaliacao.gabarito import ler_vinculos
    arq = tmp_path / "v.toml"
    arq.write_text(
        '[[topico]]\ntitulo = "Coordenadas polares"\nunidade = 1\nsecoes = ["10.3", "10.4"]\n'
        '[[topico]]\ntitulo = "Aula extra"\nunidade = 3\nsecoes = []\n'
        '[[lista]]\ntitulo = "Lista 5"\nunidade = 3\n'
        '[[documento]]\ntitulo = "Coordenadas polares"\nsecoes = ["10.3"]\n', encoding="utf-8")
    g = ler_vinculos(arq)
    assert g.topicos[0].secoes == ("10.3", "10.4") and g.topicos[1].secoes == ()
    assert g.listas[0].unidade == 3 and g.documentos[0].titulo == "Coordenadas polares"


def test_avaliar_vinculos_conta_acertos_erros_confiantes_e_revisao(con, materia, cenario_busca):
    # cenario_busca: livro principal com 1.1 "Coordenadas polares" e 1.2 "Integrais triplas"; tópico da unidade 3 ligado à 1.2
    from estudos.avaliacao.gabarito import GabaritoVinculos, ItemDocumento, ItemLista, ItemTopico
    from estudos.avaliacao.vinculos import ConfigVinculo, avaliar
    gabarito = GabaritoVinculos(
        topicos=(ItemTopico("Integrais triplas", 3, ("1.2",)),          # acerto
                 ItemTopico("Coordenadas polares", 1, ("1.2",)),        # escolhe 1.1 com confiança alta: erro confiante
                 ItemTopico("Séries de Fourier", 3, ())),               # nada parecido: acerto (não ligar)
        listas=(ItemLista("Integrais triplas em coordenadas cilíndricas", 3),),
        documentos=(ItemDocumento("Polares", ("1.1",)),),
    )
    linhas = {l.tipo: l for l in avaliar(con, gabarito, [ConfigVinculo("regra")], limiar_vinculo=0.35, limiar_gravar=0.75)}
    assert (linhas["topicos"].acertos, linhas["topicos"].total, linhas["topicos"].erros_confiantes) == (2, 3, 1)
    assert linhas["listas"].acertos == 1
    assert linhas["documentos"].total == 1
    assert linhas["total"].total == 5


def test_avaliar_modos_vetor_e_hibrida_com_provedor_injetado(con, materia, cenario_busca, tmp_path):
    from estudos.ia.embeddings import EmbeddingsFalso
    perguntas = [PerguntaBusca("coordenadas polares", "exata", ("secao:1.1",), None)]
    configs = [Configuracao("vetor:falso", "vetor", "falso"), Configuracao("hibrida:falso", "hibrida", "falso")]
    linhas = avaliar(con, materia.pasta, perguntas, configs, tmp_path / "t", provedores={"falso": EmbeddingsFalso()})
    assert [l.nome for l in linhas] == ["vetor:falso", "hibrida:falso"]
    assert all(l.acerto5 == 1 for l in linhas)


def test_configuracoes_do_mesmo_modelo_reaproveitam_o_indice(con, materia, cenario_busca, tmp_path, monkeypatch):
    from estudos.avaliacao import busca as modulo
    from estudos.ia.embeddings import EmbeddingsFalso
    chamadas = []
    original = modulo.sincronizar
    monkeypatch.setattr(modulo, "sincronizar", lambda *a, **k: chamadas.append(k.get("embeddings")) or original(*a, **k))
    perguntas = [PerguntaBusca("coordenadas polares", "exata", ("secao:1.1",), None)]
    configs = [Configuracao("vetor:f", "vetor", "f"), Configuracao("hibrida:f", "hibrida", "f"), Configuracao("texto", "texto", None)]
    linhas = avaliar(con, materia.pasta, perguntas, configs, tmp_path / "t", provedores={"f": EmbeddingsFalso()})
    assert len(chamadas) == 2                       # um índice para o modelo "f" e um só de texto
    assert linhas[0].indexacao_s == linhas[1].indexacao_s


def test_nomes_de_arquivo_por_materia_sem_acento(tmp_path):
    from estudos.avaliacao.__main__ import _arquivo_gabarito, _slug
    assert _slug("Geometria Analítica") == "geometriaanalitica" and _slug("Calculo 2") == "calculo2"
    assert _arquivo_gabarito("Geometria Analítica", "busca").name == "geometriaanalitica_busca.toml"
    a = gravar("x", tmp_path, "busca", datetime.date(2026, 10, 26), materia="Geometria Analítica")
    b = gravar("y", tmp_path, "busca", datetime.date(2026, 10, 26), materia="Calculo 2")
    assert a.name == "2026-10-26-geometriaanalitica-busca.md" and b.name == "2026-10-26-calculo2-busca.md"
    assert a.read_text(encoding="utf-8") == "x"


def test_ler_busca_aceita_questao_origem_e_fonte(tmp_path):
    arq = tmp_path / "g.toml"
    arq.write_text('[[pergunta]]\ntexto = "x"\nestilo = "questao"\norigem = "usuario"\naceitas = ["fonte:Aula 3#p5-7", "secao:1.1"]\n',
                   encoding="utf-8")
    [p] = ler_busca(arq)
    assert p.estilo == "questao" and p.origem == "usuario" and p.aceitas == ("fonte:Aula 3#p5-7", "secao:1.1")
    arq.write_text('[[pergunta]]\ntexto = "x"\nestilo = "exata"\norigem = "outra"\naceitas = ["secao:1"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="pergunta 1"):
        ler_busca(arq)


def test_avaliar_mede_por_origem_e_no_trecho(con, materia, cenario_busca, tmp_path):
    # a lista do cenário (fontes/listas/lista.pdf) tem "integral dupla em polares" na página 1 e "cardioide" na 2
    perguntas = [
        PerguntaBusca("cardioide", "exata", ("fonte:lista#p2",), None, "usuario"),        # arquivo e trecho certos
        PerguntaBusca("integral dupla em polares", "questao", ("fonte:lista#p3",), None, "gerada"),  # arquivo sim, página não
        PerguntaBusca("coordenadas polares", "exata", ("secao:1.1",), None, "claude"),     # sem trecho: fora da conta de trecho
    ]
    [linha] = avaliar(con, materia.pasta, perguntas, [Configuracao("texto", "texto", None)], tmp_path / "t")
    assert linha.por_origem == {"usuario": 1.0, "gerada": 1.0, "claude": 1.0}
    assert linha.n_trecho == 2 and linha.acerto5_trecho == 0.5


def test_ler_relacionados_do_mesmo_arquivo(tmp_path):
    from estudos.avaliacao.gabarito import ler_relacionados
    arq = tmp_path / "g.toml"
    arq.write_text('[[relacionado]]\nde = "documento:Polares"\nesperados = ["secao:1.1", "fonte:lista"]\n', encoding="utf-8")
    [r] = ler_relacionados(arq)
    assert r.de == "documento:Polares" and r.esperados == ("secao:1.1", "fonte:lista")
    arq.write_text('[[relacionado]]\nde = "capitulo:1"\nesperados = ["secao:1.1"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="relacionado 1"):
        ler_relacionados(arq)


def test_relacionados_conta_os_esperados_entre_os_10_primeiros(con, materia, cenario_busca, tmp_path):
    from estudos.avaliacao.gabarito import ItemRelacionado
    itens = [
        ItemRelacionado("documento:Polares", ("secao:1.1", "fonte:lista", "secao:9.9")),  # 9.9 não existe: no máximo 2/3
        ItemRelacionado("fonte:lista", ("documento:Polares",)),
    ]
    [linha] = avaliar(con, materia.pasta, [PerguntaBusca("polares", "exata", ("secao:1.1",), None)],
                      [Configuracao("texto", "texto", None)], tmp_path / "t", relacionados=itens)
    assert linha.n_relacionados == 2
    assert 0 < linha.relacionados <= (2 / 3 + 1) / 2
