from fastapi import APIRouter, Depends

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.esquemas import ListaCriar, ListaEditar, QuestaoEsquema
from estudos.api.respostas import Criado, Ok
from estudos.modelos import QuestaoEntrada
from estudos.repos import listas

router = APIRouter(prefix="/api/materias/{materia_uid}/listas", tags=["listas"])


@router.post("")
def criar(corpo: ListaCriar, ctx: Contexto = Depends(contexto_dep)) -> Criado:
    with ctx.acao(f"Criar lista {corpo.codigo}") as op:
        return {"id": listas.criar(op, **corpo.model_dump())}


@router.patch("/{lista_id}")
def editar(lista_id: int, corpo: ListaEditar, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    codigo = listas.obter(ctx.con, lista_id).codigo
    with ctx.acao(f"Editar lista {codigo}") as op:
        listas.atualizar(op, lista_id, **corpo.campos())
    return {"ok": True}


@router.put("/{lista_id}/questoes")
def definir_questoes(lista_id: int, corpo: list[QuestaoEsquema], ctx: Contexto = Depends(contexto_dep)) -> dict[str, int]:
    codigo = listas.obter(ctx.con, lista_id).codigo
    with ctx.acao(f"Atualizar questões da lista {codigo}") as op:
        return listas.sincronizar_questoes(op, lista_id, [QuestaoEntrada(**q.model_dump()) for q in corpo])


@router.post("/{lista_id}/topicos/{topico_id}")
def vincular_topico(lista_id: int, topico_id: int, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    codigo = listas.obter(ctx.con, lista_id).codigo
    with ctx.acao(f"Vincular tópico à lista {codigo}") as op:
        listas.vincular_topico(op, lista_id, topico_id)
    return {"ok": True}


@router.delete("/{lista_id}")
def remover(lista_id: int, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    codigo = listas.obter(ctx.con, lista_id).codigo
    with ctx.acao(f"Remover lista {codigo}") as op:
        listas.remover(op, lista_id)
    return {"ok": True}
