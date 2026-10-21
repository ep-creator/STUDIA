"""Corpos de requisição validados pelo Pydantic. Respostas usam os dataclasses de estudos.modelos."""

from typing import Literal

from pydantic import BaseModel


class MateriaCriar(BaseModel):
    nome: str
    periodo: str | None = None


class MarcacaoDefinir(BaseModel):
    estado: Literal["ok", "err", "dub"] | None
