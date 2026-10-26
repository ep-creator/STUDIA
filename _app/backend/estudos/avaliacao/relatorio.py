"""Tabelas da avaliação em Markdown, gravadas em docs/avaliacoes/ para a decisão ficar registrada."""

import datetime
import unicodedata
from pathlib import Path

from estudos.avaliacao.busca import LinhaBusca


def _pct(valor: float) -> str:
    return f"{round(valor * 100)}%"


def tabela_busca(linhas: list[LinhaBusca]) -> str:
    cabecalho = (
        "| configuração | acerto@5 | exata | paráfrase | MRR@10 | indexação (s) | busca p50 (ms) | busca p95 (ms) | memória (MB) |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    corpo = "".join(
        f"| {l.nome} | {_pct(l.acerto5)} | {_pct(l.acerto5_exata)} | {_pct(l.acerto5_parafrase)} | {l.mrr10:.2f} | "
        f"{l.indexacao_s} | {l.p50_ms} | {l.p95_ms} | {l.memoria_mb} |\n"
        for l in linhas
    )
    return cabecalho + corpo


def slug(texto: str) -> str:
    """"Geometria Analítica" → "geometriaanalitica": nome de arquivo sem acento nem espaço."""
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if c.isascii() and c.isalnum())


def gravar(conteudo: str, pasta: Path, tipo: str, hoje: datetime.date, materia: str | None = None) -> Path:
    """Grava em AAAA-MM-DD-<matéria>-<tipo>.md (uma matéria nunca sobrescreve o relatório de outra)."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{hoje.isoformat()}-{slug(materia) + '-' if materia else ''}{tipo}.md"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def tabela_vinculos(linhas) -> str:
    cabecalho = "| configuração | ligação | acertos | erros confiantes | para revisão |\n|---|---|---|---|---|\n"
    corpo = "".join(
        f"| {l.nome} | {l.tipo} | {l.acertos}/{l.total} ({_pct(l.acertos / l.total) if l.total else '—'}) | "
        f"{l.erros_confiantes} | {l.para_revisao} |\n"
        for l in linhas
    )
    return cabecalho + corpo
