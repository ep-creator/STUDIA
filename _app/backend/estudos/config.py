"""Configuração do motor: defaults num único lugar, sobrescritos por _app/config.toml."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# Seção do config.toml -> {chave no arquivo: campo de Settings}
_MAPA_TOML = {
    "servidor": {"host": "host", "porta": "porta"},
    "importacao": {"limiar_confianca": "limiar_confianca", "limiar_vinculo": "limiar_vinculo",
                   "limite_upload_mb": "limite_upload_mb"},
    "historico": {"max_grupos": "historico_max_grupos"},
    "inteligencia": {"embeddings": "embeddings", "modelo": "modelo", "busca": "busca",
                     "vinculos_com_embeddings": "vinculos_com_embeddings", "peso_sentido_vinculo": "peso_sentido_vinculo"},
    "agente": {"modelo": "agente_modelo", "teto_mensal_brl": "teto_mensal_brl", "cotacao_dolar": "cotacao_dolar",
               "max_rodadas": "max_rodadas", "tempo_limite_s": "tempo_limite_s", "precos": "agente_precos"},
}


@dataclass(frozen=True)
class Settings:
    workspace: Path
    app_dir: Path
    host: str = "127.0.0.1"
    porta: int = 8790
    limiar_confianca: float = 0.75
    limiar_vinculo: float = 0.35
    historico_max_grupos: int = 500
    limite_upload_mb: int = 200
    # Inteligência (peça B da Fase 6): tudo desligado até a avaliação mandar ligar
    embeddings: bool = False
    modelo: str = "intfloat/multilingual-e5-small"
    busca: str = "texto"                 # "texto", "vetor" ou "hibrida"
    vinculos_com_embeddings: bool = False
    peso_sentido_vinculo: float = 0.5
    # Assistente (peça A da Fase 6): Gemini por REST; preços em US$ por milhão de tokens
    agente_modelo: str = "gemini-3.8-flash"
    teto_mensal_brl: float = 20.0
    cotacao_dolar: float = 5.6
    max_rodadas: int = 6
    tempo_limite_s: int = 60
    agente_precos: dict = field(default_factory=lambda: {"gemini-3.8-flash": {"entrada": 0.30, "saida": 2.50}})


def carregar_settings(app_dir: Path, workspace: Path | None = None) -> Settings:
    valores = {}
    arquivo = app_dir / "config.toml"
    if arquivo.is_file():
        dados = tomllib.loads(arquivo.read_text(encoding="utf-8"))
        for secao, chaves in _MAPA_TOML.items():
            for chave, campo in chaves.items():
                if chave in dados.get(secao, {}):
                    valores[campo] = dados[secao][chave]
    return Settings(workspace=workspace or app_dir.parent, app_dir=app_dir, **valores)
