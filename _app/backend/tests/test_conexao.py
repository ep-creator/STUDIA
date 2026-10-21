import threading

import pytest

from estudos.db.conexao import aplicar_migracoes, conectar, transacao


def test_pragmas(tmp_path):
    con = conectar(tmp_path / "m.db")
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert con.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert con.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def test_transacao_rollback(tmp_path):
    con = conectar(tmp_path / "m.db")
    con.execute("CREATE TABLE t(x)")
    with pytest.raises(RuntimeError):
        with transacao(con):
            con.execute("INSERT INTO t VALUES (1)")
            raise RuntimeError
    assert con.execute("SELECT count(*) FROM t").fetchone()[0] == 0


def test_transacao_aninhada_savepoint(tmp_path):
    con = conectar(tmp_path / "m.db")
    con.execute("CREATE TABLE t(x)")
    with transacao(con):
        con.execute("INSERT INTO t VALUES ('externa')")
        with pytest.raises(RuntimeError):
            with transacao(con):
                con.execute("INSERT INTO t VALUES ('interna')")
                raise RuntimeError
    assert [r[0] for r in con.execute("SELECT x FROM t")] == ["externa"]


def test_migracoes_em_ordem_e_idempotentes(tmp_path):
    pasta = tmp_path / "mig"
    pasta.mkdir()
    (pasta / "0002_b.sql").write_text("CREATE TABLE b(x REFERENCES a(x));")
    (pasta / "0001_a.sql").write_text("CREATE TABLE a(x PRIMARY KEY);")
    con = conectar(tmp_path / "m.db")
    assert aplicar_migracoes(con, pasta) == 2
    assert aplicar_migracoes(con, pasta) == 2
    assert con.execute("SELECT count(*) FROM schema_versao").fetchone()[0] == 2


def test_migracao_com_erro_nao_avanca_versao(tmp_path):
    pasta = tmp_path / "mig"
    pasta.mkdir()
    (pasta / "0001_a.sql").write_text("CREATE TABLE a(x);")
    (pasta / "0002_ruim.sql").write_text("CREATE TABLE c(x); ISSO NAO E SQL;")
    con = conectar(tmp_path / "m.db")
    with pytest.raises(Exception):
        aplicar_migracoes(con, pasta)
    assert con.execute("SELECT max(versao) FROM schema_versao").fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM sqlite_master WHERE name='c'").fetchone()[0] == 0


def test_escritas_concorrentes(tmp_path):
    caminho = tmp_path / "m.db"
    conectar(caminho).execute("CREATE TABLE t(x)")
    erros = []

    def escrever(prefixo):
        con = conectar(caminho)
        try:
            for i in range(50):
                with transacao(con):
                    con.execute("INSERT INTO t VALUES (?)", (f"{prefixo}{i}",))
        except Exception as e:  # pragma: no cover - só aparece se falhar
            erros.append(e)

    threads = [threading.Thread(target=escrever, args=(p,)) for p in "ab"]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert erros == []
    assert conectar(caminho).execute("SELECT count(*) FROM t").fetchone()[0] == 100
