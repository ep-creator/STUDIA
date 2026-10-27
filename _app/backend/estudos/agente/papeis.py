"""Papéis do assistente (tutor, resumidor, estrategista): instruções e ferramentas permitidas em `papeis/<nome>.md`,
editáveis sem mexer no código. Os atalhos da tela viram estes pedidos.
"""

from dataclasses import dataclass
from pathlib import Path

from estudos.conteudo import analisar_md

_PASTA = Path(__file__).parent / "papeis"
PAPEIS = ("tutor", "resumidor", "estrategista")

ATALHOS = {
    "N1": "Nível N1 (dica): só o conceito e o ponto de partida, sem contas.",
    "N2": "Nível N2 (caminho): o roteiro em passos, sem resolver as contas.",
    "N3": "Nível N3 (esboço): a estrutura com as passagens-chave, deixando as contas finais.",
    "N4": "Nível N4 (resolução completa no padrão prova): resolva e grave com salvar_resolucao.",
    "resumir": "Resuma a seção no formato dos meus resumos, grave com salvar_resumo e crie os cartões de fórmula.",
    "plano": "Monte o diagnóstico e o plano de revisão até a próxima prova.",
}


@dataclass(frozen=True)
class Papel:
    nome: str
    instrucoes: str
    ferramentas: list[str]
    modelo: str | None = None


def carregar_papel(nome: str) -> Papel:
    if nome not in PAPEIS:
        raise ValueError(f"papel desconhecido: {nome}")
    doc = analisar_md((_PASTA / f"{nome}.md").read_text(encoding="utf-8"))
    ferramentas = [f.strip() for f in str(doc.meta.get("ferramentas", "")).split(",") if f.strip()]
    return Papel(nome, doc.corpo.strip(), ferramentas, doc.meta.get("modelo") or None)
