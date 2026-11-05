"""Progresso derivado e a tela Hoje: regras explícitas a partir do plano, das marcações e das resoluções gravadas."""

from datetime import date
from types import SimpleNamespace

import pytest

from estudos import progresso
from estudos.historico import operacao
from estudos.modelos import QuestaoEntrada
from estudos.repos import cronograma, documentos, eventos, fontes, formulas, listas, livros, marcacoes, topicos, unidades

HOJE = date(2099, 3, 10)


@pytest.fixture
def plano(con, materia):
    """1ª unidade com prova em 5 dias (reta final); 2ª unidade com um erro para revisar."""
    pdf = materia.pasta / "fontes" / "livros" / "stewart.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(b"%PDF-1.4 livro")
    with operacao(con, "plano", materia.pasta) as op:
        u1 = unidades.criar(op, 1, "Primeira")
        u2 = unidades.criar(op, 2, "Segunda")
        eventos.criar(op, "prova", "2099-03-15", unidade_id=u1)
        eventos.criar(op, "prova", "2099-04-20", unidade_id=u2)
        eventos.criar(op, "aula", "2099-03-11", unidade_id=u1, descricao="Aula de aplicações")
        livro = fontes.registrar(op, "livro", "fontes/livros/stewart.pdf", "Stewart")
        livros.criar(op, livro, "principal", titulo_obra="Stewart")
        s154 = livros.criar_secao(op, livro, "15.4", "Polares", 431, 440)
        s155 = livros.criar_secao(op, livro, "15.5", "Aplicações", 441, 450)

        polares = topicos.criar(op, u1, "Integrais em polares")
        aplicacoes = topicos.criar(op, u1, "Aplicações")
        extra = topicos.criar(op, u1, "Aula extra")
        livros.vincular_topico(op, polares, s154, confianca=1.0, confirmado=True)
        livros.vincular_topico(op, aplicacoes, s155, confianca=1.0, confirmado=True)

        l154 = listas.criar(op, "15.4", "Integrais em polares", u1)
        listas.vincular_secao(op, l154, s154)
        q154 = listas.sincronizar_questoes(op, l154, [QuestaoEntrada(r) for r in ("1", "2", "3")])
        l155 = listas.criar(op, "15.5", "Aplicações", u1)
        listas.vincular_secao(op, l155, s155)
        q155 = listas.sincronizar_questoes(op, l155, [QuestaoEntrada(r) for r in ("11", "18")])
        l5 = listas.criar(op, "L5", "Lista 5", u1)
        listas.vincular_topico(op, l5, aplicacoes)
        listas.vincular_topico(op, l5, extra)       # lista sem seção ligada a mais de um tópico
        q5 = listas.sincronizar_questoes(op, l5, [QuestaoEntrada(r) for r in ("8", "9")])
        lu2 = listas.criar(op, "14.6", "Gradiente", u2)
        qu2 = listas.sincronizar_questoes(op, lu2, [QuestaoEntrada("4")])

        s1 = cronograma.criar_sessao(op, u1, "S1", "2099-03-08", "**15.4 Polares**\n\nExercícios: 15.4: 1, 2")
        cronograma.vincular_questoes(op, s1, [q154["1"], q154["2"]])
        s2 = cronograma.criar_sessao(op, u1, "S2", "2099-03-10", "**15.5 Aplicações** — massa, centro de massa\n\nExercícios: 15.5: 11, 18")
        cronograma.vincular_questoes(op, s2, [q155["11"], q155["18"], q5["9"]])
        cronograma.criar_sessao(op, u1, "S3", "2099-03-12", "**Simulado cronometrado** — 2h30")
        cronograma.criar_sessao(op, u1, "S4", "2099-03-30", "**Depois da prova**")

        resumo = documentos.salvar(op, "resumo", "15.5.md", "15.5 Aplicações", "texto", unidade_id=u1, secao_id=s155)
        resolucao = documentos.salvar(op, "resolucao", "15.4-3.md", "Resolução 15.4-3", "r", unidade_id=u1, secao_id=s154, questao_id=q154["3"])
        f_titulo = formulas.criar(op, u1, "Massa de uma lâmina (15.5)", "m = \\iint \\rho")
        formulas.criar(op, u1, "Área polar", "A = \\int r", secao_id=s154)

        marcacoes.definir(op, q154["1"], "err")
        marcacoes.definir(op, q154["2"], "ok")
        marcacoes.definir(op, q5["8"], "dub")
        marcacoes.definir(op, qu2["4"], "err")
    return SimpleNamespace(
        u1=u1, polares=polares, aplicacoes=aplicacoes, extra=extra, q154=q154, q155=q155, q5=q5, qu2=qu2,
        resumo=resumo, resolucao=resolucao, f_titulo=f_titulo, s155=s155,
    )


def test_sessao_de_hoje_em_foco_com_o_material(con, plano):
    h = progresso.hoje(con, HOJE)
    s = h["sessao"]
    assert (s["codigo"], s["data"], s["estado"]) == ("S2", "2099-03-10", "hoje")
    assert (s["titulo"], s["detalhe"]) == ("15.5 Aplicações", "massa, centro de massa")
    assert [x["codigo"] for x in s["secoes"]] == ["15.5"]
    assert [d["id"] for d in s["resumos"]] == [plano.resumo]
    assert [f["id"] for f in s["formulas"]] == [plano.f_titulo]       # pelo código "(15.5)" no título
    assert [(q["lista_codigo"], q["rotulo"], q["estado"]) for q in s["questoes"]] == [
        ("15.5", "11", None), ("15.5", "18", None), ("L5", "9", None)]


def test_sem_sessao_hoje_vem_a_proxima(con, plano):
    s = progresso.hoje(con, date(2099, 3, 11))["sessao"]
    assert (s["codigo"], s["estado"]) == ("S3", "futura")
    assert s["questoes"] == [] and s["secoes"] == []


def test_estado_da_sessao_vem_do_trabalho_nas_questoes(con, plano):
    h = progresso.hoje(con, date(2099, 3, 12))
    estados = {s["codigo"]: s["estado"] for s in progresso.sessoes(con, date(2099, 3, 12))}
    assert estados == {"S1": "feita", "S2": "passou", "S3": "hoje", "S4": "futura"}
    assert h["sessao"]["codigo"] == "S3"


def test_proximos_sete_dias_juntam_sessoes_e_eventos(con, plano):
    itens = progresso.hoje(con, HOJE)["proximos"]
    assert [(i["data"], i["tipo"], i["codigo"]) for i in itens] == [
        ("2099-03-10", "sessao", "S2"), ("2099-03-11", "aula", None), ("2099-03-12", "sessao", "S3"), ("2099-03-15", "prova", None),
    ]


def test_revisar_traz_erros_e_duvidas_de_todas_as_unidades(con, plano):
    grupos = progresso.hoje(con, HOJE)["revisar"]
    assert [(g["lista_codigo"], g["unidade"], [(q["rotulo"], q["estado"]) for q in g["questoes"]]) for g in grupos] == [
        ("15.4", 1, [("1", "err")]), ("L5", 1, [("8", "dub")]), ("14.6", 2, [("4", "err")]),
    ]


def test_topicos_com_estado_e_progresso_derivados(con, plano):
    t = {x["id"]: x for x in progresso.hoje(con, HOJE)["topicos"]}
    polares, aplic, extra = t[plano.polares], t[plano.aplicacoes], t[plano.extra]
    # 15.4: coberto pela S1 (já passou); 1 erro, 1 certa e 1 resolução gravada
    assert polares["estado"] == "visto"
    assert (polares["total"], polares["trabalhadas"], polares["ok"], polares["err"], polares["dub"]) == (3, 3, 1, 1, 0)
    # 15.5 + L5 (ligada ao tópico): é o tópico da sessão de hoje
    assert aplic["estado"] == "hoje"
    assert (aplic["total"], aplic["trabalhadas"], aplic["dub"]) == (4, 1, 1)
    assert aplic["secoes"] == ["15.5"]
    # ligado só pela L5 (sem seção): a sessão de hoje tem seção, então não o cobre; o ? da L5 conta como trabalho
    assert (extra["estado"], extra["total"], extra["dub"]) == ("visto", 2, 1)


def test_status_manual_visto_ainda_vale(con, materia, plano):
    with operacao(con, "manual", materia.pasta) as op:
        solto = topicos.criar(op, plano.u1, "Tópico sem lista nem sessão")
        topicos.definir_status(op, solto, "visto")
        outro = topicos.criar(op, plano.u1, "Outro sem nada")
    t = {x["id"]: x for x in progresso.hoje(con, HOJE)["topicos"]}
    assert (t[solto]["estado"], t[outro]["estado"]) == ("visto", "a seguir")


def test_prova_e_reta_final(con, plano):
    h = progresso.hoje(con, HOJE)
    assert h["unidade"] == 1
    assert h["prova"] == {"data": "2099-03-15", "hora_inicio": None, "unidade": 1, "dias": 5}
    assert h["reta_final"] is True
    assert progresso.hoje(con, date(2099, 3, 1))["reta_final"] is False


def test_materia_vazia(con):
    h = progresso.hoje(con, HOJE)
    assert h == {
        "data": "2099-03-10", "unidade": None, "prova": None, "reta_final": False,
        "sessao": None, "proximos": [], "revisar": [], "topicos": [],
    }


def test_rota_hoje(tmp_path):
    from fastapi.testclient import TestClient

    from estudos.config import carregar_settings
    from estudos.main import create_app

    (tmp_path / "_app").mkdir()
    cliente = TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")
    uid = cliente.post("/api/materias", json={"nome": "Nova"}).json()["uid"]
    r = cliente.get(f"/api/materias/{uid}/hoje?data=2099-03-10")
    assert r.status_code == 200
    assert r.json()["data"] == "2099-03-10" and r.json()["sessao"] is None
