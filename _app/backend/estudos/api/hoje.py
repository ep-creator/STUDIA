"""A tela Hoje: a sessão em foco com o material, os próximos dias, o que revisar e os tópicos com progresso derivado."""

from datetime import date

from fastapi import APIRouter, Depends

from estudos import progresso
from estudos.api.deps import Contexto, contexto_dep
from estudos.api.respostas import Hoje

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["hoje"])


@router.get("/hoje")
def hoje(data: date | None = None, ctx: Contexto = Depends(contexto_dep)) -> Hoje:
    """`data` só serve para testar e conferir outro dia; sem ela, vale hoje."""
    return progresso.hoje(ctx.con, data or date.today())
