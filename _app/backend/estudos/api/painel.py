"""Tudo que a tela da unidade precisa numa chamada (sem o corpo dos documentos, buscado sob demanda)."""

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Depends

from estudos.api.deps import Contexto, contexto_dep
from estudos.erros import NaoEncontrado
from estudos.repos import cronograma, documentos, formulas, listas, marcacoes, materia, topicos, unidades

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["painel"])


@router.get("/painel")
def painel(unidade: int | None = None, ctx: Contexto = Depends(contexto_dep)) -> dict:
    con = ctx.con
    todas = unidades.listar(con)
    atual = unidades.unidade_atual(con, date.today())
    if unidade is None:
        exibida = atual
    else:
        exibida = next((u for u in todas if u.numero == unidade), None)
        if exibida is None:
            raise NaoEncontrado(f"Unidade {unidade} não existe nesta matéria")

    resposta = {
        "materia": asdict(materia.obter(con)),
        "unidades": [asdict(u) for u in todas],
        "unidade_atual": atual.numero if atual else None,
        "unidade": exibida.numero if exibida else None,
        "topicos": [], "listas": [], "marcacoes": {}, "sessoes": [], "formulas": [], "documentos": [],
        "placar": None,
    }
    if exibida is None:
        return resposta
    resposta.update({
        "topicos": [asdict(t) for t in topicos.listar(con, exibida.id)],
        "listas": [
            {**asdict(l), "questoes": [asdict(q) for q in listas.listar_questoes(con, l.id)]}
            for l in listas.listar(con, exibida.id)
        ],
        "marcacoes": {str(k): v for k, v in marcacoes.estados(con, exibida.id).items()},
        "sessoes": [asdict(s) for s in cronograma.listar(con, exibida.id)],
        "formulas": [asdict(f) for f in formulas.listar(con, exibida.id)],
        "documentos": [asdict(d) for d in documentos.listar(con, unidade_id=exibida.id)],
        "placar": asdict(marcacoes.placar(con, exibida.id)),
    })
    return resposta
