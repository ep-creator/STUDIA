from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from estudos.api.deps import Contexto, contexto_dep, materia_dep
from estudos.api.esquemas import DocumentoSalvar
from estudos.erros import NaoEncontrado
from estudos.repos import documentos
from estudos.seguranca import caminho_seguro
from estudos.workspace import MateriaRef

router = APIRouter(tags=["documentos"])
_PREFIXO = "/api/materias/{materia_uid}/documentos"


@router.get(_PREFIXO)
def listar(tipo: str | None = None, unidade_id: int | None = None, ctx: Contexto = Depends(contexto_dep)) -> list[dict]:
    return [asdict(d) for d in documentos.listar(ctx.con, tipo, unidade_id)]


@router.get(_PREFIXO + "/{documento_id}")
def obter(documento_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    documento = documentos.obter(ctx.con, documento_id)
    return {**asdict(documento), "corpo": documentos.ler_corpo(ctx.materia.pasta, documento)}


@router.put(_PREFIXO)
def salvar(corpo: DocumentoSalvar, ctx: Contexto = Depends(contexto_dep)) -> dict:
    with ctx.acao(f"Salvar {corpo.tipo} '{corpo.titulo}'") as op:
        return {"id": documentos.salvar(op, **corpo.model_dump())}


@router.delete(_PREFIXO + "/{documento_id}")
def remover(documento_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    titulo = documentos.obter(ctx.con, documento_id).titulo
    with ctx.acao(f"Remover documento '{titulo}'") as op:
        documentos.remover(op, documento_id)
    return {"ok": True}


@router.get("/arquivos/{materia_uid}/{caminho:path}")
def arquivo(caminho: str, materia: MateriaRef = Depends(materia_dep)) -> FileResponse:
    alvo = caminho_seguro(materia.pasta, caminho)
    if not alvo.is_file():
        raise NaoEncontrado(f"Arquivo não encontrado: {caminho}")
    return FileResponse(alvo)
