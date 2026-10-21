"""Rotas de importação: upload → proposta revisável → edição/troca de tipo → confirmar ou descartar."""

import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from estudos.api.deps import Contexto, contexto_dep
from estudos.erros import ArquivoGrande, DadoInvalido
from estudos.importacao import pipeline
from estudos.modelos import Importacao
from estudos.repos import importacoes

router = APIRouter(prefix="/api/materias/{materia_uid}/importacoes", tags=["importação"])

_ASSINATURA_PDF = b"%PDF"
_BLOCO = 1024 * 1024
# Chaves que a proposta precisa manter para cada tipo (o restante é livre para edição)
_ESTRUTURA = {"programa": ("unidades",), "calendario": ("unidades",), "livro": ("secoes",), "lista": ("listas", "modo")}


class TipoEntrada(BaseModel):
    tipo: str


def _saida(imp: Importacao) -> dict:
    return {**asdict(imp), "pendencias": pipeline.contar_pendencias(imp.proposta)}


@router.post("")
def enviar(arquivo: UploadFile = File(...), ctx: Contexto = Depends(contexto_dep)) -> JSONResponse:
    # Rota síncrona de propósito: ler um livro leva segundos e o FastAPI a executa numa thread, sem travar o servidor
    limite = ctx.settings.limite_upload_mb * _BLOCO
    temporario = ctx.materia.pasta / ".versoes" / "_upload" / f"{uuid.uuid4().hex}.pdf"
    temporario.parent.mkdir(parents=True, exist_ok=True)
    try:
        tamanho, inicio = 0, b""
        with temporario.open("wb") as destino:
            while bloco := arquivo.file.read(_BLOCO):
                tamanho += len(bloco)
                if tamanho > limite:
                    raise ArquivoGrande(f"O arquivo passa do limite de {ctx.settings.limite_upload_mb} MB.")
                inicio = inicio or bloco[:4]
                destino.write(bloco)
        if inicio != _ASSINATURA_PDF:
            raise DadoInvalido("Por enquanto só PDFs podem ser importados.")
        antes = {i.id for i in importacoes.listar(ctx.con)}
        imp = pipeline.receber_arquivo(ctx.con, ctx.materia.pasta, temporario, arquivo.filename or "arquivo.pdf", ctx.settings)
    finally:
        temporario.unlink(missing_ok=True)
    return JSONResponse(_saida(imp), status_code=200 if imp.id in antes else 201)


@router.get("")
def listar(estado: str | None = None, ctx: Contexto = Depends(contexto_dep)) -> list[dict]:
    return [_saida(i) for i in importacoes.listar(ctx.con, estado)]


@router.get("/{importacao_id}")
def obter(importacao_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    return _saida(importacoes.obter(ctx.con, importacao_id))


@router.put("/{importacao_id}")
def editar(importacao_id: int, proposta: dict, ctx: Contexto = Depends(contexto_dep)) -> dict:
    imp = importacoes.obter(ctx.con, importacao_id)
    faltando = [c for c in _ESTRUTURA.get(imp.tipo, ()) if c not in proposta]
    if faltando:
        raise DadoInvalido(f"Proposta de '{imp.tipo}' sem: {', '.join(faltando)}")
    importacoes.atualizar_proposta(ctx.con, importacao_id, proposta)
    return _saida(importacoes.obter(ctx.con, importacao_id))


@router.post("/{importacao_id}/tipo")
def trocar_tipo(importacao_id: int, corpo: TipoEntrada, ctx: Contexto = Depends(contexto_dep)) -> dict:
    return _saida(pipeline.reprocessar(ctx.con, ctx.materia.pasta, importacao_id, corpo.tipo, ctx.settings))


@router.post("/{importacao_id}/confirmar")
def confirmar(importacao_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    return pipeline.confirmar(ctx.con, ctx.materia.pasta, importacao_id)


@router.post("/{importacao_id}/descartar")
def descartar(importacao_id: int, ctx: Contexto = Depends(contexto_dep)) -> dict:
    pipeline.descartar(ctx.con, importacao_id)
    return {"ok": True}
