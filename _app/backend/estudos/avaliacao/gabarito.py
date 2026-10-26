"""Leitura dos gabaritos (TOML versionado em estudos/avaliacao/gabaritos/)."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ESTILOS = ("exata", "parafrase")
PREFIXOS_ACEITA = ("secao:", "documento:")


@dataclass(frozen=True)
class PerguntaBusca:
    texto: str
    estilo: Literal["exata", "parafrase"]
    aceitas: tuple[str, ...]
    unidade: int | None = None


def ler_busca(caminho: Path) -> list[PerguntaBusca]:
    dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    perguntas = []
    for i, p in enumerate(dados.get("pergunta", []), start=1):
        texto, estilo, aceitas = p.get("texto", "").strip(), p.get("estilo"), p.get("aceitas") or []
        if not texto:
            raise ValueError(f"pergunta {i}: texto vazio")
        if estilo not in ESTILOS:
            raise ValueError(f"pergunta {i}: estilo {estilo!r} (use {' ou '.join(ESTILOS)})")
        if not aceitas or not all(isinstance(a, str) and a.startswith(PREFIXOS_ACEITA) and a.split(":", 1)[1] for a in aceitas):
            raise ValueError(f"pergunta {i}: aceitas precisa de itens 'secao:<código>' ou 'documento:<título>'")
        perguntas.append(PerguntaBusca(texto, estilo, tuple(aceitas), p.get("unidade")))
    return perguntas
