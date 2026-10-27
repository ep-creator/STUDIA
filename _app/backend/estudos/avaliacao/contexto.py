"""Cobertura do contexto inicial do assistente: para cada pergunta de questão do gabarito, a resposta aceita já vem no
contexto que o app monta para a questão (sem o modelo precisar buscar)? Não chama a API.
"""

import re
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from estudos.agente.contexto import montar_contexto
from estudos.avaliacao.busca import _ESTILOS_DE_QUESTAO, _enunciado, _nomes
from estudos.avaliacao.gabarito import PerguntaBusca
from estudos.avaliacao.respostas import casa, ler_aceita
from estudos.importacao.idioma import sem_acento
from estudos.rag.indexador import sincronizar

_PREFIXO = 60


@dataclass(frozen=True)
class LinhaContexto:
    total: int                     # perguntas de questão que acharam a questão no banco
    achadas: int                   # dessas, quantas têm uma resposta aceita no contexto inicial
    por_estilo: dict[str, float]


def _normal(texto: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", sem_acento(texto or "").lower()).split())[:_PREFIXO]


def _questao_do_enunciado(con: sqlite3.Connection, enunciado: str) -> int | None:
    alvo = _normal(enunciado)
    if not alvo:
        return None
    for linha in con.execute("SELECT id, enunciado_md FROM questao WHERE enunciado_md != ''"):
        if _normal(linha["enunciado_md"]) == alvo:
            return linha["id"]
    return None


def _como_resultado(p):
    return SimpleNamespace(secao_codigo=p.secao_codigo, documento_id=p.documento_id, fonte_id=p.fonte_id, titulo=p.titulo,
                           pagina=p.pagina, pagina_fim=p.pagina_fim)


def cobertura_do_contexto(con: sqlite3.Connection, raiz: Path, perguntas: list[PerguntaBusca]) -> LinhaContexto:
    """Usa um índice temporário (o da matéria não é tocado), como a avaliação da busca."""
    with tempfile.TemporaryDirectory() as temp:
        caminho = Path(temp) / "indice.db"
        sincronizar(con, raiz, caminho_indice_=caminho)
        return _cobertura(con, raiz, perguntas, caminho)


def _cobertura(con: sqlite3.Connection, raiz: Path, perguntas: list[PerguntaBusca], caminho: Path) -> LinhaContexto:
    fontes, documentos = _nomes(con)
    por_estilo: dict[str, list[bool]] = {}
    for p in perguntas:
        if p.estilo not in _ESTILOS_DE_QUESTAO:
            continue
        questao_id = _questao_do_enunciado(con, _enunciado(p))
        if questao_id is None:
            continue
        pedacos = [_como_resultado(x) for x in montar_contexto(con, raiz, f"questao:{questao_id}", "tutor", caminho)]
        aceitas = [ler_aceita(a) for a in p.aceitas]
        por_estilo.setdefault(p.estilo, []).append(any(casa(fontes, documentos, r, a, trecho=False)
                                                       for r in pedacos for a in aceitas))
    todos = [v for vs in por_estilo.values() for v in vs]
    return LinhaContexto(len(todos), sum(todos), {e: sum(vs) / len(vs) for e, vs in por_estilo.items()})
