import datetime
from contextlib import closing

from estudos.agente import conversas
from estudos.db.conexao import conectar
from estudos.workspace import criar_materia


def test_uma_conversa_ativa_por_alvo_e_papel(con):
    a = conversas.conversa_ativa(con, "questao:7", "tutor")
    assert conversas.conversa_ativa(con, "questao:7", "tutor").id == a.id
    assert conversas.conversa_ativa(con, "questao:8", "tutor").id != a.id
    assert conversas.conversa_ativa(con, "questao:7", "resumidor").id != a.id


def test_recomecar_arquiva_e_abre_outra(con):
    a = conversas.conversa_ativa(con, "secao:3", "resumidor")
    conversas.adicionar(con, a.id, "voce", "resuma")
    b = conversas.recomecar(con, "secao:3", "resumidor")
    assert b.id != a.id and conversas.mensagens(con, b.id) == []
    assert [m.texto for m in conversas.mensagens(con, a.id)] == ["resuma"]
    assert conversas.conversa_ativa(con, "secao:3", "resumidor").id == b.id


def test_mensagens_em_ordem_com_custo(con):
    c = conversas.conversa_ativa(con, "geral", "estrategista")
    conversas.adicionar(con, c.id, "voce", "plano")
    conversas.adicionar(con, c.id, "agente", "aqui está", tokens_entrada=100, tokens_saida=50, custo_brl=0.02, modelo="m")
    ms = conversas.mensagens(con, c.id)
    assert [(m.autor, m.texto) for m in ms] == [("voce", "plano"), ("agente", "aqui está")] and ms[1].custo_brl == 0.02


def test_total_do_mes_soma_as_materias(tmp_path):
    hoje = datetime.date(2026, 10, 27)
    for nome, custos in (("A", [0.10, 0.20]), ("B", [0.05])):
        m = criar_materia(tmp_path, nome)
        with closing(conectar(m.db)) as con:
            c = conversas.conversa_ativa(con, "geral", "estrategista")
            for v in custos:
                conversas.adicionar(con, c.id, "agente", "x", custo_brl=v)
            con.execute("INSERT INTO mensagem (conversa_id, autor, texto, tokens_entrada, tokens_saida, custo_brl, criada_em) "
                        "VALUES (?, 'agente', 'mês passado', 0, 0, 9.0, '2026-09-30T10:00:00')", (c.id,))
            con.commit()
    assert round(conversas.total_do_mes(tmp_path, hoje), 4) == 0.35


def test_conversa_nao_entra_no_historico(con):
    antes = con.execute("SELECT count(*) FROM historico_grupo").fetchone()[0]
    c = conversas.conversa_ativa(con, "geral", "estrategista")
    conversas.adicionar(con, c.id, "voce", "oi")
    assert con.execute("SELECT count(*) FROM historico_grupo").fetchone()[0] == antes


def test_estimativa_padrao_e_pelo_maior_recente(tmp_path):
    m = criar_materia(tmp_path, "A")
    assert conversas.estimativa(tmp_path) == 0.05
    with closing(conectar(m.db)) as con:
        c = conversas.conversa_ativa(con, "geral", "estrategista")
        for v in (0.01, 0.08, 0.02):
            conversas.adicionar(con, c.id, "agente", "x", custo_brl=v)
    assert conversas.estimativa(tmp_path) == 0.08


def _questao(con, materia, codigo="14.1", rotulo="22"):
    from estudos.historico import operacao
    from estudos.modelos import QuestaoEntrada
    from estudos.repos import listas, unidades
    with operacao(con, "base", materia.pasta) as op:
        lid = listas.criar(op, codigo, "Funções", unidades.criar(op, 1))
        listas.sincronizar_questoes(op, lid, [QuestaoEntrada(rotulo, enunciado_md="Esboce.")])
    return listas.listar_questoes(con, lid)[0].id


def _mensagem_em(con, alvo, papel, quando):
    c = conversas.conversa_ativa(con, alvo, papel)
    mid = conversas.adicionar(con, c.id, "voce", "oi")
    con.execute("UPDATE mensagem SET criada_em = ? WHERE id = ?", (quando, mid))
    return c


def test_ativas_lista_so_conversas_com_mensagem_mais_recentes_primeiro(con, materia):
    qid = _questao(con, materia)
    _mensagem_em(con, "geral", "estrategista", "2026-10-27T10:00:00")
    _mensagem_em(con, f"questao:{qid}", "tutor", "2026-10-28T09:00:00")
    conversas.conversa_ativa(con, "questao:9999", "tutor")   # aberta, mas sem mensagem
    r = conversas.ativas(con)
    assert [(c.rotulo, c.papel) for c in r] == [("14.1 #22", "tutor"), ("Geral", "estrategista")]
    assert r[0].alvo == f"questao:{qid}" and r[0].atualizada_em == "2026-10-28T09:00:00"


def test_rotulo_de_alvo_apagado_cai_para_o_alvo(con):
    _mensagem_em(con, "questao:999", "tutor", "2026-10-28T09:00:00")
    _mensagem_em(con, "secao:999", "resumidor", "2026-10-27T09:00:00")
    assert [c.rotulo for c in conversas.ativas(con)] == ["questao:999", "secao:999"]


def test_rotulo_de_secao_tem_codigo_e_titulo(con, materia, cenario_busca):
    _mensagem_em(con, f"secao:{cenario_busca['s11']}", "resumidor", "2026-10-28T09:00:00")
    assert [c.rotulo for c in conversas.ativas(con)] == ["1.1 Coordenadas polares"]


def test_conversa_recomecada_some_da_lista_ate_ter_mensagem(con):
    _mensagem_em(con, "geral", "estrategista", "2026-10-28T09:00:00")
    conversas.recomecar(con, "geral", "estrategista")
    assert conversas.ativas(con) == []
