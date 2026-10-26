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


@dataclass(frozen=True)
class ItemTopico:
    titulo: str
    unidade: int
    secoes: tuple[str, ...]      # códigos aceitos do livro principal; vazio = o certo é não ligar


@dataclass(frozen=True)
class ItemLista:
    titulo: str
    unidade: int


@dataclass(frozen=True)
class ItemDocumento:
    titulo: str                  # título exato do documento na matéria
    secoes: tuple[str, ...]      # vazio = o certo é não ligar


@dataclass(frozen=True)
class GabaritoVinculos:
    topicos: tuple[ItemTopico, ...]
    listas: tuple[ItemLista, ...]
    documentos: tuple[ItemDocumento, ...]


def ler_vinculos(caminho: Path) -> GabaritoVinculos:
    dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    try:
        return GabaritoVinculos(
            topicos=tuple(ItemTopico(t["titulo"], int(t["unidade"]), tuple(t.get("secoes", []))) for t in dados.get("topico", [])),
            listas=tuple(ItemLista(l["titulo"], int(l["unidade"])) for l in dados.get("lista", [])),
            documentos=tuple(ItemDocumento(d["titulo"], tuple(d.get("secoes", []))) for d in dados.get("documento", [])),
        )
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"gabarito de vínculos inválido: {e}") from e
