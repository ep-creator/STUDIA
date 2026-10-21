"""Tipos de leitura do domínio e os valores permitidos de cada campo enumerado (espelham os CHECK do schema)."""

from dataclasses import dataclass

from estudos.erros import DadoInvalido

ORIGENS = ("importado", "manual", "agente", "migrado")
TIPOS_EVENTO = ("aula", "prova", "segunda_chamada", "exame_final", "extra", "feriado")
STATUS_TOPICO = ("pendente", "proxima", "visto")


def exigir_opcao(valor: str, opcoes: tuple[str, ...], campo: str) -> str:
    if valor not in opcoes:
        raise DadoInvalido(f"{campo} inválido: {valor!r} (use {', '.join(opcoes)})")
    return valor


@dataclass(frozen=True)
class Materia:
    id: int
    uid: str
    nome: str
    periodo: str | None
    instituicao: str | None
    professor: str | None
    email_professor: str | None


@dataclass(frozen=True)
class Unidade:
    id: int
    numero: int
    titulo: str
    origem: str
    confianca: float | None
    data_prova: str | None


@dataclass(frozen=True)
class Evento:
    id: int
    tipo: str
    data: str
    hora_inicio: str | None
    hora_fim: str | None
    unidade_id: int | None
    descricao: str
    origem: str


@dataclass(frozen=True)
class Topico:
    id: int
    unidade_id: int
    pai_id: int | None
    ordem: int
    titulo: str
    status: str
    origem: str
