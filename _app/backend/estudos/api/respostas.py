"""Formatos das respostas compostas da API, para o OpenAPI (e daí os tipos do frontend).

Só descrevem o JSON que as rotas já devolvem: o FastAPI usa a anotação de retorno como `response_model`, e uma chave que
faltasse aqui sumiria da resposta, o que a suíte de testes acusa.
"""

from typing import Any, TypedDict

from estudos.historico import GrupoHistorico
from estudos.modelos import (
    Documento, Evento, Formula, Materia, Placar, Questao, SecaoLivro, Sessao, Topico, Unidade,
)
from estudos.rag.busca import Resultado
from estudos.rag.indexador import ResumoSincronizacao


class Criado(TypedDict):
    id: int


class Ok(TypedDict):
    ok: bool


class Ligados(TypedDict):
    ligados: int


class ProximaProva(TypedDict):
    data: str
    hora_inicio: str | None
    unidade: int | None


class ResumoMateria(TypedDict):
    uid: str
    nome: str
    periodo: str | None
    unidades: int
    proxima_prova: ProximaProva | None
    importacoes_pendentes: int


class MateriaCriada(TypedDict):
    uid: str
    nome: str


class SecaoVinculada(TypedDict):
    secao_id: int
    codigo: str
    titulo: str
    fonte_id: int
    caminho: str
    pagina_pdf_ini: int


class VinculosLista(TypedDict):
    topicos: list[int]
    secao: SecaoVinculada | None


class Vinculos(TypedDict):
    topicos: dict[str, list[SecaoVinculada]]
    listas: dict[str, VinculosLista]


class ListaComQuestoes(TypedDict):
    id: int
    codigo: str
    titulo: str
    unidade_id: int
    fonte_id: int | None
    liberacao: str
    ordem: int
    origem: str
    aberta: bool
    questoes: list[Questao]


class Painel(TypedDict):
    materia: Materia
    unidades: list[Unidade]
    unidade_atual: int | None
    unidade: int | None
    topicos: list[Topico]
    listas: list[ListaComQuestoes]
    marcacoes: dict[str, str]
    sessoes: list[Sessao]
    formulas: list[Formula]
    documentos: list[Documento]
    placar: Placar | None
    eventos: list[Evento]
    vinculos: Vinculos
    importacoes_pendentes: int


class Marcado(TypedDict):
    placar: Placar


class FonteResumo(TypedDict):
    id: int
    tipo: str
    titulo: str
    caminho: str
    paginas: int | None


class DocumentoComCorpo(TypedDict):
    id: int
    tipo: str
    caminho: str
    titulo: str
    unidade_id: int | None
    secao_id: int | None
    questao_id: int | None
    origem: str
    atualizado_em: str
    secao_decidida: bool
    secao_codigo: str | None
    secao_posicao: int | None
    corpo: str
    versao: str | None


class MudancaLinha(TypedDict):
    tabela: str
    chave: dict[str, Any]
    antes: dict[str, Any] | None
    depois: dict[str, Any] | None


class MudancaArquivo(TypedDict):
    caminho: str
    antes: str | None
    depois: str | None


class DetalheHistorico(TypedDict):
    grupo: GrupoHistorico
    mudancas: list[MudancaLinha]
    arquivos: list[MudancaArquivo]


class Desfeito(TypedDict):
    desfeito: GrupoHistorico | None


class ImportacaoSaida(TypedDict):
    id: int
    fonte_id: int
    tipo: str
    estado: str
    proposta: dict[str, Any]  # livre: o frontend tipa por tipo de arquivo (src/api/proposta.ts)
    criada_em: str
    confirmada_em: str | None
    pendencias: int


class ResumoImportacao(TypedDict):
    unidades: int
    topicos: int
    eventos: int
    secoes: int
    listas: int
    questoes: int
    vinculos: int
    criterios: int
    indexacao: str


class MensagemSaida(TypedDict):
    id: int
    autor: str          # voce, agente ou ferramenta
    texto: str
    custo_brl: float
    criada_em: str


class ConversaResumo(TypedDict):
    id: int
    alvo: str
    papel: str
    rotulo: str          # "Geral", "14.1 #22" ou "15.4 Integrais duplas"
    atualizada_em: str


class ConversaSaida(TypedDict):
    id: int
    alvo: str
    papel: str
    mensagens: list[MensagemSaida]


class PacoteContexto(TypedDict):
    texto: str          # instruções do papel + contexto da tela + pedido, para colar em qualquer chat


class EstadoAgente(TypedDict):
    chave_configurada: bool
    modelo: str
    total_mes: float
    teto: float


class ExercicioLivro(TypedDict):
    exercicio: Resultado
    resposta: Resultado | None       # do gabarito do livro, quando há


class ResultadoBusca(TypedDict):
    resultados: list[Resultado]       # só teoria
    exercicios: list[ExercicioLivro]  # exercícios do livro mais parecidos (até 3), à parte
    sincronizacao: ResumoSincronizacao
    modo: str          # modo efetivamente usado ("texto" quando não há embeddings)


class TextoSecao(TypedDict):
    secao_id: int
    codigo: str
    titulo: str
    texto: str


__all__ = [
    "Criado", "Ok", "ResumoMateria", "MateriaCriada", "Painel", "Marcado", "FonteResumo", "DocumentoComCorpo",
    "DetalheHistorico", "Desfeito", "ImportacaoSaida", "ResumoImportacao", "ResultadoBusca", "TextoSecao",
    "SecaoLivro", "GrupoHistorico", "ResumoSincronizacao", "ExercicioLivro", "ConversaSaida", "PacoteContexto",
    "EstadoAgente",
]
