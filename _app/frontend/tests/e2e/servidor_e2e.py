"""Motor para os testes de ponta a ponta: workspace temporário e porta própria.

Uso: python servidor_e2e.py <workspace> <porta>
Serve o build de _app/frontend/dist (o app_dir é o _app real) sobre um workspace vazio.
"""

import dataclasses
import sys
from pathlib import Path

import uvicorn

from estudos.config import carregar_settings
from estudos.main import create_app

APP_DIR = Path(__file__).resolve().parents[3]  # .../_app

workspace = Path(sys.argv[1])
porta = int(sys.argv[2])
workspace.mkdir(parents=True, exist_ok=True)
settings = dataclasses.replace(carregar_settings(APP_DIR, workspace), porta=porta)
uvicorn.run(create_app(settings), host="127.0.0.1", port=porta, log_level="warning")
