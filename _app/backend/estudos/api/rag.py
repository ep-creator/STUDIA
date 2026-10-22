"""Rotas da busca: sincroniza o índice (barato quando nada mudou) e consulta com filtros exatos."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from estudos.api.deps import Contexto, contexto_dep
from estudos.erros import NaoEncontrado
from estudos.rag.busca import buscar, secao_completa
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["busca"])


@router.get("/busca")
def busca(
    q: str = "",
    unidade: int | None = None,
    secao_id: int | None = None,
    tipo: list[str] | None = Query(None),
    limite: int = 8,
    ctx: Contexto = Depends(contexto_dep),
) -> dict:
    resumo = sincronizar(ctx.con, ctx.materia.pasta)
    indice = abrir_indice(ctx.materia.pasta)
    try:
        resultados = buscar(indice, q, unidade=unidade, secao_id=secao_id, tipos=tipo, limite=limite)
    finally:
        indice.close()
    return {"resultados": [asdict(r) for r in resultados], "sincronizacao": asdict(resumo)}


@router.post("/busca/sincronizar")
def sincronizar_indice(ctx: Contexto = Depends(contexto_dep)) -> dict:
    return asdict(sincronizar(ctx.con, ctx.materia.pasta))


@router.get("/secoes/{secao_id}/texto")
def texto_da_secao(secao_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    secao = ctx.con.execute("SELECT id, codigo, titulo FROM secao_livro WHERE id = ?", (secao_id,)).fetchone()
    if secao is None:
        raise NaoEncontrado(f"Seção {secao_id} não encontrada")
    sincronizar(ctx.con, ctx.materia.pasta)
    indice = abrir_indice(ctx.materia.pasta)
    try:
        texto = secao_completa(indice, secao_id)
    finally:
        indice.close()
    return {"secao_id": secao["id"], "codigo": secao["codigo"], "titulo": secao["titulo"], "texto": texto}
