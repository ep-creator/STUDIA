"""Conversas do assistente guardadas na matéria: uma ativa por alvo e papel, com o custo de cada resposta.

Ficam fora do Histórico (escrita direta): são o registro da conversa, não dados de estudo.
"""

import datetime
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from estudos.workspace import ARQUIVO_DB, descobrir_materias

_ESTIMATIVA_PADRAO = 0.05   # R$ por resposta quando ainda não há histórico de custo


@dataclass(frozen=True)
class Conversa:
    id: int
    papel: str
    alvo: str


@dataclass(frozen=True)
class Mensagem:
    id: int
    autor: str
    texto: str
    custo_brl: float
    criada_em: str


@dataclass(frozen=True)
class ResumoConversa:
    id: int
    alvo: str
    papel: str
    rotulo: str
    atualizada_em: str


def _agora() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def conversa_ativa(con: sqlite3.Connection, alvo: str, papel: str) -> Conversa:
    linha = con.execute("SELECT id FROM conversa WHERE alvo = ? AND papel = ? AND ativa = 1 ORDER BY id DESC LIMIT 1",
                        (alvo, papel)).fetchone()
    if linha is None:
        cid = con.execute("INSERT INTO conversa (papel, alvo, ativa, criada_em) VALUES (?, ?, 1, ?)",
                          (papel, alvo, _agora())).lastrowid
        return Conversa(cid, papel, alvo)
    return Conversa(linha["id"], papel, alvo)


def recomecar(con: sqlite3.Connection, alvo: str, papel: str) -> Conversa:
    """Arquiva a conversa ativa (as mensagens ficam) e abre outra vazia."""
    con.execute("UPDATE conversa SET ativa = 0 WHERE alvo = ? AND papel = ? AND ativa = 1", (alvo, papel))
    return conversa_ativa(con, alvo, papel)


def mensagens(con: sqlite3.Connection, conversa_id: int) -> list[Mensagem]:
    return [Mensagem(l["id"], l["autor"], l["texto"], l["custo_brl"], l["criada_em"]) for l in con.execute(
        "SELECT id, autor, texto, custo_brl, criada_em FROM mensagem WHERE conversa_id = ? ORDER BY id", (conversa_id,))]


def adicionar(
    con: sqlite3.Connection, conversa_id: int, autor: str, texto: str, tokens_entrada: int = 0, tokens_saida: int = 0,
    custo_brl: float = 0.0, modelo: str | None = None,
) -> int:
    return con.execute(
        "INSERT INTO mensagem (conversa_id, autor, texto, tokens_entrada, tokens_saida, custo_brl, modelo, criada_em) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (conversa_id, autor, texto, tokens_entrada, tokens_saida, custo_brl, modelo, _agora())).lastrowid


def _por_materia(workspace: Path, sql: str, params: tuple) -> list:
    valores = []
    for m in descobrir_materias(workspace):
        try:
            with closing(sqlite3.connect(f"{(m.pasta / ARQUIVO_DB).resolve().as_uri()}?mode=ro", uri=True)) as con:
                valores += [r[0] for r in con.execute(sql, params)]
        except sqlite3.DatabaseError:  # matéria sem as tabelas do agente (ainda não aberta nesta versão)
            continue
    return valores


def total_do_mes(workspace: Path, hoje: datetime.date) -> float:
    """Gasto do mês somando todas as matérias do workspace (o teto é do usuário, não da matéria)."""
    inicio = hoje.replace(day=1).isoformat()
    return round(sum(v or 0 for v in _por_materia(
        workspace, "SELECT sum(custo_brl) FROM mensagem WHERE criada_em >= ?", (inicio,))), 4)


def estimativa(workspace: Path) -> float:
    """Quanto uma resposta deve custar: o maior custo entre as 10 últimas respostas (o teto erra para o lado seguro)."""
    recentes = _por_materia(workspace, "SELECT custo_brl FROM mensagem WHERE autor = 'agente' AND custo_brl > 0 "
                                        "ORDER BY criada_em DESC, id DESC LIMIT 10", ())
    return max(recentes) if recentes else _ESTIMATIVA_PADRAO


def _rotulo(con: sqlite3.Connection, alvo: str) -> str:
    """Nome curto do alvo para a lista de conversas; alvo apagado fica com o próprio alvo."""
    if alvo == "geral":
        return "Geral"
    tipo, _, ident = alvo.partition(":")
    if tipo == "questao" and ident.isdigit():
        l = con.execute("SELECT l.codigo, q.rotulo FROM questao q JOIN lista l ON l.id = q.lista_id WHERE q.id = ?",
                        (int(ident),)).fetchone()
        if l:
            return f"{l['codigo']} #{l['rotulo']}"
    if tipo == "secao" and ident.isdigit():
        l = con.execute("SELECT codigo, titulo FROM secao_livro WHERE id = ?", (int(ident),)).fetchone()
        if l:
            return f"{l['codigo']} {l['titulo']}"
    return alvo


def ativas(con: sqlite3.Connection) -> list[ResumoConversa]:
    """Conversas ativas que já têm mensagem, da usada mais recentemente para a mais antiga."""
    linhas = con.execute(
        "SELECT c.id, c.alvo, c.papel, MAX(m.criada_em) AS ultima FROM conversa c JOIN mensagem m ON m.conversa_id = c.id "
        "WHERE c.ativa = 1 GROUP BY c.id ORDER BY ultima DESC, c.id DESC").fetchall()
    return [ResumoConversa(l["id"], l["alvo"], l["papel"], _rotulo(con, l["alvo"]), l["ultima"]) for l in linhas]
