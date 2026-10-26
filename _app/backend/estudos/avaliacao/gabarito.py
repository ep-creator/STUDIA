"""Leitura dos gabaritos (TOML versionado em estudos/avaliacao/gabaritos/)."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from estudos.avaliacao.respostas import ler_aceita

# exata: palavras do livro · parafrase: como um aluno perguntaria · questao: o enunciado de uma questão (o que a IA vê)
ESTILOS = ("exata", "parafrase", "questao")
# quem escreveu: claude (rascunho revisado), usuario (dúvida real), gerada (a partir do banco, sem revisão item a item)
ORIGENS = ("claude", "usuario", "gerada")


@dataclass(frozen=True)
class PerguntaBusca:
    texto: str
    estilo: Literal["exata", "parafrase", "questao"]
    aceitas: tuple[str, ...]
    unidade: int | None = None
    origem: Literal["claude", "usuario", "gerada"] = "claude"


def ler_busca(caminho: Path) -> list[PerguntaBusca]:
    dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    perguntas = []
    for i, p in enumerate(dados.get("pergunta", []), start=1):
        texto, estilo, aceitas = p.get("texto", "").strip(), p.get("estilo"), p.get("aceitas") or []
        if not texto:
            raise ValueError(f"pergunta {i}: texto vazio")
        if estilo not in ESTILOS:
            raise ValueError(f"pergunta {i}: estilo {estilo!r} (use {' ou '.join(ESTILOS)})")
        origem = p.get("origem", "claude")
        if origem not in ORIGENS:
            raise ValueError(f"pergunta {i}: origem {origem!r} (use {', '.join(ORIGENS)})")
        if not aceitas:
            raise ValueError(f"pergunta {i}: sem respostas aceitas")
        for a in aceitas:
            try:
                ler_aceita(a)
            except ValueError as e:
                raise ValueError(f"pergunta {i}: {e}") from e
        perguntas.append(PerguntaBusca(texto, estilo, tuple(aceitas), p.get("unidade"), origem))
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


@dataclass(frozen=True)
class ItemRelacionado:
    de: str                       # documento ou arquivo de partida (mesmo formato das respostas aceitas)
    esperados: tuple[str, ...]    # o que deveria aparecer ligado a ele (seções, documentos, slides, listas…)


def ler_relacionados(caminho: Path) -> list[ItemRelacionado]:
    """[[relacionado]] do mesmo arquivo do gabarito de busca: mede os links entre documentos."""
    dados = tomllib.loads(Path(caminho).read_text(encoding="utf-8"))
    itens = []
    for i, r in enumerate(dados.get("relacionado", []), start=1):
        try:
            de = ler_aceita(r["de"])
            if de.tipo == "secao":
                raise ValueError("o ponto de partida precisa ser documento: ou fonte:")
            esperados = tuple(r.get("esperados", []))
            if not esperados:
                raise ValueError("sem esperados")
            for e in esperados:
                ler_aceita(e)
        except (KeyError, ValueError) as e:
            raise ValueError(f"relacionado {i}: {e}") from e
        itens.append(ItemRelacionado(r["de"], esperados))
    return itens
