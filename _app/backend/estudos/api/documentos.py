from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from estudos.api.deps import Contexto, contexto_dep, materia_dep
from estudos.api.esquemas import DocumentoSalvar
from estudos.api.respostas import Criado, Documento, DocumentoComCorpo, Ok
from estudos.erros import Conflito, NaoEncontrado
from estudos.repos import documentos
from estudos.seguranca import caminho_seguro
from estudos.workspace import MateriaRef

router = APIRouter(tags=["documentos"])
_PREFIXO = "/api/materias/{materia_uid}/documentos"


@router.get(_PREFIXO)
def listar(tipo: str | None = None, unidade_id: int | None = None, ctx: Contexto = Depends(contexto_dep)) -> list[Documento]:
    return [asdict(d) for d in documentos.listar(ctx.con, tipo, unidade_id)]


@router.get(_PREFIXO + "/{documento_id}")
def obter(documento_id: int, ctx: Contexto = Depends(contexto_dep)) -> DocumentoComCorpo:
    documento = documentos.obter(ctx.con, documento_id)
    return {
        **asdict(documento), "corpo": documentos.ler_corpo(ctx.materia.pasta, documento),
        "versao": documentos.versao(ctx.materia.pasta, documento.caminho),
    }


@router.put(_PREFIXO)
def salvar(corpo: DocumentoSalvar, ctx: Contexto = Depends(contexto_dep)) -> Criado:
    dados = corpo.model_dump(exclude={"versao_esperada"})
    if corpo.versao_esperada is not None:
        atual = documentos.versao(ctx.materia.pasta, documentos.caminho_documento(corpo.tipo, corpo.nome_arquivo))
        if atual is not None and atual != corpo.versao_esperada:
            raise Conflito("O documento mudou desde que foi aberto; recarregue para ver a versão atual.")
    with ctx.acao(f"Salvar {corpo.tipo} '{corpo.titulo}'") as op:
        return {"id": documentos.salvar(op, **dados)}


@router.delete(_PREFIXO + "/{documento_id}")
def remover(documento_id: int, ctx: Contexto = Depends(contexto_dep)) -> Ok:
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
