"""Único ponto que fala com o modelo de linguagem. Hoje, o Gemini por REST (resposta aos pedaços por SSE, com chamadas
de função); trocar de modelo ou de provedor mexe só aqui. `ModeloFalso` roteiriza respostas para os testes.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol

import httpx

_URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:streamGenerateContent?alt=sse"


@dataclass(frozen=True)
class Texto:
    texto: str


@dataclass(frozen=True)
class Chamada:
    nome: str
    argumentos: dict
    assinatura: str | None = None   # "thoughtSignature" do Gemini: precisa voltar junto na rodada seguinte


@dataclass(frozen=True)
class Uso:
    entrada: int
    saida: int


@dataclass(frozen=True)
class Turno:
    autor: str                                   # "usuario", "modelo" ou "ferramenta"
    texto: str | None = None
    chamadas: list[Chamada] = field(default_factory=list)
    resultados: list[tuple[str, dict]] = field(default_factory=list)


class ErroModelo(Exception):
    """motivo: sem_chave, chave_invalida, indisponivel, limite_de_uso ou tempo_esgotado."""

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)
        self.motivo = motivo
        self.detalhe = detalhe


class Modelo(Protocol):
    nome: str

    def responder(self, sistema: str, turnos: list[Turno], ferramentas: list[dict]) -> Iterator[Texto | Chamada | Uso]: ...


def _conteudo(turno: Turno) -> dict:
    if turno.autor == "usuario":
        return {"role": "user", "parts": [{"text": turno.texto or ""}]}
    if turno.autor == "modelo":
        partes = [{"text": turno.texto}] if turno.texto else []
        for c in turno.chamadas:
            parte: dict = {"functionCall": {"name": c.nome, "args": c.argumentos}}
            if c.assinatura:
                parte["thoughtSignature"] = c.assinatura
            partes.append(parte)
        return {"role": "model", "parts": partes}
    return {"role": "user", "parts": [{"functionResponse": {"name": n, "response": r}} for n, r in turno.resultados]}


def _motivo_http(status: int) -> str:
    if status in (400, 401, 403):
        return "chave_invalida"
    if status == 429:
        return "limite_de_uso"
    return "indisponivel"


class Gemini:
    def __init__(self, chave: str, modelo: str, tempo_limite_s: int, transporte: httpx.BaseTransport | None = None) -> None:
        self.nome = modelo
        self._chave = chave
        self._tempo = tempo_limite_s
        self._transporte = transporte

    def responder(self, sistema: str, turnos: list[Turno], ferramentas: list[dict]) -> Iterator[Texto | Chamada | Uso]:
        corpo = {"systemInstruction": {"parts": [{"text": sistema}]}, "contents": [_conteudo(t) for t in turnos]}
        if ferramentas:
            corpo["tools"] = [{"functionDeclarations": ferramentas}]
        uso = None
        try:
            with httpx.Client(transport=self._transporte, timeout=self._tempo) as cliente, cliente.stream(
                "POST", _URL.format(modelo=self.nome), json=corpo, headers={"x-goog-api-key": self._chave},
            ) as resposta:
                if resposta.status_code >= 400:
                    resposta.read()
                    raise ErroModelo(_motivo_http(resposta.status_code), resposta.text[:300])
                for linha in resposta.iter_lines():
                    if not linha.startswith("data:"):
                        continue
                    evento = json.loads(linha[5:].strip())
                    for candidato in evento.get("candidates", []):
                        for parte in candidato.get("content", {}).get("parts", []):
                            if "text" in parte and not parte.get("thought"):
                                yield Texto(parte["text"])
                            elif "functionCall" in parte:
                                fc = parte["functionCall"]
                                yield Chamada(fc["name"], fc.get("args") or {}, parte.get("thoughtSignature"))
                    if "usageMetadata" in evento:
                        u = evento["usageMetadata"]
                        uso = Uso(u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0))
        except httpx.TimeoutException as e:
            raise ErroModelo("tempo_esgotado", str(e)) from None
        except httpx.TransportError as e:
            raise ErroModelo("indisponivel", str(e)) from None
        if uso is not None:
            yield uso


class ModeloFalso:
    """Cada chamada a `responder` consome uma rodada roteirizada; um ErroModelo na rodada é levantado ali."""

    def __init__(self, rodadas: list[list], nome: str = "falso") -> None:
        self.nome = nome
        self._rodadas = list(rodadas)
        self.pedidos: list[tuple[str, list[Turno], list[dict]]] = []

    def responder(self, sistema: str, turnos: list[Turno], ferramentas: list[dict]) -> Iterator[Texto | Chamada | Uso]:
        self.pedidos.append((sistema, list(turnos), ferramentas))
        rodada = self._rodadas.pop(0) if self._rodadas else [Texto("(sem roteiro)")]
        for evento in rodada:
            if isinstance(evento, ErroModelo):
                raise evento
            yield evento
