from dataclasses import asdict

from fastapi import APIRouter, Depends

from estudos import historico
from estudos.api.deps import Contexto, contexto_dep

router = APIRouter(prefix="/api/materias/{materia_uid}/historico", tags=["histórico"])


@router.get("")
def listar(limite: int = 50, ctx: Contexto = Depends(contexto_dep)) -> list[dict]:
    return [asdict(g) for g in historico.listar(ctx.con, limite)]


@router.get("/{grupo_id}")
def detalhar(grupo_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    detalhe = historico.detalhar(ctx.con, ctx.materia.pasta, grupo_id)
    return {**detalhe, "grupo": asdict(detalhe["grupo"])}


@router.post("/desfazer")
def desfazer(ctx: Contexto = Depends(contexto_dep)) -> dict:
    grupo = historico.desfazer_ultimo(ctx.con, ctx.materia.pasta)
    return {"desfeito": asdict(grupo) if grupo else None}
