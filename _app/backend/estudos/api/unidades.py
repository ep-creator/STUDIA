from fastapi import APIRouter, Depends

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.esquemas import EventoCriar, UnidadeCriar, UnidadeEditar
from estudos.repos import eventos, unidades

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["unidades"])


@router.post("/unidades")
def criar(corpo: UnidadeCriar, ctx: Contexto = Depends(contexto_dep)) -> dict:
    with ctx.acao(f"Criar unidade {corpo.numero}") as op:
        return {"id": unidades.criar(op, corpo.numero, corpo.titulo)}


@router.patch("/unidades/{unidade_id}")
def editar(unidade_id: int, corpo: UnidadeEditar, ctx: Contexto = Depends(contexto_dep)) -> dict:
    numero = unidades.obter(ctx.con, unidade_id).numero
    with ctx.acao(f"Editar unidade {numero}") as op:
        unidades.atualizar(op, unidade_id, **corpo.campos())
    return {"ok": True}


@router.delete("/unidades/{unidade_id}")
def remover(unidade_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    numero = unidades.obter(ctx.con, unidade_id).numero
    with ctx.acao(f"Remover unidade {numero}") as op:
        unidades.remover(op, unidade_id)
    return {"ok": True}


@router.post("/eventos")
def criar_evento(corpo: EventoCriar, ctx: Contexto = Depends(contexto_dep)) -> dict:
    with ctx.acao(f"Adicionar {corpo.tipo} em {corpo.data}") as op:
        return {"id": eventos.criar(op, **corpo.model_dump())}


@router.delete("/eventos/{evento_id}")
def remover_evento(evento_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    with ctx.acao("Remover evento do calendário") as op:
        eventos.remover(op, evento_id)
    return {"ok": True}
