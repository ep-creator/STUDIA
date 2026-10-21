"""Relatório da migração: contagens legado × novo, decisões tomadas por regra e o que ficou sem resolver."""

from dataclasses import dataclass, field

_ROTULOS = {
    "unidades": "Unidades", "topicos": "Tópicos (Onde estamos)", "livros": "Livros", "secoes_livro": "Seções de livro",
    "listas": "Listas / seções de exercício", "questoes": "Questões", "marcacoes": "Marcações ✓ ✗ ?",
    "sessoes": "Sessões do cronograma", "formulas": "Fórmulas", "resumos": "Resumos", "resolucoes": "Resoluções",
    "documentos": "Outros documentos", "figuras": "Figuras", "fontes": "PDFs (fontes)",
}


@dataclass
class Relatorio:
    materia: str
    gerado_em: str
    contagens: dict[str, tuple[int, int]] = field(default_factory=dict)
    decisoes: list[str] = field(default_factory=list)
    nao_resolvidos: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    arquivos: dict[str, int] = field(default_factory=lambda: {"hardlink": 0, "copia": 0, "existente": 0})

    def bate(self) -> bool:
        """Tudo o que as regras dizem que deve migrar foi gravado (o legado já vem contado pelas mesmas regras)."""
        return all(legado == novo for legado, novo in self.contagens.values())

    def markdown(self) -> str:
        def lista(itens: list[str]) -> list[str]:
            return [f"- {i}" for i in itens] or ["_Nenhum._"]

        linhas = [
            f"# Relatório da migração — {self.materia}",
            "",
            f"Gerado em {self.gerado_em}. Resultado: **{'contagens batem' if self.bate() else 'CONTAGENS NÃO BATEM'}**.",
            "",
            "## Contagens",
            "",
            "| Item | Legado | Novo | |",
            "|---|---|---|---|",
            *(
                f"| {_ROTULOS.get(chave, chave)} | {legado} | {novo} | {'✓' if legado == novo else '✗'} |"
                for chave, (legado, novo) in self.contagens.items()
            ),
            "",
            "## Decisões tomadas por regra",
            "",
            *lista(self.decisoes),
            "",
            "## Não resolvidos (revise)",
            "",
            *lista(self.nao_resolvidos),
            "",
            "## Avisos",
            "",
            *lista(self.avisos),
            "",
            "## Arquivos",
            "",
            *(f"- {modo}: {n}" for modo, n in self.arquivos.items()),
            "",
        ]
        return "\n".join(linhas)
