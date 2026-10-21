import hashlib
import shutil
from contextlib import closing
from pathlib import Path

import pytest

from estudos.db.conexao import conectar
from estudos.historico import listar as listar_historico
from estudos.historico import operacao
from estudos.migracao.executar import MigracaoRecusada, migrar
from estudos.repos import documentos, listas, livros, marcacoes, topicos, unidades
from estudos.workspace import descobrir_materias

FIXTURE = Path(__file__).parent / "fixtures" / "legado_minimo"
GERADOS = {"materia.db", "materia.db-wal", "materia.db-shm", "fontes", "conteudo", "figuras", ".versoes", ".migracao"}


@pytest.fixture
def pasta(tmp_path):
    destino = tmp_path / "Calculo Teste"
    shutil.copytree(FIXTURE, destino)
    return destino


@pytest.fixture
def migrada(pasta):
    relatorio = migrar(pasta, pasta)
    con = conectar(pasta / "materia.db")
    yield pasta, relatorio, con
    con.close()


def _unidade(con, numero):
    return next(u for u in unidades.listar(con) if u.numero == numero)


def _lista(con, codigo):
    return next(l for u in unidades.listar(con) for l in listas.listar(con, u.id) if l.codigo == codigo)


def _hashes(pasta):
    return {
        p.relative_to(pasta).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in pasta.rglob("*")
        if p.is_file() and p.relative_to(pasta).parts[0] not in GERADOS
    }


def test_contagens_batem(migrada):
    _, relatorio, _ = migrada
    assert relatorio.bate(), relatorio.contagens
    assert relatorio.contagens["questoes"] == (6, 6)
    assert relatorio.contagens["marcacoes"] == (3, 3)
    assert relatorio.contagens["sessoes"] == (3, 3)
    assert relatorio.contagens["livros"] == (3, 3)


def test_materia_e_unidades(migrada):
    pasta, _, con = migrada
    m = con.execute("SELECT nome, periodo, instituicao FROM materia").fetchone()
    assert tuple(m) == ("Cálculo Teste", "2026.2", "UFPE")
    assert [(u.numero, u.titulo, u.data_prova) for u in unidades.listar(con)] == [
        (1, "Primeira unidade", "2026-09-14"), (3, "Terceira unidade", "2026-11-30")]
    nota = con.execute("SELECT nota FROM nota_avaliacao").fetchall()
    assert [n[0] for n in nota] == [8.0]
    assert [m.nome for m in descobrir_materias(pasta.parent)] == ["Cálculo Teste"]


def test_marcacao_da_questao_repetida(migrada):
    _, relatorio, con = migrada
    l = _lista(con, "14.1")
    questoes = {q.rotulo: q for q in listas.listar_questoes(con, l.id)}
    assert [q.linha for q in questoes.values()] == [1, 1, 2]
    assert marcacoes.estados(con, l.unidade_id)[questoes["30"].id] == "err"
    assert any("14.1 #30" in d for d in relatorio.decisoes)


def test_estado_das_listas_preservado(migrada):
    _, _, con = migrada
    estados = {c: (_lista(con, c).aberta, _lista(con, c).liberacao) for c in ("14.1", "15.4", "L5")}
    assert estados == {"14.1": (True, "auto"), "15.4": (False, "auto"), "L5": (True, "aberta")}


def test_enunciado_convertido_e_figura(migrada):
    pasta, _, con = migrada
    q = listas.listar_questoes(con, _lista(con, "14.1").id)[0]
    assert q.enunciado_md == "Determine e esboce o **domínio**." and q.figura == "ex22"
    assert (pasta / "figuras" / "ex22.png").read_bytes() == (pasta / "_app/img/ex22.png").read_bytes()


def test_livros_secoes_e_equivalencia(migrada):
    _, _, con = migrada
    principal = livros.principal(con)
    secoes = {s.codigo: s for s in livros.listar_secoes(con, principal.fonte_id)}
    assert (secoes["14.1"].pagina_pdf_fim, secoes["15.4"].pagina_pdf_fim) == (314, 406)
    assert principal.offset_pagina == -489
    pares = con.execute("SELECT count(*) FROM secao_equivalente").fetchone()[0]
    assert pares == 2
    tipos = dict(con.execute("SELECT caminho, tipo FROM fonte").fetchall())
    assert tipos["fontes/listas/Lista5.pdf"] == "lista" and tipos["fontes/documentos/Programa.pdf"] == "outro"
    assert tipos["fontes/livros/extra.pdf"] == "livro"
    assert _lista(con, "L5").fonte_id is not None


def test_topicos_e_vinculos(migrada):
    _, relatorio, con = migrada
    u3 = _unidade(con, 3)
    [t] = topicos.listar(con, u3.id)
    assert (t.titulo, t.status) == ("Integrais duplas em polares", "proxima")
    assert t.detalhe_md == "Previsto: Sex 30/10\nOnde: Stewart 15.4, 10.3 · Guidorizzi 8, 14.1\n\ndA = r dr dθ"
    assert len(topicos.listar(con, _unidade(con, 1).id)) == 1
    assert any("10.3" in a for a in relatorio.avisos)
    vinculos = sorted(tuple(v) for v in con.execute(
        "SELECT f.titulo, s.codigo FROM topico_secao ts JOIN secao_livro s ON s.id = ts.secao_id"
        " JOIN fonte f ON f.id = s.livro_id WHERE ts.topico_id = ?", (t.id,)
    ).fetchall())
    assert [tuple(v) for v in vinculos] == [("Guidorizzi", "8"), ("Stewart", "15.4")]
    assert any("Guidorizzi" in a and "14.1" in a for a in relatorio.avisos)


def test_sessoes_com_questoes(migrada):
    _, _, con = migrada
    from estudos.repos import cronograma

    s1, s2 = cronograma.listar(con, _unidade(con, 1).id)
    assert (s1.codigo, s1.data, s1.feito, len(s1.questao_ids)) == ("S1", "2026-08-31", True, 2)
    assert "Exercícios: 68 (pendente) + 20" in s2.foco_md and s2.questao_ids == ()
    [p1] = cronograma.listar(con, _unidade(con, 3).id)
    assert len(p1.questao_ids) == 3 and p1.foco_md.startswith("Polares — o começo")


def test_resumos_documentos_e_contexto(migrada):
    pasta, relatorio, con = migrada
    u1, u3 = _unidade(con, 1), _unidade(con, 3)
    resumos = {d.caminho: d for d in documentos.listar(con, "resumo")}
    assert resumos["conteudo/resumos/00-polares.md"].unidade_id == u1.id
    assert resumos["conteudo/resumos/01-funcoes.md"].unidade_id == u1.id
    assert resumos["conteudo/resumos/02-solto.md"].unidade_id is None
    assert "conteudo/resumos/00-polares.md" in {d.caminho for d in documentos.listar(con, "resumo", u3.id)}
    corpo = documentos.ler_corpo(pasta, resumos["conteudo/resumos/01-funcoes.md"])
    assert corpo == (pasta / "resumos/01-funcoes.md").read_text(encoding="utf-8")
    assert any("02-solto" in n for n in relatorio.nao_resolvidos)
    tipos = sorted((d.tipo, d.caminho) for d in documentos.listar(con) if d.tipo != "resumo" and d.tipo != "resolucao")
    assert ("contexto", "conteudo/contexto.md") in tipos
    assert ("plano", "conteudo/planos/plano-estudos-unidade1.md") in tipos
    assert ("anotacao", "conteudo/anotacoes/legado-unidade-3.md") in tipos
    calendario = next(d for d in documentos.listar(con) if d.caminho.endswith("calendario.md"))
    assert calendario.unidade_id is None
    assert any("nao-existe.md" in n for n in relatorio.nao_resolvidos)
    tabela = documentos.ler_corpo(pasta, next(d for d in documentos.listar(con) if d.caminho.endswith("legado-unidade-3.md")))
    assert "| Prioridade | O quê | Por quê |" in tabela and "| Prio 1 | **Triplas** | metade da prova |" in tabela


def test_resolucao_orfa_no_relatorio(migrada):
    _, relatorio, con = migrada
    resolucoes = {d.caminho: d for d in documentos.listar(con, "resolucao")}
    assert resolucoes["conteudo/resolucoes/14-1-22.md"].questao_id is not None
    assert resolucoes["conteudo/resolucoes/15-4-99.md"].questao_id is None
    assert any("15.4-99" in n for n in relatorio.nao_resolvidos)
    assert any("99.9-1" in n for n in relatorio.nao_resolvidos)


def test_legado_intocado(pasta):
    antes = _hashes(pasta)
    migrar(pasta, pasta)
    assert _hashes(pasta) == antes


def test_reexecucao_idempotente(pasta):
    r1 = migrar(pasta, pasta)
    uid = descobrir_materias(pasta.parent)[0].uid
    r2 = migrar(pasta, pasta)
    assert descobrir_materias(pasta.parent)[0].uid == uid
    assert r1.contagens == r2.contagens
    assert len(list((pasta / "fontes").rglob("*.pdf"))) == 5


def test_recusa_com_historico(pasta):
    migrar(pasta, pasta)
    with closing(conectar(pasta / "materia.db")) as con, operacao(con, "ação do usuário") as op:
        unidades.criar(op, 9)
    with pytest.raises(MigracaoRecusada):
        migrar(pasta, pasta)
    relatorio = migrar(pasta, pasta, forcar=True)
    with closing(conectar(pasta / "materia.db")) as con:
        assert [u.numero for u in unidades.listar(con)] == [1, 3]
    assert relatorio.bate()


def test_historico_vazio_apos_migrar(migrada):
    _, _, con = migrada
    assert listar_historico(con) == []


def test_relatorio_gravado(migrada):
    pasta, relatorio, _ = migrada
    texto = (pasta / ".migracao" / "relatorio.md").read_text(encoding="utf-8")
    assert texto == relatorio.markdown()
    assert "14.1 #30" in texto and "Não resolvidos" in texto


def test_migrar_para_outra_pasta(pasta, tmp_path):
    destino = tmp_path / "ws" / "Calculo Teste"
    relatorio = migrar(pasta, destino)
    assert relatorio.bate() and (destino / "materia.db").exists()
    assert not (pasta / "materia.db").exists()


def test_notas_das_fases_preservadas(migrada):
    pasta, _, con = migrada
    nota = documentos.ler_corpo(pasta, next(d for d in documentos.listar(con) if d.caminho.endswith("legado-unidade-1.md")))
    assert "O que ficou em aberto: **14.2 #18**" in nota and "concluída" in nota and "Sessões até a prova" in nota
    assert "- **Subtítulo:** Funções de várias variáveis." in nota
    tabela = documentos.ler_corpo(pasta, next(d for d in documentos.listar(con) if d.caminho.endswith("legado-unidade-3.md")))
    assert "Se o tempo apertar" in tabela


def test_bate_detecta_vinculo_faltando(pasta, monkeypatch):
    monkeypatch.setattr(livros, "vincular_topico", lambda *a, **k: None)
    relatorio = migrar(pasta, pasta)
    assert not relatorio.bate()
    assert relatorio.contagens["topico_secao"][0] > relatorio.contagens["topico_secao"][1]


def test_contagens_de_relacoes(migrada):
    _, relatorio, _ = migrada
    c = relatorio.contagens
    assert c["eventos_prova"] == (2, 2) and c["notas"] == (1, 1)
    assert c["lista_secao"] == (2, 2) and c["lista_topico"] == (3, 3)
    assert c["topico_secao"] == (3, 3) and c["secao_equivalente"] == (2, 2)
    assert c["sessao_questao"] == (5, 5) and c["extras_documento"] == (1, 1)
    assert c["figuras_referenciadas"] == (1, 1)
    assert c["itens_brutos"] == (7, 7)


def test_recusa_pasta_gerada_que_ja_existia(pasta):
    (pasta / "figuras").mkdir()
    (pasta / "figuras" / "minha.png").write_bytes(b"do legado")
    with pytest.raises(MigracaoRecusada, match="figuras"):
        migrar(pasta, pasta)
    assert (pasta / "figuras" / "minha.png").read_bytes() == b"do legado"
    assert not (pasta / "materia.db").exists()
