"""Chave do Gemini, guardada em _app/.segredos.toml (fora do Git: o repositório é público). Nenhuma rota a devolve."""

import tomllib
from pathlib import Path

_ARQUIVO = ".segredos.toml"


def ler_chave(app_dir: Path) -> str | None:
    arquivo = app_dir / _ARQUIVO
    if not arquivo.is_file():
        return None
    chave = tomllib.loads(arquivo.read_text(encoding="utf-8")).get("gemini", "").strip()
    return chave or None


def gravar_chave(app_dir: Path, chave: str) -> None:
    app_dir.mkdir(parents=True, exist_ok=True)
    limpa = chave.strip().replace("\\", "").replace('"', "")
    (app_dir / _ARQUIVO).write_text(f'# Chave da API do Gemini (não vai para o Git)\ngemini = "{limpa}"\n', encoding="utf-8")
