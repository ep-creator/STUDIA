"""Aplicação FastAPI: middleware de origem local, tradução de erros de domínio e rotas."""

import sqlite3

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from estudos.api import (
    agente, app_web,
    cronograma, documentos, fontes, formulas, historico, importacoes, listas, marcacoes, materias, painel, rag, topicos,
    unidades,
)
from estudos.config import Settings
from estudos.erros import ArquivoGrande, Conflito, DadoInvalido, NaoEncontrado
from estudos.importacao.pdf import PdfInvalido
from estudos.seguranca import CaminhoInvalido, OrigemLocalMiddleware

ROUTERS = (
    materias.router, painel.router, marcacoes.router, historico.router, unidades.router, topicos.router,
    listas.router, cronograma.router, formulas.router, documentos.router, importacoes.router, rag.router, fontes.router,
    agente.router,
)


def _erro(status: int):
    async def tratar(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse({"erro": str(exc)}, status_code=status)
    return tratar


async def _erro_validacao(_request: Request, exc: RequestValidationError) -> JSONResponse:
    detalhes = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    return JSONResponse({"erro": f"Dados inválidos — {detalhes}"}, status_code=422)


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="STUDIA", version="2.0.0")
    app.state.settings = settings
    app.add_middleware(OrigemLocalMiddleware, porta=settings.porta)
    app.add_exception_handler(NaoEncontrado, _erro(404))
    app.add_exception_handler(Conflito, _erro(409))
    app.add_exception_handler(DadoInvalido, _erro(422))
    app.add_exception_handler(PdfInvalido, _erro(422))
    app.add_exception_handler(ArquivoGrande, _erro(413))
    app.add_exception_handler(CaminhoInvalido, _erro(422))
    app.add_exception_handler(sqlite3.IntegrityError, _erro(409))
    app.add_exception_handler(RequestValidationError, _erro_validacao)
    for router in ROUTERS:
        app.include_router(router)
    app_web.registrar(app, settings.app_dir / "frontend" / "dist")  # por último: rota coringa
    return app
