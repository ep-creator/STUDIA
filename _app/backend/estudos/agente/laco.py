"""Laço de uma resposta do assistente: teto do mês → contexto da tela → modelo ↔ ferramentas (até `max_rodadas`) →
mensagem guardada com tokens e custo. Cada passo vira um evento para a tela (`Saida`).
"""

import datetime
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from estudos.agente import conversas
from estudos.agente.contexto import contexto_em_texto, montar_contexto
from estudos.agente.custo import custo_brl
from estudos.agente.ferramentas import FERRAMENTAS, Ambiente, declaracoes, executar
from estudos.agente.modelo import Chamada, ErroModelo, Modelo, Texto, Turno, Uso
from estudos.agente.papeis import Papel

_HISTORICO = 20
_PAREI = "\n\n_(Parei aqui para não gastar demais com buscas. Peça para continuar, se precisar.)_"


@dataclass(frozen=True)
class Saida:
    tipo: str                 # texto, ferramenta, gravado, confirmar, erro, fim
    dados: dict = field(default_factory=dict)


def _turnos(con, conversa_id: int) -> list[Turno]:
    anteriores = [m for m in conversas.mensagens(con, conversa_id) if m.autor in ("voce", "agente")][-_HISTORICO:]
    return [Turno("usuario" if m.autor == "voce" else "modelo", m.texto) for m in anteriores]


def responder(
    ambiente: Ambiente, modelo: Modelo, papel: Papel, texto: str, confirmado: bool, workspace: Path, hoje: datetime.date,
) -> Iterator[Saida]:
    ajustes = ambiente.settings
    if not confirmado:
        total = conversas.total_do_mes(workspace, hoje)
        if total + conversas.estimativa(workspace) > ajustes.teto_mensal_brl:
            yield Saida("confirmar", {"total_mes": total, "teto": ajustes.teto_mensal_brl})
            return
    con = ambiente.con
    conversa = conversas.conversa_ativa(con, ambiente.alvo, papel.nome)
    turnos = _turnos(con, conversa.id) + [Turno("usuario", texto)]
    conversas.adicionar(con, conversa.id, "voce", texto)
    try:
        contexto = contexto_em_texto(montar_contexto(con, ambiente.raiz, ambiente.alvo, papel.nome))
    except ValueError as e:
        yield Saida("erro", {"motivo": "alvo", "detalhe": str(e)})
        return
    sistema = f"{papel.instrucoes}\n\n## Contexto da tela (do app, com os rótulos para citar)\n\n{contexto}"
    ferramentas = declaracoes(papel.ferramentas)
    resposta: list[str] = []
    entrada = saida = 0
    try:
        for rodada in range(ajustes.max_rodadas + 1):
            texto_rodada: list[str] = []
            chamadas: list[Chamada] = []
            for evento in modelo.responder(sistema, turnos, ferramentas):
                if isinstance(evento, Texto):
                    texto_rodada.append(evento.texto)
                    resposta.append(evento.texto)
                    yield Saida("texto", {"texto": evento.texto})
                elif isinstance(evento, Chamada):
                    chamadas.append(evento)
                elif isinstance(evento, Uso):
                    entrada, saida = entrada + evento.entrada, saida + evento.saida
            if not chamadas:
                break
            if rodada == ajustes.max_rodadas:
                resposta.append(_PAREI)
                yield Saida("texto", {"texto": _PAREI})
                break
            resultados = []
            for c in chamadas:
                ferramenta = FERRAMENTAS.get(c.nome)
                yield Saida("ferramenta", {"nome": c.nome, "aviso": ferramenta.aviso if ferramenta else c.nome})
                resultado = executar(ambiente, papel.ferramentas, c.nome, c.argumentos)
                if "gravado" in resultado:
                    gravado = resultado["gravado"]
                    conversas.adicionar(con, conversa.id, "ferramenta", f"Gravado: {gravado['titulo']}")
                    yield Saida("gravado", gravado)
                resultados.append((c.nome, resultado))
            turnos = turnos + [Turno("modelo", "".join(texto_rodada) or None, chamadas), Turno("ferramenta", resultados=resultados)]
    except ErroModelo as e:
        custo = custo_brl(ajustes, modelo.nome, entrada, saida)
        if resposta:  # o que já chegou fica guardado
            conversas.adicionar(con, conversa.id, "agente", "".join(resposta), entrada, saida, custo, modelo.nome)
        yield Saida("erro", {"motivo": e.motivo, "detalhe": e.detalhe})
        return
    custo = custo_brl(ajustes, modelo.nome, entrada, saida)
    conversas.adicionar(con, conversa.id, "agente", "".join(resposta), entrada, saida, custo, modelo.nome)
    yield Saida("fim", {"custo_brl": custo, "total_mes": conversas.total_do_mes(workspace, hoje),
                        "tokens_entrada": entrada, "tokens_saida": saida})
