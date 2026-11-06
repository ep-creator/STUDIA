"""A tela Hoje: a sessão em foco com o material, os próximos dias, o que revisar e os tópicos com progresso derivado."""

from datetime import date

from fastapi import APIRouter, Depends

from estudos import progresso
from estudos.api.deps import Contexto, contexto_dep
from estudos.api.respostas import Hoje, Indice, SessaoProgresso, TopicoPagina, TopicoProgresso

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["hoje"])


@router.get("/hoje")
def hoje(data: date | None = None, ctx: Contexto = Depends(contexto_dep)) -> Hoje:
    """`data` só serve para testar e conferir outro dia; sem ela, vale hoje."""
    return progresso.hoje(ctx.con, data or date.today())


@router.get("/progresso")
def progresso_da_unidade(unidade: int, data: date | None = None, ctx: Contexto = Depends(contexto_dep)) -> list[TopicoProgresso]:
    """Tópicos da unidade com o estado e o placar derivados."""
    return progresso.topicos_da_unidade(ctx.con, unidade, data or date.today())


@router.get("/indice")
def indice(ctx: Contexto = Depends(contexto_dep)) -> Indice:
    """Questões e tópicos de todas as unidades (a busca leva a qualquer um, em qualquer unidade)."""
    return progresso.indice(ctx.con)


@router.get("/sessoes/progresso")
def progresso_das_sessoes(unidade: int, data: date | None = None, ctx: Contexto = Depends(contexto_dep)) -> list[SessaoProgresso]:
    """Estado derivado de cada sessão da unidade (o plano completo usa o mesmo que a tela Hoje)."""
    return progresso.sessoes_da_unidade(ctx.con, unidade, data or date.today())


@router.get("/topicos/{topico_id}/pagina")
def pagina_do_topico(topico_id: int, data: date | None = None, ctx: Contexto = Depends(contexto_dep)) -> TopicoPagina:
    return progresso.pagina_topico(ctx.con, topico_id, data or date.today())
