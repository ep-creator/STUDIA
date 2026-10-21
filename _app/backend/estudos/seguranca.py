"""Proteções do servidor local: caminhos confinados à matéria e requisições só da própria interface."""

import json
from pathlib import Path, PurePosixPath, PureWindowsPath

HOSTS_LOCAIS = frozenset({"127.0.0.1", "localhost"})
METODOS_ESCRITA = frozenset({"POST", "PUT", "PATCH", "DELETE"})
TIPOS_CORPO_PERMITIDOS = ("application/json", "multipart/form-data")


class CaminhoInvalido(ValueError):
    pass


def caminho_seguro(base: Path, relativo: str) -> Path:
    """Resolve `relativo` dentro de `base`; qualquer caminho absoluto ou que escape de `base` é rejeitado."""
    janela = PureWindowsPath(relativo)
    if janela.is_absolute() or janela.drive or janela.root or PurePosixPath(relativo).is_absolute():
        raise CaminhoInvalido(f"Caminho absoluto não é permitido: {relativo}")
    raiz = base.resolve()
    alvo = (raiz / relativo.replace("\\", "/")).resolve()
    if not alvo.is_relative_to(raiz):
        raise CaminhoInvalido(f"Caminho fora da matéria: {relativo}")
    return alvo


def _cabecalho(scope, nome: bytes) -> str:
    for chave, valor in scope.get("headers", []):
        if chave == nome:
            return valor.decode("latin-1")
    return ""


class OrigemLocalMiddleware:
    """Bloqueia Host não local, escritas vindas de outra origem e corpos que um site externo enviaria sem preflight."""

    def __init__(self, app, porta: int) -> None:
        self.app = app
        self.origens = {f"http://{h}:{porta}" for h in HOSTS_LOCAIS}

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and not self._permitido(scope):
            corpo = json.dumps({"erro": "requisição não permitida"}).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 403,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(corpo)).encode())],
            })
            await send({"type": "http.response.body", "body": corpo})
            return
        await self.app(scope, receive, send)

    def _permitido(self, scope) -> bool:
        host = _cabecalho(scope, b"host").rsplit(":", 1)[0].strip("[]")
        if host not in HOSTS_LOCAIS:
            return False
        if scope["method"] not in METODOS_ESCRITA:
            return True
        origem = _cabecalho(scope, b"origin")
        if origem and origem not in self.origens:
            return False
        tipo = _cabecalho(scope, b"content-type").lower()
        tem_corpo = _cabecalho(scope, b"content-length") not in ("", "0") or bool(_cabecalho(scope, b"transfer-encoding"))
        return not tem_corpo or tipo.startswith(TIPOS_CORPO_PERMITIDOS)
