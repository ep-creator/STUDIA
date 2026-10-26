import datetime
import hashlib
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


def caminho_documento(tipo: str, nome_arquivo: str) -> str:
    """Caminho relativo do .md de um documento (pasta pelo tipo + nome sem diretórios)."""
    exigir_opcao(tipo, TIPOS_DOCUMENTO, "tipo de documento")
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
    caminho = caminho_documento(tipo, nome_arquivo)
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


# Código e posição da seção ligada: livro principal primeiro, depois os demais; dentro do livro, pela página
_COM_SECAO = """
    WITH ordem AS (
        SELECT s.id, s.codigo,
               ROW_NUMBER() OVER (ORDER BY l.papel = 'principal' DESC, l.fonte_id, s.pagina_pdf_ini, s.nivel) AS posicao
        FROM secao_livro s JOIN livro l ON l.fonte_id = s.livro_id)
    SELECT d.*, o.codigo AS secao_codigo, o.posicao AS secao_posicao
    FROM documento d LEFT JOIN ordem o ON o.id = d.secao_id
"""


def _documento(linha: sqlite3.Row) -> Documento:
    dados = dict(linha)
    dados["secao_decidida"] = bool(dados.get("secao_decidida"))
    return Documento(**dados)


def listar(con: sqlite3.Connection, tipo: str | None = None, unidade_id: int | None = None) -> list[Documento]:
    """Com `unidade_id`: documentos da unidade, os que a têm como unidade extra e os globais (sem unidade)."""
    sql, params = _COM_SECAO + " WHERE 1 = 1", []
    if tipo is not None:
        sql += " AND d.tipo = ?"
        params.append(tipo)
    if unidade_id is not None:
        sql += (
            " AND (d.unidade_id = ? OR d.unidade_id IS NULL OR EXISTS ("
            "SELECT 1 FROM documento_unidade_extra e WHERE e.documento_id = d.id AND e.unidade_id = ?))"
        )
        params += [unidade_id, unidade_id]
    return [_documento(l) for l in con.execute(sql + " ORDER BY d.caminho", params)]


def adicionar_unidade_extra(op: Operacao, documento_id: int, unidade_id: int) -> None:
    chave = {"documento_id": documento_id, "unidade_id": unidade_id}
    if _base.obter(op.con, "documento_unidade_extra", chave) is None:
        _base.inserir(op, "documento_unidade_extra", chave)


def obter(con: sqlite3.Connection, documento_id: int) -> Documento:
    linha = con.execute(_COM_SECAO + " WHERE d.id = ?", (documento_id,)).fetchone()
    if linha is None:
        raise NaoEncontrado(f"Documento {documento_id} não encontrado")
    return _documento(linha)


def versao(raiz: Path, caminho_rel: str) -> str | None:
    """sha256 dos bytes atuais do .md (None se não existe): muda com qualquer edição, inclusive por fora do app."""
    alvo = caminho_seguro(raiz, caminho_rel)
    return hashlib.sha256(alvo.read_bytes()).hexdigest() if alvo.is_file() else None


def ler_corpo(raiz: Path, documento: Documento) -> str:
    return ler_md(caminho_seguro(raiz, documento.caminho)).corpo


def remover(op: Operacao, documento_id: int) -> None:
    documento = obter(op.con, documento_id)
    apagar_md(op, documento.caminho)
    _base.remover(op, "documento", {"id": documento_id})


TIPOS_COM_SECAO = ("resumo", "resolucao", "plano")


def _regravar_secao(op: Operacao, raiz: Path, documento_id: int, secao_id: int | None) -> None:
    """Troca a seção do documento mantendo o corpo (o frontmatter do .md acompanha)."""
    doc = obter(op.con, documento_id)
    corpo = ler_corpo(raiz, doc)
    salvar(op, doc.tipo, doc.caminho.rsplit("/", 1)[-1], doc.titulo, corpo, doc.unidade_id, secao_id, doc.questao_id, doc.origem)


def ligar_secao(op: Operacao, raiz: Path, documento_id: int, secao_id: int | None) -> None:
    """Escolha do usuário (inclusive "sem seção"): fica marcada como decidida e a ligação automática não a desfaz."""
    _regravar_secao(op, raiz, documento_id, secao_id)
    _base.atualizar(op, "documento", {"id": documento_id}, {"secao_decidida": 1})


def _ligacao_desfeita(con: sqlite3.Connection, documento_id: int) -> bool:
    """O usuário desfez (no Histórico) uma ligação deste documento a uma seção: a ligação automática não a refaz."""
    return con.execute(
        "SELECT 1 FROM historico_mudanca m JOIN historico_grupo g ON g.id = m.grupo_id "
        "WHERE g.desfeito_em IS NOT NULL AND m.tabela = 'documento' AND json_extract(m.chave_json, '$.id') = ? "
        "AND json_extract(m.antes_json, '$.secao_id') IS NULL AND json_extract(m.depois_json, '$.secao_id') IS NOT NULL "
        "LIMIT 1", (documento_id,),
    ).fetchone() is not None


def tentar_ligar(
    op: Operacao, raiz: Path, documento_id: int, limiar_vinculo: float, limiar_gravar: float, semantica=None, peso: float = 0.5
) -> bool:
    """Liga à seção sugerida só se a confiança alcança `limiar_gravar`; abaixo disso nada é gravado (vira sugestão)."""
    from estudos.importacao.vinculo import secao_do_documento  # vínculo usa este repositório na leitura

    doc = obter(op.con, documento_id)
    if doc.tipo not in TIPOS_COM_SECAO or doc.secao_id is not None or doc.secao_decidida or _ligacao_desfeita(op.con, documento_id):
        return False
    sugestao = secao_do_documento(op.con, doc, limiar_vinculo, semantica=semantica, peso=peso)
    if sugestao is None or sugestao.confianca < limiar_gravar:
        return False
    _regravar_secao(op, raiz, documento_id, sugestao.secao_id)
    return True


def ligar_sem_secao(
    op: Operacao, raiz: Path, limiar_vinculo: float, limiar_gravar: float, semantica=None, peso: float = 0.5
) -> int:
    """Liga os documentos ainda sem seção (e sem decisão do usuário) cuja sugestão é confiante; devolve quantos."""
    ids = [
        r["id"] for r in op.con.execute(
            f"SELECT id FROM documento WHERE secao_id IS NULL AND secao_decidida = 0 "
            f"AND tipo IN ({', '.join('?' * len(TIPOS_COM_SECAO))}) ORDER BY id", TIPOS_COM_SECAO)
    ]
    return sum(tentar_ligar(op, raiz, i, limiar_vinculo, limiar_gravar, semantica, peso) for i in ids)
