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
    "N4": "Nível N4 (resolução completa no padrão prova): resolva e grave com salvar_resolucao; não repita a resolução no chat, responda só com uma linha (gravou e o resultado final).",
    "resumir": "Resuma a seção no formato dos meus resumos, grave com salvar_resumo e crie os cartões de fórmula.",
    "plano": "Monte o diagnóstico e o plano de revisão até a próxima prova.",
}

# Como cada atalho aparece na conversa (a instrução acima é só para o modelo)
NOMES_ATALHOS = {
    "N1": "N1 Dica", "N2": "N2 Caminho", "N3": "N3 Esboço", "N4": "N4 Resolução",
    "resumir": "Resumir a seção", "plano": "Plano de revisão",
}


def texto_visivel(texto: str) -> str:
    """O pedido como o aluno o fez: "N4 Resolução" em vez da instrução do atalho; o que ele escreveu junto vem depois."""
    for atalho, instrucao in ATALHOS.items():
        if texto == instrucao:
            return NOMES_ATALHOS[atalho]
        if texto.startswith(instrucao + "\n\n"):
            return f"{NOMES_ATALHOS[atalho]}: {texto[len(instrucao) + 2:]}"
    return texto


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
