"""Configuração do motor: defaults num único lugar, sobrescritos por _app/config.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

# Seção do config.toml -> {chave no arquivo: campo de Settings}
_MAPA_TOML = {
    "servidor": {"host": "host", "porta": "porta"},
    "importacao": {"limiar_confianca": "limiar_confianca", "limiar_vinculo": "limiar_vinculo",
                   "limite_upload_mb": "limite_upload_mb"},
    "historico": {"max_grupos": "historico_max_grupos"},
    "inteligencia": {"embeddings": "embeddings", "modelo": "modelo", "busca": "busca",
                     "vinculos_com_embeddings": "vinculos_com_embeddings", "peso_sentido_vinculo": "peso_sentido_vinculo"},
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
