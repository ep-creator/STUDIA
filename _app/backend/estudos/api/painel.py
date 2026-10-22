"""Tudo que a tela da unidade precisa numa chamada (sem o corpo dos documentos, buscado sob demanda)."""

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Depends

from estudos import resumo
from estudos.api.deps import Contexto, contexto_dep
from estudos.erros import NaoEncontrado
from estudos.repos import cronograma, documentos, eventos, formulas, listas, marcacoes, materia, topicos, unidades

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
        "eventos": _eventos(con, exibida.id if exibida else None),
        "vinculos": {"topicos": {}, "listas": {}},
        "importacoes_pendentes": resumo.importacoes_pendentes(con),
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
        "vinculos": resumo.vinculos(con, exibida.id),
    })
    return resposta


def _eventos(con, unidade_id: int | None) -> list[dict]:
    """Eventos da unidade exibida mais os gerais (segunda chamada, exame final), em ordem de data e hora."""
    selecionados = [e for e in eventos.listar(con) if e.unidade_id is None or e.unidade_id == unidade_id]
    return [asdict(e) for e in sorted(selecionados, key=lambda e: (e.data, e.hora_inicio or ""))]
