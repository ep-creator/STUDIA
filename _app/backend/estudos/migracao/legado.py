"""Leitura tipada e validada dos arquivos do app legado. Só lê; nenhuma regra de mapeamento aqui."""

import json
from dataclasses import dataclass
from pathlib import Path

_CHAVES_CURSO = ("nome", "subtituloGeral", "livros", "documentos", "unidades")
_CHAVES_SECAO = ("sec", "un", "nome", "l1", "l2")


class LegadoInvalido(ValueError):
    pass


@dataclass(frozen=True)
class ItemLegado:
    numero: str
    pede: str
    expressao: str | None
    figura: str | None
    linha: int


@dataclass(frozen=True)
class SecaoLegado:
    sec: str
    un: int
    nome: str
    pdf: str | None
    locked: bool
    itens: tuple[ItemLegado, ...]


@dataclass(frozen=True)
class Legado:
    pasta: Path
    curso: dict
    secoes: tuple[SecaoLegado, ...]
    marcacoes: dict[str, str]
    resumos: tuple[Path, ...]
    resolucoes: tuple[Path, ...]
    pdfs: tuple[Path, ...]
    figuras: tuple[Path, ...]


def _json(caminho: Path, rel: str):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise LegadoInvalido(f"Arquivo ausente: {rel}") from None
    except json.JSONDecodeError as e:
        raise LegadoInvalido(f"JSON inválido em {rel}: {e}") from None


def _exigir(dados: dict, chaves, rel: str) -> None:
    faltando = [c for c in chaves if c not in dados]
    if faltando:
        raise LegadoInvalido(f"{rel}: chave(s) ausente(s): {', '.join(faltando)}")


def _secao(dados: dict) -> SecaoLegado:
    _exigir(dados, _CHAVES_SECAO, f"exercicios.json (seção {dados.get('sec', '?')})")
    itens = tuple(
        ItemLegado(numero=str(item[0]), pede=item[1] or "", expressao=item[2], figura=item[3], linha=linha)
        for linha, chave in ((1, "l1"), (2, "l2"))
        for item in dados[chave]
    )
    return SecaoLegado(
        sec=str(dados["sec"]), un=int(dados["un"]), nome=dados["nome"], pdf=dados.get("pdf"),
        locked=bool(dados.get("locked", False)), itens=itens,
    )


def carregar(pasta: Path) -> Legado:
    curso = _json(pasta / "_app/dados/curso.json", "_app/dados/curso.json")
    _exigir(curso, _CHAVES_CURSO, "_app/dados/curso.json")
    exercicios = _json(pasta / "_app/dados/exercicios.json", "_app/dados/exercicios.json")
    status = _json(pasta / "status.json", "status.json")
    pdfs = sorted(
        p.relative_to(pasta)
        for sub in ("disciplina", "livros")
        if (pasta / sub).is_dir()
        for p in (pasta / sub).rglob("*.pdf")
    )
    return Legado(
        pasta=pasta,
        curso=curso,
        secoes=tuple(_secao(s) for s in exercicios),
        marcacoes=dict(status.get("marcacoes", {})),
        resumos=tuple(sorted((pasta / "resumos").glob("*.md"))),
        resolucoes=tuple(sorted((pasta / "resolucoes").glob("*.md"))),
        pdfs=tuple(pdfs),
        figuras=tuple(sorted((pasta / "_app/img").glob("*.png"))),
    )
