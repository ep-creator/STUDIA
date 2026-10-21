import pytest

from estudos.erros import DadoInvalido
from estudos.historico import desfazer_ultimo, listar, operacao, podar
from estudos.repos._base import atualizar, inserir, obter, remover


def _unidade(op, numero=1):
    return inserir(op, "unidade", {"numero": numero, "titulo": f"U{numero}", "origem": "manual"})


def test_desfazer_insercao(con):
    with operacao(con, "criar unidade") as op:
        uid = _unidade(op)
    desfeito = desfazer_ultimo(con)
    assert desfeito.descricao == "criar unidade"
    assert obter(con, "unidade", {"id": uid}) is None


def test_desfazer_atualizacao_e_remocao_em_grupo(con):
    with operacao(con, "base") as op:
        u1, u2 = _unidade(op, 1), _unidade(op, 2)
    with operacao(con, "editar") as op:
        atualizar(op, "unidade", {"id": u1}, {"titulo": "Derivadas"})
        remover(op, "unidade", {"id": u2})
    desfazer_ultimo(con)
    assert obter(con, "unidade", {"id": u1})["titulo"] == "U1"
    assert obter(con, "unidade", {"id": u2})["titulo"] == "U2"


def test_desfazer_remocao_reinsere_filhos_em_cascata(con):
    with operacao(con, "base") as op:
        u = _unidade(op)
        evento = inserir(op, "evento", {"tipo": "prova", "data": "2026-09-14", "unidade_id": u, "origem": "manual"})
        lista = inserir(op, "lista", {"codigo": "L1", "titulo": "L1", "unidade_id": u, "ordem": 1, "origem": "manual"})
        q = inserir(op, "questao", {"lista_id": lista, "rotulo": "1", "ordem": 1})
        inserir(op, "marcacao", {"questao_id": q, "estado": "ok", "atualizado_em": "x"})
    with operacao(con, "apagar lista") as op:
        remover(op, "lista", {"id": lista})
    assert obter(con, "questao", {"id": q}) is None
    desfazer_ultimo(con)
    assert obter(con, "lista", {"id": lista})["codigo"] == "L1"
    assert obter(con, "questao", {"id": q})["rotulo"] == "1"
    assert obter(con, "marcacao", {"questao_id": q})["estado"] == "ok"
    assert obter(con, "evento", {"id": evento})["unidade_id"] == u


def test_desfazer_remocao_restaura_filhos_set_null(con):
    with operacao(con, "base") as op:
        u = _unidade(op)
        evento = inserir(op, "evento", {"tipo": "prova", "data": "2026-09-14", "unidade_id": u, "origem": "manual"})
    with operacao(con, "apagar unidade") as op:
        remover(op, "unidade", {"id": u})
    assert obter(con, "evento", {"id": evento})["unidade_id"] is None
    desfazer_ultimo(con)
    assert obter(con, "evento", {"id": evento})["unidade_id"] == u


def test_desfazer_nao_repete_grupo_ja_desfeito(con):
    with operacao(con, "u1") as op:
        u1 = _unidade(op, 1)
    with operacao(con, "u2") as op:
        u2 = _unidade(op, 2)
    assert desfazer_ultimo(con).descricao == "u2"
    assert desfazer_ultimo(con).descricao == "u1"
    assert desfazer_ultimo(con) is None
    assert obter(con, "unidade", {"id": u1}) is None and obter(con, "unidade", {"id": u2}) is None


def test_grupo_de_desfazer_fica_no_historico(con):
    with operacao(con, "u1") as op:
        _unidade(op)
    desfazer_ultimo(con)
    grupos = listar(con)
    assert grupos[0].desfaz_grupo == grupos[1].id
    assert grupos[1].desfeito_em is not None


def test_falha_no_meio_nao_deixa_grupo(con):
    with pytest.raises(RuntimeError):
        with operacao(con, "falha") as op:
            _unidade(op)
            raise RuntimeError
    assert listar(con) == []
    assert con.execute("SELECT count(*) FROM unidade").fetchone()[0] == 0


def test_grupo_sem_mudancas_e_descartado(con):
    with operacao(con, "nada"):
        pass
    assert listar(con) == []


def test_tabela_nao_permitida(con):
    with operacao(con, "x") as op, pytest.raises(DadoInvalido):
        inserir(op, "historico_grupo", {"descricao": "hack"})


def test_coluna_inexistente(con):
    with operacao(con, "x") as op, pytest.raises(DadoInvalido):
        inserir(op, "unidade", {"numero": 1, "origem": "manual", "titulo; DROP TABLE unidade": "x"})


def test_podar(con):
    for n in range(1, 6):
        with operacao(con, f"u{n}") as op:
            _unidade(op, n)
    assert podar(con, 2) == 3
    assert [g.descricao for g in listar(con)] == ["u5", "u4"]


def test_desfazer_remocao_unidade_com_arvore_de_topicos(con):
    from estudos.repos import topicos

    with operacao(con, "base") as op:
        u = _unidade(op)
        a = topicos.criar(op, u, "A")
        b = topicos.criar(op, u, "B", pai_id=a)
        topicos.criar(op, u, "C", pai_id=b)
    antes = [tuple(r) for r in con.execute("SELECT * FROM topico ORDER BY id")]
    with operacao(con, "remover unidade") as op:
        remover(op, "unidade", {"id": u})
    desfazer_ultimo(con)
    assert [tuple(r) for r in con.execute("SELECT * FROM topico ORDER BY id")] == antes


def test_poda_nao_transforma_desfazer_em_acao_comum(con):
    with operacao(con, "A") as op:
        uid = _unidade(op, 7)
    desfazer_ultimo(con)
    podar(con, 1)
    assert desfazer_ultimo(con) is None
    assert obter(con, "unidade", {"id": uid}) is None
