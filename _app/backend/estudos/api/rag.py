"""Rotas da busca: sincroniza o índice (barato quando nada mudou) e consulta com filtros exatos."""

import sqlite3
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from estudos.api.deps import Contexto, contexto_dep
from estudos.api.respostas import ExercicioLivro, ResultadoBusca, ResumoSincronizacao, TextoSecao
from estudos.erros import NaoEncontrado
from estudos.ia.embeddings import obter_embeddings
from estudos.rag.busca import buscar_modo, exercicio_de, resposta_de, secao_completa
from estudos.rag.indexador import ResumoSincronizacao as Resumo, agendar_sincronizacao, sincronizar
from estudos.rag.indice import abrir_indice, descartar_indice, eh_corrupcao, indice_desatualizado
from estudos.workspace import ARQUIVO_DB

router = APIRouter(prefix="/api/materias/{materia_uid}", tags=["busca"])


@router.get("/busca")
def busca(
    q: str = "",
    unidade: int | None = None,
    secao_id: int | None = None,
    tipo: list[str] | None = Query(None),
    limite: int = 8,
    modo: str | None = None,
    ctx: Contexto = Depends(contexto_dep),
) -> ResultadoBusca:
    """modo: "texto", "vetor" ou "hibrida" (padrão: o do config). Sem embeddings disponíveis, a busca é por texto e a
    resposta diz o modo efetivamente usado."""
    embeddings = obter_embeddings(ctx.settings)
    if _refazendo(ctx, embeddings):
        return {"resultados": [], "exercicios": [], "sincronizacao": asdict(Resumo(avisos=[_EM_ANDAMENTO])), "modo": "texto"}
    resumo = sincronizar(ctx.con, ctx.materia.pasta, esperar=False)
    if embeddings is not None and _faltam_vetores(ctx):
        # gerar os vetores leva minutos na primeira vez: vai para segundo plano e a busca segue com o que já existe
        agendar_sincronizacao(ctx.materia.pasta, ctx.materia.pasta / ARQUIVO_DB, embeddings=embeddings)
        resumo.avisos.append("vetores da busca por sentido em andamento; por enquanto parte da busca é só por texto")
    def consultar(indice):
        efetivo, resultados = buscar_modo(
            indice, q, unidade=unidade, secao_id=secao_id, tipos=tipo, limite=limite, modo=modo or ctx.settings.busca,
            embeddings=embeddings, partes=_partes(tipo))
        exercicios = []
        if not tipo or "livro" in tipo:  # exercícios do livro, à parte (com a resposta do gabarito quando há)
            _, achados = buscar_modo(indice, q, unidade=unidade, secao_id=secao_id, limite=_EXERCICIOS, modo=efetivo,
                                     embeddings=embeddings, partes=["exercicio"])
            exercicios = [_com_resposta(indice, r) for r in achados]
        return efetivo, resultados, exercicios

    efetivo, resultados, exercicios = _com_indice(ctx, consultar)
    return {"resultados": [asdict(r) for r in resultados], "exercicios": exercicios, "sincronizacao": asdict(resumo),
            "modo": efetivo}


_EXERCICIOS = 3
_EM_ANDAMENTO = "índice da busca sendo refeito em segundo plano (em andamento); os resultados voltam em alguns minutos"


def _refazendo(ctx: Contexto, embeddings=None) -> bool:
    """Índice de uma versão antiga (depois de atualizar o app): refazer leva minutos, então vai para segundo plano e
    quem pediu não espera."""
    if not indice_desatualizado(ctx.materia.pasta):
        return False
    agendar_sincronizacao(ctx.materia.pasta, ctx.materia.pasta / ARQUIVO_DB, embeddings=embeddings)
    return True


def _partes(tipos: list[str] | None) -> list[str]:
    """Resultados são a teoria; o gabarito (com ou sem número) entra quando o filtro pede gabarito."""
    return ["teoria", "resposta"] if tipos and "gabarito" in tipos else ["teoria"]


def _com_resposta(indice, exercicio) -> ExercicioLivro:
    resposta = None
    if exercicio.secao_id is not None and exercicio.numero is not None:
        resposta = resposta_de(indice, exercicio.secao_id, exercicio.numero)
    return {"exercicio": asdict(exercicio), "resposta": asdict(resposta) if resposta else None}


def _faltam_vetores(ctx: Contexto) -> bool:
    indice = abrir_indice(ctx.materia.pasta)
    try:
        return indice.execute("SELECT 1 FROM trecho WHERE vetor IS NULL LIMIT 1").fetchone() is not None
    finally:
        indice.close()


def _com_indice(ctx: Contexto, consulta):
    """Executa a consulta; índice corrompido é descartado e refeito uma vez (é sempre reconstruível)."""
    for tentativa in (1, 2):
        indice = abrir_indice(ctx.materia.pasta)
        try:
            return consulta(indice)
        except sqlite3.DatabaseError as erro:
            if tentativa == 2 or not eh_corrupcao(erro):
                raise
        finally:
            indice.close()
        descartar_indice(ctx.materia.pasta)
        sincronizar(ctx.con, ctx.materia.pasta)


@router.post("/busca/sincronizar")
def sincronizar_indice(ctx: Contexto = Depends(contexto_dep)) -> ResumoSincronizacao:
    return asdict(sincronizar(ctx.con, ctx.materia.pasta))


@router.get("/secoes/{secao_id}/texto")
def texto_da_secao(secao_id: int, ctx: Contexto = Depends(contexto_dep)) -> TextoSecao:
    secao = ctx.con.execute("SELECT id, codigo, titulo FROM secao_livro WHERE id = ?", (secao_id,)).fetchone()
    if secao is None:
        raise NaoEncontrado(f"Seção {secao_id} não encontrada")
    if _refazendo(ctx):
        return {"secao_id": secao["id"], "codigo": secao["codigo"], "titulo": secao["titulo"], "texto": ""}
    sincronizar(ctx.con, ctx.materia.pasta, esperar=False)
    texto = _com_indice(ctx, lambda indice: secao_completa(indice, secao_id))
    return {"secao_id": secao["id"], "codigo": secao["codigo"], "titulo": secao["titulo"], "texto": texto}


@router.get("/secoes/{secao_id}/exercicios/{numero}")
def exercicio_do_livro(secao_id: int, numero: int, ctx: Contexto = Depends(contexto_dep)) -> ExercicioLivro:
    """Exercício `numero` da seção do livro (enunciado original) e a resposta do gabarito, quando há."""
    if _refazendo(ctx):
        raise NaoEncontrado("O índice da busca está sendo refeito; o exercício aparece em alguns minutos")
    sincronizar(ctx.con, ctx.materia.pasta, esperar=False)
    exercicio = _com_indice(ctx, lambda indice: exercicio_de(indice, secao_id, numero))
    if exercicio is None:
        raise NaoEncontrado(f"Exercício {numero} da seção {secao_id} não está no índice")
    resposta = _com_indice(ctx, lambda indice: resposta_de(indice, secao_id, numero))
    return {"exercicio": asdict(exercicio), "resposta": asdict(resposta) if resposta else None}
