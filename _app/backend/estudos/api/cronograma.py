from fastapi import APIRouter, Depends

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.esquemas import SessaoCriar, SessaoEditar
from estudos.api.respostas import Criado, Ok
from estudos.erros import NaoEncontrado
from estudos.repos import _base, cronograma

router = APIRouter(prefix="/api/materias/{materia_uid}/sessoes", tags=["cronograma"])


def _codigo(ctx: Contexto, sessao_id: int) -> str:
    linha = _base.obter(ctx.con, "sessao_estudo", {"id": sessao_id})
    if linha is None:
        raise NaoEncontrado(f"Sessão {sessao_id} não encontrada")
    return linha["codigo"]


@router.post("")
def criar(corpo: SessaoCriar, ctx: Contexto = Depends(contexto_dep)) -> Criado:
    with ctx.acao(f"Adicionar sessão {corpo.codigo} ao cronograma") as op:
        return {"id": cronograma.criar_sessao(op, **corpo.model_dump())}


@router.patch("/{sessao_id}")
def editar(sessao_id: int, corpo: SessaoEditar, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    campos = corpo.campos()
    codigo = _codigo(ctx, sessao_id)
    if set(campos) == {"feito"}:
        descricao = f"Marcar sessão {codigo} como {'feita' if campos['feito'] else 'pendente'}"
    else:
        descricao = f"Editar sessão {codigo}"
    with ctx.acao(descricao) as op:
        cronograma.atualizar(op, sessao_id, **campos)
    return {"ok": True}


@router.put("/{sessao_id}/questoes")
def definir_questoes(sessao_id: int, corpo: list[int], ctx: Contexto = Depends(contexto_dep)) -> Ok:
    with ctx.acao(f"Definir exercícios da sessão {_codigo(ctx, sessao_id)}") as op:
        cronograma.vincular_questoes(op, sessao_id, corpo)
    return {"ok": True}


@router.delete("/{sessao_id}")
def remover(sessao_id: int, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    with ctx.acao(f"Remover sessão {_codigo(ctx, sessao_id)}") as op:
        cronograma.remover(op, sessao_id)
    return {"ok": True}
