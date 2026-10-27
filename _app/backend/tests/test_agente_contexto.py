import re

import pytest

from estudos.agente.contexto import contexto_em_texto, montar_contexto
from estudos.agente.papeis import ATALHOS, carregar_papel
from estudos.historico import operacao
from estudos.modelos import QuestaoEntrada
from estudos.rag.indexador import sincronizar
from estudos.repos import documentos, eventos, listas, marcacoes


@pytest.fixture
def questao_do_livro(con, materia, cenario_busca):
    # lista "1.2" ligada à seção 1.2 do livro do cenário (que tem "Exercícios 1.2" e gabarito "1.2 / 1.")
    with operacao(con, "lista", materia.pasta) as op:
        lid = listas.criar(op, "1.2", "Lista 1.2", cenario_busca["u1"])
        listas.vincular_secao(op, lid, cenario_busca["s12"])
        listas.sincronizar_questoes(op, lid, [QuestaoEntrada("1", enunciado_md="Calcule a integral tripla em casa.")])
        documentos.salvar(op, "resumo", "triplas", "1.2 Integrais triplas", "# Triplas\n\nTeoria das triplas.",
                          secao_id=cenario_busca["s12"])
    sincronizar(con, materia.pasta)
    [q] = listas.listar_questoes(con, lid)
    return q.id


def _rotulos(pedacos):
    return [p.rotulo for p in pedacos]


def test_contexto_de_questao(con, materia, cenario_busca, questao_do_livro):
    pedacos = montar_contexto(con, materia.pasta, f"questao:{questao_do_livro}", "tutor")
    rotulos = _rotulos(pedacos)
    assert rotulos[0] == "[Lista 1.2 #1]" and "Calcule a integral tripla" in pedacos[0].texto
    livro = next(p for p in pedacos if "exercício 1" in p.rotulo)
    assert "resolver em casa" in livro.texto and "resposta da integral tripla" in livro.texto
    teoria = [p for p in pedacos if re.fullmatch(r"\[livro p\. \d+\]", p.rotulo)]
    assert teoria and any("integrais triplas" in p.texto for p in teoria)
    assert "[resumo 1.2 Integrais triplas]" in rotulos
    texto = contexto_em_texto(pedacos)
    assert "[Lista 1.2 #1]" in texto and "Teoria das triplas" in texto


def test_contexto_de_secao(con, materia, cenario_busca, questao_do_livro):
    pedacos = montar_contexto(con, materia.pasta, f"secao:{cenario_busca['s12']}", "resumidor")
    juntos = " ".join(p.texto for p in pedacos)
    assert "integrais triplas em coordenadas cilíndricas" in juntos
    assert "resolver em casa" not in juntos          # só a teoria da seção, sem os exercícios
    assert "[resumo 1.2 Integrais triplas]" in _rotulos(pedacos)   # o resumo atual, para reescrever


def test_contexto_geral_traz_marcacoes_e_prova(con, materia, cenario_busca, questao_do_livro):
    with operacao(con, "marcar", materia.pasta) as op:
        marcacoes.definir(op, questao_do_livro, "err")
        eventos.criar(op, "prova", "2099-12-01", unidade_id=cenario_busca["u1"], descricao="Prova 1")
    juntos = contexto_em_texto(montar_contexto(con, materia.pasta, "geral", "estrategista"))
    assert "Lista 1.2 #1" in juntos and "errei" in juntos and "2099-12-01" in juntos


def test_contexto_de_questao_sem_livro(con, materia):
    from estudos.repos import unidades
    with operacao(con, "base", materia.pasta) as op:
        u = unidades.criar(op, 1)
        lid = listas.criar(op, "L1", "Lista 1", u)
        listas.sincronizar_questoes(op, lid, [QuestaoEntrada("3", enunciado_md="Derive f(x) = x².")])
    [q] = listas.listar_questoes(con, lid)
    pedacos = montar_contexto(con, materia.pasta, f"questao:{q.id}", "tutor")
    assert _rotulos(pedacos)[0] == "[Lista L1 #3]" and "Derive" in pedacos[0].texto


def test_alvo_invalido():
    with pytest.raises(ValueError):
        montar_contexto(None, None, "documento:1", "tutor")


def test_papeis_carregam_ferramentas_e_instrucoes():
    tutor, resumidor, estrategista = (carregar_papel(n) for n in ("tutor", "resumidor", "estrategista"))
    assert {"buscar", "calcular", "salvar_resolucao", "exercicio_do_livro"} <= set(tutor.ferramentas)
    assert {"salvar_resumo", "adicionar_formula", "ler_secao"} <= set(resumidor.ferramentas)
    assert not {"salvar_resolucao", "salvar_resumo", "adicionar_formula"} & set(estrategista.ferramentas)
    assert "N4" in tutor.instrucoes and tutor.instrucoes.strip()
    assert set(ATALHOS) == {"N1", "N2", "N3", "N4", "resumir", "plano"}
