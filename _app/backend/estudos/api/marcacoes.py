from dataclasses import asdict

from fastapi import APIRouter, Depends

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.esquemas import MarcacaoDefinir
from estudos.api.respostas import Marcado
from estudos.erros import NaoEncontrado
from estudos.repos import marcacoes

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["marcações"])

_ROTULO_ESTADO = {"ok": "acertei", "err": "errei", "dub": "dúvida", None: "sem marcação"}


@router.put("/marcacoes/{questao_id}")
def definir(questao_id: int, corpo: MarcacaoDefinir, ctx: Contexto = Depends(contexto_dep)) -> Marcado:
    questao = ctx.con.execute(
        "SELECT q.rotulo, l.codigo, l.unidade_id FROM questao q JOIN lista l ON l.id = q.lista_id WHERE q.id = ?",
        (questao_id,),
    ).fetchone()
    if questao is None:
        raise NaoEncontrado(f"Questão {questao_id} não encontrada")
    descricao = f"Marcar questão {questao['codigo']} #{questao['rotulo']} como {_ROTULO_ESTADO[corpo.estado]}"
    with ctx.acao(descricao) as op:
        marcacoes.definir(op, questao_id, corpo.estado)
    return {"placar": asdict(marcacoes.placar(ctx.con, questao["unidade_id"]))}
