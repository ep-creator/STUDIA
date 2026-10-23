"""Inicia o motor: `python -m estudos [--porta N] [--sem-navegador]`."""

import argparse
import dataclasses
import threading
import webbrowser
from pathlib import Path

import uvicorn

from estudos.config import carregar_settings
from estudos.main import create_app

APP_DIR_PADRAO = Path(__file__).resolve().parents[2]  # .../_app


def main(argv: list[str] | None = None, app_dir: Path | None = None) -> None:
    parser = argparse.ArgumentParser(prog="estudos", description="STUDIA — motor local")
    parser.add_argument("--porta", type=int, help="porta HTTP (padrão: config.toml)")
    parser.add_argument("--sem-navegador", action="store_true", help="não abrir o navegador")
    args = parser.parse_args(argv)

    settings = carregar_settings(app_dir or APP_DIR_PADRAO)
    if args.porta:
        settings = dataclasses.replace(settings, porta=args.porta)
    if not args.sem_navegador:
        url = f"http://{settings.host}:{settings.porta}/"
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.porta)


if __name__ == "__main__":
    main()
