"""Rotas da busca: sincroniza o índice (barato quando nada mudou) e consulta com filtros exatos."""

import sqlite3
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.respostas import ResultadoBusca, ResumoSincronizacao, TextoSecao
from estudos.erros import NaoEncontrado
from estudos.ia.embeddings import obter_embeddings
from estudos.rag.busca import buscar_modo, secao_completa
from estudos.rag.indexador import agendar_sincronizacao, sincronizar
from estudos.rag.indice import abrir_indice, descartar_indice, eh_corrupcao
from estudos.workspace import ARQUIVO_DB

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["busca"])


@router.get("/busca")
def busca(
    q: str = "",
    unidade: int | None = None,
    secao_id: int | None = None,
    tipo: list[str] | None = Query(None),
    limite: int = 8,
    modo: str | None = None,
    ctx: Contexto = Depends(contexto_dep),
) -> ResultadoBusca:
    """modo: "texto", "vetor" ou "hibrida" (padrão: o do config). Sem embeddings disponíveis, a busca é por texto e a
    resposta diz o modo efetivamente usado."""
    embeddings = obter_embeddings(ctx.settings)
    resumo = sincronizar(ctx.con, ctx.materia.pasta, esperar=False)
    if embeddings is not None and _faltam_vetores(ctx):
        # gerar os vetores leva minutos na primeira vez: vai para segundo plano e a busca segue com o que já existe
        agendar_sincronizacao(ctx.materia.pasta, ctx.materia.pasta / ARQUIVO_DB, embeddings=embeddings)
        resumo.avisos.append("vetores da busca por sentido em andamento; por enquanto parte da busca é só por texto")
    efetivo, resultados = _com_indice(ctx, lambda indice: buscar_modo(
        indice, q, unidade=unidade, secao_id=secao_id, tipos=tipo, limite=limite, modo=modo or ctx.settings.busca,
        embeddings=embeddings))
    return {"resultados": [asdict(r) for r in resultados], "sincronizacao": asdict(resumo), "modo": efetivo}


def _faltam_vetores(ctx: Contexto) -> bool:
    indice = abrir_indice(ctx.materia.pasta)
    try:
        return indice.execute("SELECT 1 FROM trecho WHERE vetor IS NULL LIMIT 1").fetchone() is not None
    finally:
        indice.close()


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
