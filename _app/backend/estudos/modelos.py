"""Tipos de leitura do domínio e os valores permitidos de cada campo enumerado (espelham os CHECK do schema)."""

from dataclasses import dataclass

from estudos.erros import DadoInvalido

ORIGENS = ("importado", "manual", "agente", "migrado")
TIPOS_EVENTO = ("aula", "prova", "segunda_chamada", "exame_final", "extra", "feriado")
STATUS_TOPICO = ("pendente", "proxima", "visto")
LIBERACOES = ("auto", "aberta", "travada")
ESTADOS_MARCACAO = ("ok", "err", "dub")
LINHAS = (1, 2)
TIPOS_DOCUMENTO = ("resumo", "resolucao", "plano", "anotacao", "contexto")
TIPOS_FONTE = ("programa", "calendario", "turma", "livro", "lista", "slides", "prova", "anotacao", "outro")
PAPEIS_LIVRO = ("principal", "complementar")


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
    detalhe_md: str


@dataclass(frozen=True)
class Lista:
    id: int
    codigo: str
    titulo: str
    unidade_id: int
    fonte_id: int | None
    liberacao: str
    ordem: int
    origem: str
    aberta: bool


@dataclass(frozen=True)
class Questao:
    id: int
    lista_id: int
    rotulo: str
    ordem: int
    linha: int
    enunciado_md: str
    expressao: str | None
    pagina_pdf: int | None
    figura: str | None


@dataclass(frozen=True)
class QuestaoEntrada:
    rotulo: str
    linha: int = 1
    enunciado_md: str = ""
    expressao: str | None = None
    pagina_pdf: int | None = None
    figura: str | None = None
    chave_legada: str | None = None


@dataclass(frozen=True)
class Placar:
    ok: int
    err: int
    dub: int
    total: int
    feitos_linha1: int
    total_linha1: int
    feitos_linha2: int
    total_linha2: int
    taxa_acerto: float | None


@dataclass(frozen=True)
class Documento:
    id: int
    tipo: str
    caminho: str
    titulo: str
    unidade_id: int | None
    secao_id: int | None
    questao_id: int | None
    origem: str
    atualizado_em: str


@dataclass(frozen=True)
class Sessao:
    id: int
    unidade_id: int
    codigo: str
    data: str | None
    foco_md: str
    feito: bool
    ordem: int
    origem: str
    questao_ids: tuple[int, ...]


@dataclass(frozen=True)
class Formula:
    id: int
    unidade_id: int
    secao_id: int | None
    titulo: str
    corpo_tex: str
    notas_md: str
    ordem: int
    origem: str


@dataclass(frozen=True)
class Fonte:
    id: int
    tipo: str
    caminho: str
    sha256: str
    titulo: str
    paginas: int | None
    importada_em: str
    origem: str


@dataclass(frozen=True)
class Livro:
    fonte_id: int
    papel: str
    autor: str
    titulo_obra: str
    edicao: str
    offset_pagina: int
    gabarito_pdf_ini: int | None
    gabarito_pdf_fim: int | None


@dataclass(frozen=True)
class SecaoLivro:
    id: int
    livro_id: int
    codigo: str
    titulo: str
    nivel: int
    pagina_pdf_ini: int
    pagina_pdf_fim: int
    origem: str
    confianca: float | None


ESTADOS_IMPORTACAO = ("proposta", "confirmada", "descartada")


@dataclass(frozen=True)
class Importacao:
    id: int
    fonte_id: int
    tipo: str
    estado: str
    proposta: dict
    criada_em: str
    confirmada_em: str | None


@dataclass(frozen=True)
class HorarioAula:
    id: int
    dia_semana: int
    hora_inicio: str
    hora_fim: str


@dataclass(frozen=True)
class Criterio:
    id: int
    ordem: int
    texto: str
    origem: str
