"""Tabelas da avaliação em Markdown, gravadas em docs/avaliacoes/ para a decisão ficar registrada."""

import datetime
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


def gravar(conteudo: str, pasta: Path, tipo: str, hoje: datetime.date) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{hoje.isoformat()}-{tipo}.md"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho
