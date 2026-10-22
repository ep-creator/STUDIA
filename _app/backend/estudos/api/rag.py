"""Rotas da busca: sincroniza o índice (barato quando nada mudou) e consulta com filtros exatos."""

import sqlite3
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.respostas import ResultadoBusca, ResumoSincronizacao, TextoSecao
from estudos.erros import NaoEncontrado
from estudos.rag.busca import buscar, secao_completa
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice, descartar_indice, eh_corrupcao

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["busca"])


@router.get("/busca")
def busca(
    q: str = "",
    unidade: int | None = None,
    secao_id: int | None = None,
    tipo: list[str] | None = Query(None),
    limite: int = 8,
    ctx: Contexto = Depends(contexto_dep),
) -> ResultadoBusca:
    resumo = sincronizar(ctx.con, ctx.materia.pasta, esperar=False)
    resultados = _com_indice(ctx, lambda indice: buscar(indice, q, unidade=unidade, secao_id=secao_id, tipos=tipo, limite=limite))
    return {"resultados": [asdict(r) for r in resultados], "sincronizacao": asdict(resumo)}


def _com_indice(ctx: Contexto, consulta):
    """Executa a consulta; índice corrompido é descartado e refeito uma vez (é sempre reconstruível)."""
    for tentativa in (1, 2):
        indice = abrir_indice(ctx.materia.pasta)
        try:
            return consulta(indice)
        except sqlite3.DatabaseError as erro:
            if tentativa == 2 or not eh_corrupcao(erro):
                raise
        finally:
            indice.close()
        descartar_indice(ctx.materia.pasta)
        sincronizar(ctx.con, ctx.materia.pasta)


@router.post("/busca/sincronizar")
def sincronizar_indice(ctx: Contexto = Depends(contexto_dep)) -> ResumoSincronizacao:
    return asdict(sincronizar(ctx.con, ctx.materia.pasta))


@router.get("/secoes/{secao_id}/texto")
def texto_da_secao(secao_id: int, ctx: Contexto = Depends(contexto_dep)) -> TextoSecao:
    secao = ctx.con.execute("SELECT id, codigo, titulo FROM secao_livro WHERE id = ?", (secao_id,)).fetchone()
    if secao is None:
        raise NaoEncontrado(f"Seção {secao_id} não encontrada")
    sincronizar(ctx.con, ctx.materia.pasta, esperar=False)
    texto = _com_indice(ctx, lambda indice: secao_completa(indice, secao_id))
    return {"secao_id": secao["id"], "codigo": secao["codigo"], "titulo": secao["titulo"], "texto": texto}
