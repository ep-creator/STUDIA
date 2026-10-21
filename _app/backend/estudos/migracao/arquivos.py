"""Arquivos do legado entram na matéria nova por hardlink: mesmo conteúdo, sem ocupar espaço, legado intacto."""

import os
import shutil
from pathlib import Path

from estudos.erros import DadoInvalido
from estudos.repos.fontes import sha256_arquivo

PASTA_FONTE_POR_TIPO = {"livro": "fontes/livros", "lista": "fontes/listas", "outro": "fontes/documentos"}


def vincular_arquivo(origem: Path, destino: Path) -> str:
    """Devolve 'hardlink', 'copia' (sem suporte a hardlink) ou 'existente' (destino já tem o mesmo conteúdo)."""
    if destino.exists():
        if sha256_arquivo(destino) == sha256_arquivo(origem):
            return "existente"
        raise DadoInvalido(f"{destino.name} já existe no destino com outro conteúdo.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(origem, destino)
        return "hardlink"
    except OSError:
        shutil.copy2(origem, destino)
        return "copia"
