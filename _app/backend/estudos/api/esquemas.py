"""Corpos de requisição validados pelo Pydantic. Respostas usam os dataclasses de estudos.modelos."""

from typing import Literal

from pydantic import BaseModel

from estudos.erros import DadoInvalido


class MateriaCriar(BaseModel):
    nome: str
    periodo: str | None = None


class MarcacaoDefinir(BaseModel):
    estado: Literal["ok", "err", "dub"] | None


class Edicao(BaseModel):
    """Base dos PATCH: só os campos enviados são alterados."""

    def campos(self) -> dict:
        valores = self.model_dump(exclude_unset=True)
        if not valores:
            raise DadoInvalido("Nenhum campo para alterar.")
        return valores


class UnidadeCriar(BaseModel):
    numero: int
    titulo: str = ""


class UnidadeEditar(Edicao):
    numero: int | None = None
    titulo: str | None = None


class EventoCriar(BaseModel):
    tipo: str
    data: str
    unidade_id: int | None = None
    hora_inicio: str | None = None
    hora_fim: str | None = None
    descricao: str = ""


class TopicoCriar(BaseModel):
    unidade_id: int
    titulo: str
    pai_id: int | None = None
    ordem: int | None = None


class TopicoEditar(Edicao):
    titulo: str | None = None
    status: str | None = None
    ordem: int | None = None
    pai_id: int | None = None


class ListaCriar(BaseModel):
    codigo: str
    titulo: str
    unidade_id: int
    liberacao: str = "auto"


class ListaEditar(Edicao):
    codigo: str | None = None
    titulo: str | None = None
    unidade_id: int | None = None
    liberacao: str | None = None


class QuestaoEsquema(BaseModel):
    rotulo: str
    linha: int = 1
    enunciado_md: str = ""
    expressao: str | None = None
    pagina_pdf: int | None = None
    figura: str | None = None


class SessaoCriar(BaseModel):
    unidade_id: int
    codigo: str
    data: str | None = None
    foco_md: str = ""


class SessaoEditar(Edicao):
    codigo: str | None = None
    data: str | None = None
    foco_md: str | None = None
    feito: bool | None = None
    ordem: int | None = None


class FormulaCriar(BaseModel):
    unidade_id: int
    titulo: str
    corpo_tex: str
    notas_md: str = ""
    secao_id: int | None = None


class FormulaEditar(Edicao):
    titulo: str | None = None
    corpo_tex: str | None = None
    notas_md: str | None = None
    secao_id: int | None = None


class DocumentoSalvar(BaseModel):
    tipo: str
    nome_arquivo: str
    titulo: str
    corpo: str
    unidade_id: int | None = None
    secao_id: int | None = None
    questao_id: int | None = None
    versao_esperada: str | None = None  # "versao" do documento quando foi aberto; diferente da atual → 409
