"""Rotas do assistente: mensagem com resposta em streaming (uma linha JSON por evento), conversa por alvo, pacote de
contexto para colar em qualquer chat, estado (sem nunca devolver a chave) e gravação da chave fora do Git.
"""

import datetime
import json
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from estudos.agente import conversas
from estudos.agente.contexto import contexto_em_texto, montar_contexto
from estudos.agente.ferramentas import Ambiente
from estudos.agente.laco import responder
from estudos.agente.modelo import Gemini, Modelo
from estudos.agente.papeis import ATALHOS, carregar_papel
from estudos.agente.segredos import gravar_chave, ler_chave
from estudos.api.deps import Contexto, contexto_dep, materia_dep, obter_settings
from estudos.api.esquemas import AlvoAgente, ChaveAgente, PedidoAgente
from estudos.api.respostas import ConversaResumo, ConversaSaida, EstadoAgente, Ok, PacoteContexto
from estudos.config import Settings
from estudos.db.conexao import conectar
from estudos.erros import DadoInvalido
from estudos.historico import operacao, podar
from estudos.workspace import MateriaRef

router = APIRouter(tags=["agente"])
_BASE = "/api/materias/{materia_uid}/agente"
_ocupadas: set[tuple[str, str, str]] = set()   # (matéria, alvo, papel) respondendo agora: uma resposta por conversa
_trava = threading.Lock()


def fabrica_padrao(settings: Settings) -> Modelo | None:
    """O Gemini com a chave de _app/.segredos.toml; None sem chave. ESTUDOS_AGENTE_FALSO=1 liga o modelo de
    demonstração (para conferir a tela sem gastar)."""
    if os.environ.get("ESTUDOS_AGENTE_FALSO") == "1":
        from estudos.agente.demonstracao import ModeloDemonstracao
        return ModeloDemonstracao()
    chave = ler_chave(settings.app_dir)
    return Gemini(chave, settings.agente_modelo, settings.tempo_limite_s) if chave else None


def _linha(tipo: str, dados: dict) -> str:
    return json.dumps({"tipo": tipo, "dados": dados}, ensure_ascii=False) + "\n"


def _texto_do_pedido(pedido: PedidoAgente) -> str:
    if pedido.texto and pedido.texto.strip():
        return pedido.texto.strip() if pedido.atalho is None else f"{ATALHOS[pedido.atalho]}\n\n{pedido.texto.strip()}"
    return ATALHOS[pedido.atalho]


def _gerar(pedido: PedidoAgente, materia: MateriaRef, settings: Settings, fabrica) -> Iterator[str]:
    chave = (materia.uid, pedido.alvo, pedido.papel)
    with _trava:
        if chave in _ocupadas:
            yield _linha("erro", {"motivo": "ocupado", "detalhe": "já estou respondendo nesta conversa; espere terminar"})
            return
        _ocupadas.add(chave)
    try:
        modelo = fabrica(settings)
        if modelo is None:
            yield _linha("erro", {"motivo": "sem_chave", "detalhe": ""})
            return
        con = conectar(materia.db)   # a conexão da requisição já foi fechada quando o streaming começa
        try:
            @contextmanager
            def acao(descricao: str):
                with operacao(con, descricao, materia.pasta) as op:
                    yield op
                podar(con, settings.historico_max_grupos, materia.pasta)

            ambiente = Ambiente(con, materia.pasta, settings, pedido.alvo, acao)
            for saida in responder(ambiente, modelo, carregar_papel(pedido.papel), _texto_do_pedido(pedido),
                                   pedido.confirmado, settings.workspace, datetime.date.today()):
                yield _linha(saida.tipo, saida.dados)
        finally:
            con.close()
    finally:
        with _trava:
            _ocupadas.discard(chave)


@router.post(_BASE + "/mensagem")
def mensagem(pedido: PedidoAgente, request: Request, materia: MateriaRef = Depends(materia_dep),
             settings: Settings = Depends(obter_settings)) -> StreamingResponse:
    """Eventos em NDJSON: texto, ferramenta, gravado, confirmar, erro, fim."""
    fabrica = getattr(request.app.state, "fabrica_modelo", None) or fabrica_padrao
    return StreamingResponse(_gerar(pedido, materia, settings, fabrica), media_type="application/x-ndjson")


def _conversa(ctx: Contexto, alvo: str, papel: str, nova: bool = False) -> ConversaSaida:
    c = (conversas.recomecar if nova else conversas.conversa_ativa)(ctx.con, alvo, papel)
    return {"id": c.id, "alvo": c.alvo, "papel": c.papel,
            "mensagens": [asdict(m) for m in conversas.mensagens(ctx.con, c.id)]}


@router.get(_BASE + "/conversa")
def conversa(alvo: str, papel: str, ctx: Contexto = Depends(contexto_dep)) -> ConversaSaida:
    AlvoAgente(alvo=alvo, papel=papel)
    return _conversa(ctx, alvo, papel)


@router.get(_BASE + "/conversas")
def lista_de_conversas(ctx: Contexto = Depends(contexto_dep)) -> list[ConversaResumo]:
    return [asdict(c) for c in conversas.ativas(ctx.con)]


@router.post(_BASE + "/conversa/recomecar")
def recomecar(corpo: AlvoAgente, ctx: Contexto = Depends(contexto_dep)) -> ConversaSaida:
    return _conversa(ctx, corpo.alvo, corpo.papel, nova=True)


@router.get(_BASE + "/contexto")
def pacote(alvo: str, papel: str, atalho: str | None = None, ctx: Contexto = Depends(contexto_dep)) -> PacoteContexto:
    AlvoAgente(alvo=alvo, papel=papel)
    try:
        pedacos = montar_contexto(ctx.con, ctx.materia.pasta, alvo, papel)
    except ValueError as e:
        raise DadoInvalido(str(e)) from None
    pedido = ATALHOS.get(atalho or "", "(escreva aqui a sua pergunta)")
    return {"texto": f"# Instruções (papel: {papel})\n\n{carregar_papel(papel).instrucoes}\n\n"
                     f"# Contexto (materiais da matéria, com os rótulos para citar)\n\n{contexto_em_texto(pedacos)}\n\n"
                     f"# Pedido\n\n{pedido}\n"}


@router.get("/api/agente/estado")
def estado(settings: Settings = Depends(obter_settings)) -> EstadoAgente:
    demonstracao = os.environ.get("ESTUDOS_AGENTE_FALSO") == "1"   # responde sem chave: não pede a chave na tela
    return {"chave_configurada": demonstracao or ler_chave(settings.app_dir) is not None, "modelo": settings.agente_modelo,
            "total_mes": conversas.total_do_mes(settings.workspace, datetime.date.today()), "teto": settings.teto_mensal_brl}


@router.put("/api/agente/chave")
def chave(corpo: ChaveAgente, settings: Settings = Depends(obter_settings)) -> Ok:
    gravar_chave(settings.app_dir, corpo.chave)
    return {"ok": True}
