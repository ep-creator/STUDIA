from fastapi import APIRouter, Depends

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.esquemas import TopicoCriar, TopicoEditar
from estudos.erros import NaoEncontrado
from estudos.repos import _base, topicos

router = APIRouter(prefix="/api/materias/{materia_uid}/topicos", tags=["tópicos"])


def _titulo(ctx: Contexto, topico_id: int) -> str:
    linha = _base.obter(ctx.con, "topico", {"id": topico_id})
    if linha is None:
        raise NaoEncontrado(f"Tópico {topico_id} não encontrado")
    return linha["titulo"]


@router.post("")
def criar(corpo: TopicoCriar, ctx: Contexto = Depends(contexto_dep)) -> dict:
    with ctx.acao(f"Adicionar tópico '{corpo.titulo}'") as op:
        return {"id": topicos.criar(op, **corpo.model_dump())}


@router.patch("/{topico_id}")
def editar(topico_id: int, corpo: TopicoEditar, ctx: Contexto = Depends(contexto_dep)) -> dict:
    campos = corpo.campos()
    titulo = _titulo(ctx, topico_id)
    descricao = (
        f"Marcar tópico '{titulo}' como {campos['status']}" if set(campos) == {"status"} else f"Editar tópico '{titulo}'"
    )
    with ctx.acao(descricao) as op:
        topicos.atualizar(op, topico_id, **campos)
    return {"ok": True}


@router.delete("/{topico_id}")
def remover(topico_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    with ctx.acao(f"Remover tópico '{_titulo(ctx, topico_id)}'") as op:
        topicos.remover(op, topico_id)
    return {"ok": True}
