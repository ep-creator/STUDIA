"""Exceções de domínio, traduzidas para HTTP pela API (404 / 422)."""


class NaoEncontrado(LookupError):
    pass


class DadoInvalido(ValueError):
    pass
