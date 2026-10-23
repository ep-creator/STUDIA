from fastapi import APIRouter, Depends

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.esquemas import FormulaCriar, FormulaEditar
from estudos.api.respostas import Criado, Ok
from estudos.erros import NaoEncontrado
from estudos.repos import _base, formulas

router = APIRouter(prefix="/api/materias/{materia_uid}/formulas", tags=["formulário"])


def _titulo(ctx: Contexto, formula_id: int) -> str:
    linha = _base.obter(ctx.con, "formula", {"id": formula_id})
    if linha is None:
        raise NaoEncontrado(f"Fórmula {formula_id} não encontrada")
    return linha["titulo"]


@router.post("")
def criar(corpo: FormulaCriar, ctx: Contexto = Depends(contexto_dep)) -> Criado:
    with ctx.acao(f"Adicionar fórmula '{corpo.titulo}'") as op:
        return {"id": formulas.criar(op, **corpo.model_dump())}


@router.patch("/{formula_id}")
def editar(formula_id: int, corpo: FormulaEditar, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    with ctx.acao(f"Editar fórmula '{_titulo(ctx, formula_id)}'") as op:
        formulas.atualizar(op, formula_id, **corpo.campos())
    return {"ok": True}


@router.delete("/{formula_id}")
def remover(formula_id: int, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    with ctx.acao(f"Remover fórmula '{_titulo(ctx, formula_id)}'") as op:
        formulas.remover(op, formula_id)
    return {"ok": True}
