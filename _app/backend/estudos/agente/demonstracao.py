"""Modelo de demonstração (ESTUDOS_AGENTE_FALSO=1): responde sem chamar a API, para conferir a tela sem gastar.

Cita o primeiro rótulo do contexto e, num pedido N4, grava a resolução pela ferramenta (como o tutor de verdade).
"""

import re
from collections.abc import Iterator

from estudos.agente.modelo import Chamada, Texto, Turno, Uso

_ROTULO = re.compile(r"^\[[^\]\n]+\]$", re.MULTILINE)


class ModeloDemonstracao:
    nome = "demonstracao"

    def responder(self, sistema: str, turnos: list[Turno], ferramentas: list[dict]) -> Iterator[Texto | Chamada | Uso]:
        ultimo = turnos[-1]
        pediu = next((t.texto or "" for t in reversed(turnos) if t.autor == "usuario"), "")
        if ultimo.autor == "usuario" and "N4" in pediu and any(f["name"] == "salvar_resolucao" for f in ferramentas):
            yield Chamada("salvar_resolucao", {"texto": "**Enunciado.** (demonstração)\n\n**Resposta.** $x = 1$\n\n"
                                                        "**Armadilha.** nenhuma — esta é uma resposta de demonstração."})
            return
        rotulos = _ROTULO.findall(sistema)
        citacao = f" {rotulos[1]}" if len(rotulos) > 1 else (f" {rotulos[0]}" if rotulos else "")
        for parte in ("Resposta de **demonstração** (sem chamar o Gemini). ",
                      f"O material da tela está no contexto{citacao}, e a fórmula fica assim: $A = \\frac{{1}}{{2}} r^2 \\theta$."):
            yield Texto(parte)
        yield Uso(0, 0)
