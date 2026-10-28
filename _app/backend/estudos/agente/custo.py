"""Custo de uma resposta em reais, pela tabela de preços do config (US$ por milhão de tokens) e pela cotação."""

from estudos.config import Settings


def custo_brl(settings: Settings, modelo: str, tokens_entrada: int, tokens_saida: int) -> float:
    precos = settings.agente_precos.get(modelo) or settings.agente_precos.get(settings.agente_modelo) or {}
    dolares = (tokens_entrada * precos.get("entrada", 0.0) + tokens_saida * precos.get("saida", 0.0)) / 1_000_000
    return round(dolares * settings.cotacao_dolar, 4)
