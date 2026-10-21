"""Exceções de domínio, traduzidas para HTTP pela API (404 / 422)."""


class NaoEncontrado(LookupError):
    pass


class DadoInvalido(ValueError):
    pass


class Conflito(DadoInvalido):
    """A operação não cabe no estado atual (ex.: confirmar uma importação já confirmada) → HTTP 409."""


class ArquivoGrande(ValueError):
    """Upload acima do limite configurado → HTTP 413."""
