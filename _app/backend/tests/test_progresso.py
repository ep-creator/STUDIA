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
    assert polares["estado"] == "em dia"                   # aula passou e 3 de 3 trabalhadas
    assert (polares["total"], polares["trabalhadas"], polares["ok"], polares["err"], polares["dub"]) == (3, 3, 1, 1, 0)
    # 15.5 + L5 (ligada ao tópico): é o tópico da sessão de hoje
    assert aplic["estado"] == "hoje"
    assert (aplic["total"], aplic["trabalhadas"], aplic["dub"]) == (4, 1, 1)
    assert aplic["secoes"] == ["15.5"]
    # ligado só pela L5 (sem seção): a sessão de hoje tem seção, então não o cobre; a aula dele ainda não veio
    assert (extra["estado"], extra["total"], extra["dub"]) == ("a seguir", 2, 1)
    assert (polares["ultima_aula"], aplic["ultima_aula"], extra["ultima_aula"]) == ("2099-03-08", None, None)


def test_status_manual_visto_ainda_vale(con, materia, plano):
    with operacao(con, "manual", materia.pasta) as op:
        solto = topicos.criar(op, plano.u1, "Tópico sem lista nem sessão")
        topicos.definir_status(op, solto, "visto")
        outro = topicos.criar(op, plano.u1, "Outro sem nada")
    t = {x["id"]: x for x in progresso.hoje(con, HOJE)["topicos"]}
    assert (t[solto]["estado"], t[outro]["estado"]) == ("em dia", "a seguir")   # visto à mão, sem questões


def test_prova_e_reta_final(con, plano):
    h = progresso.hoje(con, HOJE)
    assert h["unidade"] == 1
    assert h["prova"] == {"data": "2099-03-15", "hora_inicio": None, "unidade": 1, "dias": 5}
    assert h["reta_final"] is True
    assert progresso.hoje(con, date(2099, 3, 1))["reta_final"] is False


def test_materia_vazia(con):
    h = progresso.hoje(con, HOJE)
    assert h == {
        "data": "2099-03-10", "unidade": None, "prova": None, "reta_final": False, "tem_datas": False, "prova_passada": None, "unidade_atual": None,
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


def test_pagina_do_topico_junta_secao_resumo_formulas_questoes_e_resolucoes(con, plano):
    p = progresso.pagina_topico(con, plano.polares, HOJE)
    assert (p["topico"]["titulo"], p["topico"]["estado"], p["unidade"]) == ("Integrais em polares", "em dia", 1)
    assert [s["codigo"] for s in p["secoes"]] == ["15.4"]
    assert p["resumos"] == []                                   # só a 15.5 tem resumo
    assert [f["titulo"] for f in p["formulas"]] == ["Área polar"]
    [lista] = p["listas"]
    assert (lista["codigo"], [(q["rotulo"], q["estado"], q["resolucao_id"]) for q in lista["questoes"]]) == (
        "15.4", [("1", "err", None), ("2", "ok", None), ("3", None, plano.resolucao)])
    assert [(r["id"], r["rotulo"]) for r in p["resolucoes"]] == [(plano.resolucao, "15.4 #3")]


def test_pagina_do_topico_pela_formula_no_titulo_e_lista_ligada(con, plano):
    p = progresso.pagina_topico(con, plano.aplicacoes, HOJE)
    assert [d["id"] for d in p["resumos"]] == [plano.resumo]
    assert [f["id"] for f in p["formulas"]] == [plano.f_titulo]
    assert [l["codigo"] for l in p["listas"]] == ["15.5", "L5"]


def test_progresso_de_outra_unidade(con, plano):
    assert progresso.topicos_da_unidade(con, 2, HOJE) == []
    assert [t["id"] for t in progresso.topicos_da_unidade(con, 1, HOJE)][:2] == [plano.polares, plano.aplicacoes]


def test_pagina_de_topico_que_nao_existe(con, plano):
    from estudos.erros import NaoEncontrado
    with pytest.raises(NaoEncontrado):
        progresso.pagina_topico(con, 999, HOJE)


def test_rotas_de_progresso_e_pagina(tmp_path):
    from fastapi.testclient import TestClient

    from estudos.config import carregar_settings
    from estudos.main import create_app

    (tmp_path / "_app").mkdir()
    cliente = TestClient(create_app(carregar_settings(tmp_path / "_app", tmp_path)), base_url="http://127.0.0.1:8790")
    uid = cliente.post("/api/materias", json={"nome": "Nova"}).json()["uid"]
    assert cliente.get(f"/api/materias/{uid}/progresso?unidade=1").status_code == 404
    assert cliente.get(f"/api/materias/{uid}/topicos/1/pagina").status_code == 404


def test_sessao_so_fica_feita_com_todas_as_questoes_trabalhadas(con, materia, plano):
    with operacao(con, "metade", materia.pasta) as op:
        marcacoes.definir(op, plano.q155["11"], "ok")
    s2 = next(s for s in progresso.sessoes(con, HOJE) if s["codigo"] == "S2")
    assert (s2["estado"], s2["trabalhadas"], s2["total"]) == ("hoje", 1, 3)
    with operacao(con, "resto", materia.pasta) as op:
        marcacoes.definir(op, plano.q155["18"], "err")
        marcacoes.definir(op, plano.q5["9"], "ok")
    s2 = next(s for s in progresso.sessoes(con, HOJE) if s["codigo"] == "S2")
    assert (s2["estado"], s2["trabalhadas"], s2["total"]) == ("feita", 3, 3)


def test_topico_adiantado_continua_a_seguir_com_o_placar(con, materia, plano):
    with operacao(con, "adiantado", materia.pasta) as op:
        marcacoes.definir(op, plano.q155["18"], "ok")
    t = {x["id"]: x for x in progresso.hoje(con, date(2099, 3, 1))["topicos"]}
    assert (t[plano.aplicacoes]["estado"], t[plano.aplicacoes]["trabalhadas"]) == ("a seguir", 2)   # a S2 ainda não chegou
    assert t[plano.polares]["estado"] == "a seguir"        # nem a S1 (15.4), mas já tem marcações (o placar mostra)


def test_sessoes_da_unidade_para_o_plano(con, plano):
    lista = progresso.sessoes_da_unidade(con, 1, date(2099, 3, 12))
    assert [(s["codigo"], s["estado"], s["trabalhadas"], s["total"]) for s in lista] == [
        ("S1", "feita", 2, 2), ("S2", "passou", 0, 3), ("S3", "hoje", 0, 0), ("S4", "futura", 0, 0)]


def test_aula_passada_com_pouca_pratica_e_falta_praticar(con, materia, plano):
    with operacao(con, "desfaz", materia.pasta) as op:
        marcacoes.definir(op, plano.q154["2"], None)
    t = {x["id"]: x for x in progresso.hoje(con, HOJE)["topicos"]}
    # 15.4: 3 questões, 1 erro e 1 resolução = 2 de 3 trabalhadas (metade ou mais) → em dia
    assert (t[plano.polares]["estado"], t[plano.polares]["trabalhadas"]) == ("em dia", 2)
    with operacao(con, "desfaz2", materia.pasta) as op:
        marcacoes.definir(op, plano.q154["1"], None)
    t = {x["id"]: x for x in progresso.hoje(con, HOJE)["topicos"]}
    assert (t[plano.polares]["estado"], t[plano.polares]["trabalhadas"]) == ("falta praticar", 1)


def test_revisar_traz_o_enunciado_curto(con, materia, plano):
    from estudos.modelos import QuestaoEntrada as Q
    with operacao(con, "enunciado", materia.pasta) as op:
        lista = con.execute("SELECT lista_id FROM questao WHERE id = ?", (plano.q154["1"],)).fetchone()[0]
        listas.sincronizar_questoes(op, lista, [Q("1", enunciado_md="Calcule  a integral\n em polares."), Q("2"), Q("3")])
    [g] = [g for g in progresso.hoje(con, HOJE)["revisar"] if g["lista_codigo"] == "15.4"]
    assert g["questoes"][0]["enunciado"] == "Calcule a integral em polares."


def test_indice_de_todas_as_unidades(con, plano):
    i = progresso.indice(con)
    assert ("14.6", "4", 2) in [(q["lista_codigo"], q["rotulo"], q["unidade"]) for q in i["questoes"]]
    assert [t["titulo"] for t in i["topicos"]][:2] == ["Integrais em polares", "Aplicações"]


def test_hoje_da_unidade_pedida(con, plano):
    h = progresso.hoje(con, HOJE, 2)
    assert h["unidade"] == 2 and h["sessao"] is None             # a 2ª não tem sessão no plano
    assert h["prova"]["unidade"] == 2 and h["tem_datas"] is True   # tem a prova marcada
    assert h["topicos"] == []
    assert progresso.hoje(con, HOJE, 9)["unidade"] == 1           # unidade que não existe: a atual
    assert progresso.hoje(con, HOJE)["tem_datas"] is True


def test_previa_sem_marcacao_do_markdown():
    assert progresso._curto("Faça o **mapa de contorno** | `f` ## fim") == "Faça o mapa de contorno f fim"


def test_hoje_de_unidade_que_ja_terminou(con, plano):
    depois = HOJE.replace(year=HOJE.year + 1)                      # a prova de todas as unidades já passou
    h = progresso.hoje(con, depois, 1)
    assert h["prova"] is None and h["prova_passada"] is not None
    assert progresso.hoje(con, HOJE, 1)["prova_passada"] is None and progresso.hoje(con, HOJE, 1)["unidade_atual"] == 1


def test_resolucao_da_ia_nao_conta_como_pratica(con, materia, plano):
    with operacao(con, "ia", materia.pasta) as op:
        documentos.salvar(op, "resolucao", "15.4-2-ia.md", "Resolução 15.4-2", "r", unidade_id=plano.u1,
                          questao_id=plano.q154["2"], origem="agente")
        doc = documentos.salvar(op, "resolucao", "L5-9-ia.md", "Resolução L5-9", "r", unidade_id=plano.u1,
                                questao_id=plano.q5["9"], origem="agente")
    feitas = progresso.trabalhadas(con)
    assert plano.q5["9"] not in feitas and plano.q154["3"] in feitas      # a da IA não; a gravada à mão sim
    q = next(x for x in progresso.hoje(con, HOJE)["sessao"]["questoes"] if x["id"] == plano.q5["9"])
    assert q["resolucao_id"] == doc                                         # continua à mão para ler


def test_unidade_encerrada_nao_cobra_o_que_ficou(con, plano):
    depois = date(2099, 3, 20)                                  # a prova da 1ª foi em 15/03
    t = {x["id"]: x for x in progresso.topicos(con, plano.u1, depois)}
    assert t[plano.polares]["estado"] == "em dia"              # o que ficou em dia continua em dia
    assert t[plano.aplicacoes]["estado"] == "prova passou"     # o resto não vira "falta praticar" para sempre
    assert t[plano.aplicacoes]["trabalhadas"] == 1             # o placar continua dizendo quanto se praticou


def test_topico_conta_so_listas_da_propria_unidade(con, materia, plano):
    with operacao(con, "outra unidade", materia.pasta) as op:
        lu2 = con.execute("SELECT id FROM lista WHERE codigo = '14.6'").fetchone()[0]
        listas.vincular_topico(op, lu2, plano.polares)   # uma lista da 2ª ligada a um tópico da 1ª
    t = {x["id"]: x for x in progresso.topicos(con, plano.u1, HOJE)}
    assert t[plano.polares]["total"] == 3                      # a 14.6 (2ª unidade) não entra no placar
    assert all(l["unidade"] == 1 for l in progresso.pagina_topico(con, plano.polares, HOJE)["listas"])

