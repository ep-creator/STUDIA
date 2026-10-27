"""Tabelas da avaliação em Markdown, gravadas em docs/avaliacoes/ para a decisão ficar registrada."""

import datetime
import unicodedata
from pathlib import Path

from estudos.avaliacao.busca import LinhaBusca


def _pct(valor: float) -> str:
    return f"{round(valor * 100)}%"


def tabela_busca(linhas: list[LinhaBusca]) -> str:
    """Colunas fixas + uma por estilo e por origem presentes; "trecho" = página/bloco exato (n = perguntas com trecho)."""
    estilos = sorted({e for l in linhas for e in l.por_estilo})
    origens = sorted({o for l in linhas for o in l.por_origem})
    nomes = ["configuração", "acerto@5", "acerto@20", *estilos, *(f"de {o}" for o in origens), "trecho", "links", "MRR@10",
             "indexação (s)", "busca p95 (ms)"]
    cabecalho = "| " + " | ".join(nomes) + " |\n|" + "---|" * len(nomes) + "\n"
    corpo = "".join(
        "| " + " | ".join([
            l.nome, _pct(l.acerto5), _pct(l.acerto20) if l.acerto20 is not None else "—", *(_pct(l.por_estilo[e]) if e in l.por_estilo else "—" for e in estilos),
            *(_pct(l.por_origem[o]) if o in l.por_origem else "—" for o in origens),
            f"{_pct(l.acerto5_trecho)} (n={l.n_trecho})" if l.acerto5_trecho is not None else "—",
            f"{_pct(l.relacionados)} (n={l.n_relacionados})" if l.relacionados is not None else "—",
            f"{l.mrr10:.2f}", str(l.indexacao_s), str(l.p95_ms),
        ]) + " |\n"
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
