from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from estudos.api.deps import Contexto, contexto_dep, materia_dep
from estudos.api.esquemas import DocumentoSalvar, SecaoEscolhida
from estudos.api.respostas import Criado, Documento, DocumentoComCorpo, Ligados, Ok
from estudos.importacao.vinculo import SugestaoSecao, secao_do_documento, semantica_de
from estudos.erros import Conflito, NaoEncontrado
from estudos.repos import documentos
from estudos.seguranca import caminho_seguro
from estudos.workspace import MateriaRef

router = APIRouter(tags=["documentos"])
_PREFIXO = "/api/materias/{materia_uid}/documentos"


@router.get(_PREFIXO)
def listar(tipo: str | None = None, unidade_id: int | None = None, ctx: Contexto = Depends(contexto_dep)) -> list[Documento]:
    return [asdict(d) for d in documentos.listar(ctx.con, tipo, unidade_id)]


@router.get(_PREFIXO + "/{documento_id}")
def obter(documento_id: int, ctx: Contexto = Depends(contexto_dep)) -> DocumentoComCorpo:
    documento = documentos.obter(ctx.con, documento_id)
    return {
        **asdict(documento), "corpo": documentos.ler_corpo(ctx.materia.pasta, documento),
        "versao": documentos.versao(ctx.materia.pasta, documento.caminho),
    }


@router.put(_PREFIXO)
def salvar(corpo: DocumentoSalvar, ctx: Contexto = Depends(contexto_dep)) -> Criado:
    dados = corpo.model_dump(exclude={"versao_esperada"})
    if corpo.versao_esperada is not None:
        caminho = documentos.caminho_documento(corpo.tipo, corpo.nome_arquivo)
        atual = documentos.versao(ctx.materia.pasta, caminho)
        if corpo.versao_esperada == "" and atual is not None:  # "" = criar: o arquivo ainda não pode existir
            raise Conflito(f"Já existe um documento em {caminho}; escolha outro nome.")
        if corpo.versao_esperada and atual is not None and atual != corpo.versao_esperada:
            raise Conflito("O documento mudou desde que foi aberto; recarregue para ver a versão atual.")
    with ctx.acao(f"Salvar {corpo.tipo} '{corpo.titulo}'") as op:
        did = documentos.salvar(op, **dados)
        # documento novo ou ainda sem seção: liga sozinho se a seção do livro for certa (senão fica a sugestão)
        documentos.tentar_ligar(op, ctx.materia.pasta, did, ctx.settings.limiar_vinculo, ctx.settings.limiar_confianca,
                                semantica_de(ctx.settings), ctx.settings.peso_sentido_vinculo)
        return {"id": did}


@router.post(_PREFIXO + "/ligar-secoes")
def ligar_secoes(ctx: Contexto = Depends(contexto_dep)) -> Ligados:
    """Liga às seções do livro os documentos ainda sem seção cuja sugestão é confiante (os demais ficam como sugestão)."""
    with ctx.acao("Ligar documentos às seções do livro") as op:
        return {"ligados": documentos.ligar_sem_secao(op, ctx.materia.pasta, ctx.settings.limiar_vinculo, ctx.settings.limiar_confianca,
                                                      semantica_de(ctx.settings), ctx.settings.peso_sentido_vinculo)}


@router.get(_PREFIXO + "/{documento_id}/sugestao-secao")
def sugestao_secao(documento_id: int, ctx: Contexto = Depends(contexto_dep)) -> SugestaoSecao | None:
    return secao_do_documento(ctx.con, documentos.obter(ctx.con, documento_id), ctx.settings.limiar_vinculo,
                              semantica=semantica_de(ctx.settings), peso=ctx.settings.peso_sentido_vinculo)


@router.put(_PREFIXO + "/{documento_id}/secao")
def escolher_secao(documento_id: int, corpo: SecaoEscolhida, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    titulo = documentos.obter(ctx.con, documento_id).titulo
    with ctx.acao(f"Ligar '{titulo}' à seção do livro") as op:
        documentos.ligar_secao(op, ctx.materia.pasta, documento_id, corpo.secao_id)
    return {"ok": True}


@router.delete(_PREFIXO + "/{documento_id}")
def remover(documento_id: int, ctx: Contexto = Depends(contexto_dep)) -> Ok:
    titulo = documentos.obter(ctx.con, documento_id).titulo
    with ctx.acao(f"Remover documento '{titulo}'") as op:
        documentos.remover(op, documento_id)
    return {"ok": True}


@router.get("/arquivos/{materia_uid}/{caminho:path}")
def arquivo(caminho: str, materia: MateriaRef = Depends(materia_dep)) -> FileResponse:
    alvo = caminho_seguro(materia.pasta, caminho)
    if not alvo.is_file():
        raise NaoEncontrado(f"Arquivo não encontrado: {caminho}")
    return FileResponse(alvo)
