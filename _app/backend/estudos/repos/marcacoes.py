import datetime
import sqlite3

from estudos.historico import Operacao
from estudos.modelos import ESTADOS_MARCACAO, Placar, exigir_opcao
from estudos.repos import _base
from estudos.repos.listas import SQL_ABERTA


def definir(op: Operacao, questao_id: int, estado: str | None) -> None:
    chave = {"questao_id": questao_id}
    atual = _base.obter(op.con, "marcacao", chave)
    if estado is None:
        if atual is not None:
            _base.remover(op, "marcacao", chave)
        return
    exigir_opcao(estado, ESTADOS_MARCACAO, "estado")
    valores = {"estado": estado, "atualizado_em": datetime.datetime.now().isoformat(timespec="seconds")}
    if atual is None:
        _base.inserir(op, "marcacao", {**chave, **valores})
    else:
        _base.atualizar(op, "marcacao", chave, valores)


def estados(con: sqlite3.Connection, unidade_id: int) -> dict[int, str]:
    return {
        l["questao_id"]: l["estado"]
        for l in con.execute(
            "SELECT m.questao_id, m.estado FROM marcacao m JOIN questao q ON q.id = m.questao_id"
            " JOIN lista l ON l.id = q.lista_id WHERE l.unidade_id = ?",
            (unidade_id,),
        )
    }


def placar(con: sqlite3.Connection, unidade_id: int) -> Placar:
    """Contagem das questões das listas abertas da unidade. Taxa de acerto = ok/(ok+err); dúvidas ficam de fora."""
    linhas = con.execute(
        f"SELECT q.linha, m.estado FROM questao q JOIN lista l ON l.id = q.lista_id"
        f" LEFT JOIN marcacao m ON m.questao_id = q.id WHERE l.unidade_id = ? AND ({SQL_ABERTA})",
        (unidade_id,),
    ).fetchall()
    conta = {e: sum(1 for l in linhas if l["estado"] == e) for e in ESTADOS_MARCACAO}
    por_linha = {
        n: (sum(1 for l in linhas if l["linha"] == n and l["estado"]), sum(1 for l in linhas if l["linha"] == n))
        for n in (1, 2)
    }
    corrigidos = conta["ok"] + conta["err"]
    return Placar(
        ok=conta["ok"], err=conta["err"], dub=conta["dub"], total=len(linhas),
        feitos_linha1=por_linha[1][0], total_linha1=por_linha[1][1],
        feitos_linha2=por_linha[2][0], total_linha2=por_linha[2][1],
        taxa_acerto=conta["ok"] / corrigidos if corrigidos else None,
    )
