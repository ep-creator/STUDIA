import datetime
import sqlite3
from pathlib import Path, PurePosixPath, PureWindowsPath

from estudos.conteudo import DocumentoMd, apagar_md, escrever_md, ler_md
from estudos.erros import NaoEncontrado
from estudos.historico import Operacao
from estudos.modelos import ORIGENS, TIPOS_DOCUMENTO, Documento, exigir_opcao
from estudos.repos import _base
from estudos.seguranca import CaminhoInvalido, caminho_seguro

PASTA_POR_TIPO = {
    "resumo": "conteudo/resumos",
    "resolucao": "conteudo/resolucoes",
    "plano": "conteudo/planos",
    "anotacao": "conteudo/anotacoes",
    "contexto": "conteudo",
}


def _caminho(tipo: str, nome_arquivo: str) -> str:
    nome = nome_arquivo.strip()
    if nome != PureWindowsPath(nome).name or nome != PurePosixPath(nome).name or nome in ("", ".", ".."):
        raise CaminhoInvalido(f"Nome de arquivo inválido: {nome_arquivo!r}")
    if not nome.lower().endswith(".md"):
        nome += ".md"
    return f"{PASTA_POR_TIPO[tipo]}/{nome}"


def _frontmatter(con: sqlite3.Connection, tipo, titulo, unidade_id, secao_id, questao_id, origem) -> dict:
    unidade = con.execute("SELECT numero FROM unidade WHERE id = ?", (unidade_id,)).fetchone() if unidade_id else None
    secao = con.execute("SELECT codigo FROM secao_livro WHERE id = ?", (secao_id,)).fetchone() if secao_id else None
    return {
        "tipo": tipo,
        "titulo": titulo,
        "unidade": unidade["numero"] if unidade else None,
        "secao": secao["codigo"] if secao else None,
        "questao": questao_id,
        "origem": origem,
    }


def salvar(
    op: Operacao,
    tipo: str,
    nome_arquivo: str,
    titulo: str,
    corpo: str,
    unidade_id: int | None = None,
    secao_id: int | None = None,
    questao_id: int | None = None,
    origem: str = "manual",
) -> int:
    """Grava o .md (frontmatter gerado a partir dos dados; corpo intacto) e faz upsert da linha pelo caminho."""
    exigir_opcao(tipo, TIPOS_DOCUMENTO, "tipo de documento")
    exigir_opcao(origem, ORIGENS, "origem")
    caminho = _caminho(tipo, nome_arquivo)
    meta = _frontmatter(op.con, tipo, titulo, unidade_id, secao_id, questao_id, origem)
    escrever_md(op, caminho, DocumentoMd(meta, corpo))
    valores = {
        "tipo": tipo, "titulo": titulo, "unidade_id": unidade_id, "secao_id": secao_id, "questao_id": questao_id,
        "origem": origem, "atualizado_em": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    existente = op.con.execute("SELECT id FROM documento WHERE caminho = ?", (caminho,)).fetchone()
    if existente:
        _base.atualizar(op, "documento", {"id": existente["id"]}, valores)
        return existente["id"]
    return _base.inserir(op, "documento", {"caminho": caminho, **valores})


def listar(con: sqlite3.Connection, tipo: str | None = None, unidade_id: int | None = None) -> list[Documento]:
    """Com `unidade_id`: documentos da unidade, os que a têm como unidade extra e os globais (sem unidade)."""
    sql, params = "SELECT * FROM documento d WHERE 1 = 1", []
    if tipo is not None:
        sql += " AND d.tipo = ?"
        params.append(tipo)
    if unidade_id is not None:
        sql += (
            " AND (d.unidade_id = ? OR d.unidade_id IS NULL OR EXISTS ("
            "SELECT 1 FROM documento_unidade_extra e WHERE e.documento_id = d.id AND e.unidade_id = ?))"
        )
        params += [unidade_id, unidade_id]
    return [Documento(**dict(l)) for l in con.execute(sql + " ORDER BY d.caminho", params)]


def adicionar_unidade_extra(op: Operacao, documento_id: int, unidade_id: int) -> None:
    chave = {"documento_id": documento_id, "unidade_id": unidade_id}
    if _base.obter(op.con, "documento_unidade_extra", chave) is None:
        _base.inserir(op, "documento_unidade_extra", chave)


def obter(con: sqlite3.Connection, documento_id: int) -> Documento:
    linha = con.execute("SELECT * FROM documento WHERE id = ?", (documento_id,)).fetchone()
    if linha is None:
        raise NaoEncontrado(f"Documento {documento_id} não encontrado")
    return Documento(**dict(linha))


def ler_corpo(raiz: Path, documento: Documento) -> str:
    return ler_md(caminho_seguro(raiz, documento.caminho)).corpo


def remover(op: Operacao, documento_id: int) -> None:
    documento = obter(op.con, documento_id)
    apagar_md(op, documento.caminho)
    _base.remover(op, "documento", {"id": documento_id})
