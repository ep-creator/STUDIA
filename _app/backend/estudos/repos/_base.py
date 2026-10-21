"""Acesso genérico a linhas com registro no histórico. Único lugar que monta SQL com nomes dinâmicos."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from estudos.erros import DadoInvalido, NaoEncontrado

if TYPE_CHECKING:
    from estudos.historico import Operacao

TABELAS_PERMITIDAS = frozenset({
    "materia", "unidade", "evento", "horario_aula", "topico", "fonte", "livro", "secao_livro", "topico_secao",
    "lista", "lista_secao", "lista_topico", "questao", "marcacao", "sessao_estudo", "sessao_questao", "formula",
    "documento", "nota_avaliacao", "criterio_correcao",
})


def _colunas(con: sqlite3.Connection, tabela: str) -> list[sqlite3.Row]:
    if tabela not in TABELAS_PERMITIDAS:
        raise DadoInvalido(f"Tabela não permitida: {tabela}")
    return con.execute(f"PRAGMA table_info({tabela})").fetchall()


def _validar(con: sqlite3.Connection, tabela: str, nomes) -> None:
    existentes = {c["name"] for c in _colunas(con, tabela)}
    invalidas = set(nomes) - existentes
    if invalidas:
        raise DadoInvalido(f"Colunas inexistentes em {tabela}: {sorted(invalidas)}")


def chave_primaria(con: sqlite3.Connection, tabela: str) -> list[str]:
    return [c["name"] for c in sorted(_colunas(con, tabela), key=lambda c: c["pk"]) if c["pk"]]


def _where(chave: dict) -> tuple[str, list]:
    return " AND ".join(f"{c} = ?" for c in chave), list(chave.values())


def obter(con: sqlite3.Connection, tabela: str, chave: dict) -> dict | None:
    _validar(con, tabela, chave)
    filtro, params = _where(chave)
    linha = con.execute(f"SELECT * FROM {tabela} WHERE {filtro}", params).fetchone()
    return dict(linha) if linha else None


def _chave_da_linha(con: sqlite3.Connection, tabela: str, linha: dict) -> dict:
    return {c: linha[c] for c in chave_primaria(con, tabela)}


def _inserir_linha(con: sqlite3.Connection, tabela: str, valores: dict) -> int:
    _validar(con, tabela, valores)
    colunas = ", ".join(valores)
    marcadores = ", ".join("?" for _ in valores)
    return con.execute(f"INSERT INTO {tabela} ({colunas}) VALUES ({marcadores})", list(valores.values())).lastrowid


def _atualizar_linha(con: sqlite3.Connection, tabela: str, chave: dict, valores: dict) -> None:
    _validar(con, tabela, valores)
    filtro, params = _where(chave)
    atribuicoes = ", ".join(f"{c} = ?" for c in valores)
    con.execute(f"UPDATE {tabela} SET {atribuicoes} WHERE {filtro}", [*valores.values(), *params])


def _registrar_dependentes(op: Operacao, tabela: str, linha: dict, visitados: set | None = None) -> None:
    """Registra as linhas que o banco vai apagar (CASCADE) ou anular (SET NULL) junto com `linha`.

    Filhos são registrados antes do pai, para que o desfazer (ordem inversa) reinsira o pai primeiro.
    Uma linha alcançável por dois caminhos (ex.: tópico via unidade_id e via pai_id) é registrada uma única vez,
    na primeira visita em pós-ordem — senão o desfazer reinseriria um filho antes do pai.
    """
    con = op.con
    if visitados is None:
        visitados = set()
    for filha in sorted(TABELAS_PERMITIDAS):
        for fk in con.execute(f"PRAGMA foreign_key_list({filha})").fetchall():
            if fk["table"] != tabela or fk["on_delete"] not in ("CASCADE", "SET NULL"):
                continue
            filhos = con.execute(f"SELECT * FROM {filha} WHERE {fk['from']} = ?", (linha[fk["to"]],)).fetchall()
            for filho in map(dict, filhos):
                chave = _chave_da_linha(con, filha, filho)
                marca = (filha, tuple(sorted(chave.items())))
                if marca in visitados:
                    continue
                visitados.add(marca)
                if fk["on_delete"] == "CASCADE":
                    _registrar_dependentes(op, filha, filho, visitados)
                    op.registrar(filha, chave, filho, None)
                else:
                    op.registrar(filha, chave, filho, {**filho, fk["from"]: None})


def _remover_linha(op: Operacao, tabela: str, chave: dict, antes: dict) -> None:
    _registrar_dependentes(op, tabela, antes)
    filtro, params = _where(chave)
    op.con.execute(f"DELETE FROM {tabela} WHERE {filtro}", params)
    op.registrar(tabela, chave, antes, None)


def inserir(op: Operacao, tabela: str, valores: dict) -> int:
    rowid = _inserir_linha(op.con, tabela, valores)
    pk = chave_primaria(op.con, tabela)
    chave = {c: valores.get(c, rowid) for c in pk}
    op.registrar(tabela, chave, None, obter(op.con, tabela, chave))
    return chave[pk[0]] if len(pk) == 1 else rowid


def atualizar(op: Operacao, tabela: str, chave: dict, valores: dict) -> None:
    antes = obter(op.con, tabela, chave)
    if antes is None:
        raise NaoEncontrado(f"{tabela} {chave} não encontrado")
    _atualizar_linha(op.con, tabela, chave, valores)
    op.registrar(tabela, chave, antes, obter(op.con, tabela, chave))


def remover(op: Operacao, tabela: str, chave: dict) -> None:
    antes = obter(op.con, tabela, chave)
    if antes is None:
        raise NaoEncontrado(f"{tabela} {chave} não encontrado")
    _remover_linha(op, tabela, chave, antes)


def aplicar_estado(op: Operacao, tabela: str, chave: dict, alvo: dict | None) -> None:
    """Leva a linha `chave` ao estado `alvo` (None = inexistente), registrando a mudança. Usado pelo desfazer."""
    atual = obter(op.con, tabela, chave)
    if alvo is None:
        if atual is not None:
            _remover_linha(op, tabela, chave, atual)
        return
    if atual is None:
        _inserir_linha(op.con, tabela, alvo)
    else:
        _atualizar_linha(op.con, tabela, chave, {k: v for k, v in alvo.items() if k not in chave})
    op.registrar(tabela, chave, atual, obter(op.con, tabela, chave))
