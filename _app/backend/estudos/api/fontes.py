"""Arquivos da matéria (livros, listas, PDFs) e o sumário de cada livro, para o leitor."""

from dataclasses import asdict

from fastapi import APIRouter, Depends

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.respostas import FonteResumo, SecaoLivro
from estudos.erros import NaoEncontrado
from estudos.repos import _base, fontes, livros

router = APIRouter(prefix="/api/materias/{materia_uid}/fontes", tags=["fontes"])


@router.get("")
def listar(tipo: str | None = None, ctx: Contexto = Depends(contexto_dep)) -> list[FonteResumo]:
    return [
        {"id": f.id, "tipo": f.tipo, "titulo": f.titulo, "caminho": f.caminho, "paginas": f.paginas}
        for f in fontes.listar(ctx.con, tipo)
    ]


@router.get("/{fonte_id}/secoes")
def secoes(fonte_id: int, ctx: Contexto = Depends(contexto_dep)) -> list[SecaoLivro]:
    if _base.obter(ctx.con, "livro", {"fonte_id": fonte_id}) is None:
        raise NaoEncontrado(f"A fonte {fonte_id} não é um livro cadastrado")
    return [asdict(s) for s in livros.listar_secoes(ctx.con, fonte_id)]
