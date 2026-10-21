import dataclasses
import sqlite3

from estudos.erros import DadoInvalido, NaoEncontrado
from estudos.historico import Operacao
from estudos.modelos import LIBERACOES, LINHAS, ORIGENS, Lista, Questao, QuestaoEntrada, exigir_opcao
from estudos.repos import _base

# Regra da spec §5: manual tem precedência; em 'auto', abre quando algum tópico coberto já foi visto
# (direto por lista_topico ou via seção do livro ligada ao tópico).
SQL_ABERTA = """
    CASE l.liberacao
        WHEN 'aberta' THEN 1
        WHEN 'travada' THEN 0
        ELSE EXISTS (
            SELECT 1 FROM lista_topico lt JOIN topico t ON t.id = lt.topico_id
            WHERE lt.lista_id = l.id AND t.status = 'visto'
        ) OR EXISTS (
            SELECT 1 FROM lista_secao ls
            JOIN topico_secao ts ON ts.secao_id = ls.secao_id
            JOIN topico t ON t.id = ts.topico_id
            WHERE ls.lista_id = l.id AND t.status = 'visto'
        )
    END
"""
_SELECT = f"SELECT l.id, l.codigo, l.titulo, l.unidade_id, l.fonte_id, l.liberacao, l.ordem, l.origem, ({SQL_ABERTA}) AS aberta FROM lista l"
_CAMPOS_QUESTAO = ("linha", "enunciado_md", "expressao", "pagina_pdf", "figura", "chave_legada")


def _lista(linha: sqlite3.Row) -> Lista:
    return Lista(**{**dict(linha), "aberta": bool(linha["aberta"])})


def criar(
    op: Operacao,
    codigo: str,
    titulo: str,
    unidade_id: int,
    liberacao: str = "auto",
    fonte_id: int | None = None,
    origem: str = "manual",
) -> int:
    exigir_opcao(liberacao, LIBERACOES, "liberação")
    exigir_opcao(origem, ORIGENS, "origem")
    ordem = op.con.execute(
        "SELECT coalesce(max(ordem), 0) + 1 FROM lista WHERE unidade_id = ?", (unidade_id,)
    ).fetchone()[0]
    return _base.inserir(op, "lista", {
        "codigo": codigo, "titulo": titulo, "unidade_id": unidade_id, "liberacao": liberacao,
        "fonte_id": fonte_id, "ordem": ordem, "origem": origem,
    })


def listar(con: sqlite3.Connection, unidade_id: int) -> list[Lista]:
    return [_lista(l) for l in con.execute(_SELECT + " WHERE l.unidade_id = ? ORDER BY l.ordem, l.id", (unidade_id,))]


def obter(con: sqlite3.Connection, lista_id: int) -> Lista:
    linha = con.execute(_SELECT + " WHERE l.id = ?", (lista_id,)).fetchone()
    if linha is None:
        raise NaoEncontrado(f"Lista {lista_id} não encontrada")
    return _lista(linha)


def atualizar(op: Operacao, lista_id: int, **campos) -> None:
    if "liberacao" in campos:
        exigir_opcao(campos["liberacao"], LIBERACOES, "liberação")
    _base.atualizar(op, "lista", {"id": lista_id}, campos)


def definir_liberacao(op: Operacao, lista_id: int, liberacao: str) -> None:
    atualizar(op, lista_id, liberacao=liberacao)


def vincular_topico(op: Operacao, lista_id: int, topico_id: int) -> None:
    if _base.obter(op.con, "lista_topico", {"lista_id": lista_id, "topico_id": topico_id}) is None:
        _base.inserir(op, "lista_topico", {"lista_id": lista_id, "topico_id": topico_id})


def vincular_secao(op: Operacao, lista_id: int, secao_id: int) -> None:
    if _base.obter(op.con, "lista_secao", {"lista_id": lista_id, "secao_id": secao_id}) is None:
        _base.inserir(op, "lista_secao", {"lista_id": lista_id, "secao_id": secao_id})


def sincronizar_questoes(op: Operacao, lista_id: int, questoes: list[QuestaoEntrada]) -> dict[str, int]:
    """Deixa a lista com exatamente estas questões, preservando id (e marcação) de cada rótulo que já existia."""
    rotulos = [q.rotulo for q in questoes]
    repetidos = sorted({r for r in rotulos if rotulos.count(r) > 1})
    if repetidos:
        raise DadoInvalido(f"Rótulos repetidos na lista: {repetidos}")
    for q in questoes:
        if q.linha not in LINHAS:
            raise DadoInvalido(f"Linha inválida na questão {q.rotulo}: {q.linha} (use 1 ou 2)")

    existentes = {
        l["rotulo"]: dict(l) for l in op.con.execute("SELECT * FROM questao WHERE lista_id = ?", (lista_id,))
    }
    for rotulo in set(existentes) - set(rotulos):
        _base.remover(op, "questao", {"id": existentes[rotulo]["id"]})

    ids = {}
    for ordem, q in enumerate(questoes, start=1):
        valores = {k: v for k, v in dataclasses.asdict(q).items() if k in _CAMPOS_QUESTAO}
        valores["ordem"] = ordem
        atual = existentes.get(q.rotulo)
        if atual is None:
            ids[q.rotulo] = _base.inserir(op, "questao", {"lista_id": lista_id, "rotulo": q.rotulo, **valores})
            continue
        ids[q.rotulo] = atual["id"]
        mudou = {k: v for k, v in valores.items() if atual[k] != v}
        if mudou:
            _base.atualizar(op, "questao", {"id": atual["id"]}, mudou)
    return ids


def listar_questoes(con: sqlite3.Connection, lista_id: int) -> list[Questao]:
    return [
        Questao(**{k: l[k] for k in Questao.__dataclass_fields__})
        for l in con.execute("SELECT * FROM questao WHERE lista_id = ? ORDER BY ordem, id", (lista_id,))
    ]


def remover(op: Operacao, lista_id: int) -> None:
    _base.remover(op, "lista", {"id": lista_id})
