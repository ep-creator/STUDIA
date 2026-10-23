"""Entrega do app (o build do frontend) pelo próprio motor: tudo fora de /api e /arquivos é o app."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

from estudos.erros import NaoEncontrado
from estudos.seguranca import CaminhoInvalido, caminho_seguro

_SEM_BUILD = """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>STUDIA</title>
<body style="font-family:system-ui;max-width:40rem;margin:4rem auto;line-height:1.6">
<h1>Frontend ainda não compilado</h1>
<p>Frontend ainda não compilado: rode o <code>abrir-novo.bat</code> (ou <code>npm run build</code> em
<code>_app/frontend</code>). A API continua disponível em <a href="/docs">/docs</a>.</p></body></html>"""

_RESERVADOS = ("api/", "arquivos/", "docs", "redoc", "openapi.json")


def registrar(app: FastAPI, dist: Path) -> None:
    """Registra a rota coringa; deve ser a última, para não encobrir nenhuma rota da API."""

    @app.get("/{caminho:path}", include_in_schema=False)
    def app_web(caminho: str):
        if caminho == "api" or caminho.startswith(_RESERVADOS):
            raise NaoEncontrado(f"Rota não encontrada: /{caminho}")
        indice = dist / "index.html"
        if not indice.is_file():
            return HTMLResponse(_SEM_BUILD)
        if caminho:
            try:
                alvo = caminho_seguro(dist, caminho)
            except CaminhoInvalido:
                alvo = None
            if alvo is not None and alvo.is_file():
                return FileResponse(alvo)
        return FileResponse(indice)
