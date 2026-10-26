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
    assert linha.acerto5_exata == 1 and linha.acerto5_parafrase == 0.5
    assert linha.indexacao_s >= 0 and linha.p95_ms >= linha.p50_ms >= 0
    assert real.stat().st_mtime_ns == antes


def test_relatorio_grava_tabela_com_a_data(tmp_path):
    from estudos.avaliacao.busca import LinhaBusca
    linhas = [LinhaBusca("texto", 0.5, 1.0, 0.0, 0.4, 1.2, 3.0, 9.0, 12.5)]
    tabela = tabela_busca(linhas)
    assert "| texto |" in tabela and "50%" in tabela
    caminho = gravar(tabela, tmp_path, "busca", datetime.date(2026, 10, 26))
    assert caminho.name == "2026-10-26-busca.md" and "texto" in caminho.read_text(encoding="utf-8")
