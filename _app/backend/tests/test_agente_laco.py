import dataclasses
import datetime

import pytest

from estudos.agente import conversas
from estudos.agente.ferramentas import Ambiente
from estudos.agente.laco import responder
from estudos.agente.modelo import Chamada, ErroModelo, ModeloFalso, Texto, Uso
from estudos.agente.papeis import carregar_papel
from estudos.config import Settings
from estudos.historico import desfazer_ultimo, operacao
from estudos.repos import documentos
from test_agente_contexto import questao_do_livro  # noqa: F401 (fixture)

HOJE = datetime.date(2026, 10, 27)


@pytest.fixture
def ajustes(tmp_path):
    return Settings(workspace=tmp_path, app_dir=tmp_path / "_app")


def _ambiente(con, materia, ajustes, alvo):
    return Ambiente(con, materia.pasta, ajustes, alvo, lambda descricao: operacao(con, descricao, materia.pasta))


def _rodar(con, materia, ajustes, alvo, papel, rodadas, texto="me ajude", confirmado=False):
    modelo = ModeloFalso(rodadas, nome="gemini-3.8-flash")
    saidas = list(responder(_ambiente(con, materia, ajustes, alvo), modelo, carregar_papel(papel), texto, confirmado,
                            materia.pasta.parent, HOJE))
    return saidas, modelo


def _tipos(saidas):
    return [s.tipo for s in saidas]


def test_resposta_simples_guarda_e_custa(con, materia, ajustes, questao_do_livro):
    alvo = f"questao:{questao_do_livro}"
    saidas, modelo = _rodar(con, materia, ajustes, alvo, "tutor", [[Texto("Use "), Texto("triplas."), Uso(1000, 500)]])
    assert _tipos(saidas) == ["texto", "texto", "fim"] and saidas[-1].dados["custo_brl"] > 0
    conversa = conversas.conversa_ativa(con, alvo, "tutor")
    assert [(m.autor, m.texto) for m in conversas.mensagens(con, conversa.id)] == [("voce", "me ajude"), ("agente", "Use triplas.")]
    sistema, _, ferramentas = modelo.pedidos[0]
    assert "[Lista 1.2 #1]" in sistema and "N4" in sistema
    assert "salvar_resolucao" in {f["name"] for f in ferramentas}


def test_historico_da_conversa_vai_para_o_modelo(con, materia, ajustes, questao_do_livro):
    alvo = f"questao:{questao_do_livro}"
    _rodar(con, materia, ajustes, alvo, "tutor", [[Texto("primeira")]], texto="pergunta 1")
    _, modelo = _rodar(con, materia, ajustes, alvo, "tutor", [[Texto("segunda")]], texto="pergunta 2")
    turnos = modelo.pedidos[0][1]
    assert [(t.autor, t.texto) for t in turnos] == [("usuario", "pergunta 1"), ("modelo", "primeira"), ("usuario", "pergunta 2")]


def test_ferramenta_de_busca_volta_para_o_modelo(con, materia, ajustes, questao_do_livro):
    saidas, modelo = _rodar(con, materia, ajustes, f"questao:{questao_do_livro}", "tutor",
                            [[Chamada("buscar", {"consulta": "integrais triplas"})], [Texto("achei")]])
    assert "ferramenta" in _tipos(saidas) and _tipos(saidas)[-1] == "fim"
    nome, resultado = modelo.pedidos[1][1][-1].resultados[0]
    assert nome == "buscar" and resultado["trechos"] and resultado["trechos"][0]["rotulo"].startswith("[")


def test_n4_grava_resolucao_pelo_historico_e_desfaz(con, materia, ajustes, questao_do_livro):
    saidas, _ = _rodar(con, materia, ajustes, f"questao:{questao_do_livro}", "tutor",
                       [[Chamada("salvar_resolucao", {"texto": "**Enunciado.** x\n\n**Resposta.** y"})], [Texto("Gravei.")]])
    [gravado] = [s.dados for s in saidas if s.tipo == "gravado"]
    doc = documentos.obter(con, gravado["id"])
    assert doc.tipo == "resolucao" and doc.questao_id == questao_do_livro and doc.origem == "agente"
    assert gravado["grupo_id"] and "Resposta." in documentos.ler_corpo(materia.pasta, doc)
    desfazer_ultimo(con, materia.pasta)
    assert con.execute("SELECT count(*) FROM documento WHERE id = ?", (gravado["id"],)).fetchone()[0] == 0


def test_salvar_resumo_e_formula(con, materia, ajustes, cenario_busca, questao_do_livro):
    existente = con.execute("SELECT id FROM documento WHERE tipo = 'resumo' AND secao_id = ?",
                            (cenario_busca["s12"],)).fetchone()["id"]
    saidas, _ = _rodar(con, materia, ajustes, f"secao:{cenario_busca['s12']}", "resumidor", [[
        Chamada("salvar_resumo", {"texto": "# 1.2 Integrais triplas\n\n## 1. Ideia\n\nNovo texto."}),
        Chamada("adicionar_formula", {"titulo": "Volume", "latex": "V = \\iiint_E dV", "quando": "volume de um sólido"}),
    ], [Texto("ok")]])
    assert len([s for s in saidas if s.tipo == "gravado"]) == 2
    doc = documentos.obter(con, existente)                  # o resumo da seção foi reescrito, não duplicado
    assert doc.origem == "agente" and "Novo texto." in documentos.ler_corpo(materia.pasta, doc)
    formula = con.execute("SELECT * FROM formula WHERE titulo = 'Volume'").fetchone()
    assert formula["secao_id"] == cenario_busca["s12"] and formula["origem"] == "agente"


def test_teto_pede_confirmacao(con, materia, ajustes, questao_do_livro):
    caro = dataclasses.replace(ajustes, teto_mensal_brl=0.0)
    saidas, modelo = _rodar(con, materia, caro, f"questao:{questao_do_livro}", "tutor", [[Texto("oi")]])
    assert _tipos(saidas) == ["confirmar"] and modelo.pedidos == []
    saidas, _ = _rodar(con, materia, caro, f"questao:{questao_do_livro}", "tutor", [[Texto("oi")]], confirmado=True)
    assert _tipos(saidas)[-1] == "fim"


def test_limite_de_rodadas(con, materia, ajustes, questao_do_livro):
    curto = dataclasses.replace(ajustes, max_rodadas=2)
    busca = [Chamada("buscar", {"consulta": "triplas"})]
    saidas, modelo = _rodar(con, materia, curto, f"questao:{questao_do_livro}", "tutor", [busca, busca, busca, busca])
    assert len(modelo.pedidos) == 3 and _tipos(saidas)[-1] == "fim"
    assert any("parei" in s.dados.get("texto", "").lower() for s in saidas if s.tipo == "texto")


def test_erro_de_ferramenta_vira_resultado(con, materia, ajustes, questao_do_livro):
    _, modelo = _rodar(con, materia, ajustes, f"questao:{questao_do_livro}", "tutor",
                       [[Chamada("exercicio_do_livro", {"secao": "9.9", "numero": 1})], [Texto("não achei")]])
    _, resultado = modelo.pedidos[1][1][-1].resultados[0]
    assert "erro" in resultado


def test_ferramenta_nao_permitida(con, materia, ajustes, questao_do_livro):
    _, modelo = _rodar(con, materia, ajustes, "geral", "estrategista",
                       [[Chamada("salvar_resolucao", {"texto": "x"})], [Texto("ok")]])
    _, resultado = modelo.pedidos[1][1][-1].resultados[0]
    assert "erro" in resultado and con.execute("SELECT count(*) FROM documento WHERE tipo = 'resolucao'").fetchone()[0] == 0


def test_erro_no_meio_guarda_o_parcial(con, materia, ajustes, questao_do_livro):
    alvo = f"questao:{questao_do_livro}"
    saidas, _ = _rodar(con, materia, ajustes, alvo, "tutor", [[Texto("Começando "), ErroModelo("indisponivel", "503")]])
    assert _tipos(saidas) == ["texto", "erro"] and saidas[-1].dados["motivo"] == "indisponivel"
    mensagens = conversas.mensagens(con, conversas.conversa_ativa(con, alvo, "tutor").id)
    assert mensagens[-1].autor == "agente" and mensagens[-1].texto == "Começando "
