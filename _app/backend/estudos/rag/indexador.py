"""Sincronização do índice com o banco da matéria: só reindexa o que mudou e remove o que foi apagado.

Cada origem ("fonte:N", "documento:N") tem uma assinatura calculada só com dados do banco; sem mudança de assinatura
nenhum arquivo é aberto.
"""

import datetime
import hashlib
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from estudos.ia.embeddings import Embeddings, avisos_pendentes, invalidar_vetores
from estudos.importacao.pdf import DocumentoPdf, PdfInvalido, abrir_pdf
from estudos.db.conexao import conectar
from estudos.rag.indice import abrir_indice, caminho_indice, descartar_indice, eh_corrupcao
from estudos.rag.trechos import TrechoNovo, dividir_markdown, dividir_paginas
from estudos.repos import documentos, livros
from estudos.seguranca import caminho_seguro


@dataclass
class ResumoSincronizacao:
    indexadas: int = 0
    removidas: int = 0
    trechos: int = 0
    avisos: list[str] = field(default_factory=list)
    tempo_ms: int = 0


def assinatura_fonte(con: sqlite3.Connection, fonte_id: int) -> str:
    fonte = con.execute("SELECT sha256, tipo FROM fonte WHERE id = ?", (fonte_id,)).fetchone()
    partes = [fonte["sha256"], fonte["tipo"]]
    livro = con.execute("SELECT gabarito_pdf_ini, gabarito_pdf_fim FROM livro WHERE fonte_id = ?", (fonte_id,)).fetchone()
    if livro:
        partes.append(f"{livro['gabarito_pdf_ini']}-{livro['gabarito_pdf_fim']}")
        partes += [f"{s.codigo}:{s.titulo}:{s.pagina_pdf_ini}-{s.pagina_pdf_fim}" for s in livros.listar_secoes(con, fonte_id)]
    return hashlib.sha256("|".join(map(str, partes)).encode()).hexdigest()


def assinatura_documento(con: sqlite3.Connection, raiz: Path, documento_id: int) -> str:
    """Inclui o hash do .md: duas edições no mesmo segundo têm o mesmo atualizado_em."""
    doc = con.execute("SELECT caminho, titulo FROM documento WHERE id = ?", (documento_id,)).fetchone()
    caminho = caminho_seguro(raiz, doc["caminho"])
    conteudo = hashlib.sha256(caminho.read_bytes()).hexdigest() if caminho.is_file() else "ausente"
    return f"{doc['caminho']}|{doc['titulo']}|{conteudo}"


def _inserir(indice: sqlite3.Connection, origem: str, trechos: list[TrechoNovo], tipo: str, **ids) -> int:
    for t in trechos:
        indice.execute(
            "INSERT INTO trecho (origem, fonte_id, documento_id, secao_id, tipo, titulo, texto, pagina, pagina_fim, ordem) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (origem, ids.get("fonte_id"), ids.get("documento_id"), ids.get("secao_id"), ids.get("tipo", tipo),
             t.titulo, t.texto, t.pagina, t.pagina_fim, t.ordem),
        )
    return len(trechos)


def _secao_de_cada_pagina(con: sqlite3.Connection, fonte_id: int) -> dict[int, object]:
    """Cada página fica com a seção mais profunda que a contém (o capítulo não repete o texto das subseções)."""
    dona: dict[int, object] = {}
    for s in sorted(livros.listar_secoes(con, fonte_id), key=lambda s: (s.nivel, s.pagina_pdf_ini)):
        for pagina in range(s.pagina_pdf_ini, s.pagina_pdf_fim + 1):
            dona[pagina] = s
    return dona


def _indexar_livro(indice, con, origem: str, fonte_id: int, doc: DocumentoPdf, titulo: str) -> int:
    livro = con.execute("SELECT gabarito_pdf_ini, gabarito_pdf_fim FROM livro WHERE fonte_id = ?", (fonte_id,)).fetchone()
    dona = _secao_de_cada_pagina(con, fonte_id)
    if not dona:
        paginas = [(p.indice, p.texto) for p in doc.paginas]
        return _inserir(indice, origem, dividir_paginas(paginas, titulo), "livro", fonte_id=fonte_id)
    total = 0
    grupos: list[tuple[object, list[tuple[int, str]]]] = []
    for pagina in doc.paginas:
        s = dona.get(pagina.indice)
        if s is None:
            continue  # capa, prefácio, apêndices: fora do índice (o gabarito entra abaixo)
        if grupos and grupos[-1][0] is s:
            grupos[-1][1].append((pagina.indice, pagina.texto))
        else:
            grupos.append((s, [(pagina.indice, pagina.texto)]))
    for s, paginas in grupos:
        total += _inserir(indice, origem, dividir_paginas(paginas, f"{s.codigo} {s.titulo}"), "livro",
                          fonte_id=fonte_id, secao_id=s.id)
    if livro and livro["gabarito_pdf_ini"]:
        ini, fim = livro["gabarito_pdf_ini"], livro["gabarito_pdf_fim"] or doc.total_paginas
        paginas = [(p.indice, p.texto) for p in doc.paginas if ini <= p.indice <= fim]
        total += _inserir(indice, origem, dividir_paginas(paginas, "Respostas"), "gabarito", fonte_id=fonte_id)
    return total


def indexar_fonte(indice, con, raiz: Path, fonte_id: int, avisos: list[str]) -> int | None:
    """Nº de trechos gravados; None quando a fonte não pôde ser lida (fica fora do estado para tentar de novo)."""
    fonte = con.execute("SELECT caminho, tipo FROM fonte WHERE id = ?", (fonte_id,)).fetchone()
    origem = f"fonte:{fonte_id}"
    caminho = caminho_seguro(raiz, fonte["caminho"])
    if not caminho.is_file():
        avisos.append(f"{fonte['caminho']}: arquivo não encontrado; fora da busca")
        return None
    try:
        doc = abrir_pdf(caminho)
    except PdfInvalido as e:
        avisos.append(f"{fonte['caminho']}: {e}")
        return None
    if doc.sem_texto:
        avisos.append(f"{fonte['caminho']}: PDF sem texto (escaneado); fora da busca")
        return 0
    if fonte["tipo"] == "livro":
        return _indexar_livro(indice, con, origem, fonte_id, doc, caminho.stem)
    paginas = [(p.indice, p.texto) for p in doc.paginas]
    return _inserir(indice, origem, dividir_paginas(paginas, caminho.stem), fonte["tipo"], fonte_id=fonte_id)


def _indexar_documento(indice, con, raiz: Path, documento_id: int, avisos: list[str]) -> int | None:
    doc = documentos.obter(con, documento_id)
    try:
        corpo = documentos.ler_corpo(raiz, doc)
    except FileNotFoundError:
        avisos.append(f"{doc.caminho}: arquivo não encontrado; fora da busca")
        return None
    return _inserir(indice, f"documento:{documento_id}", dividir_markdown(corpo, doc.titulo), doc.tipo,
                    documento_id=documento_id, secao_id=doc.secao_id)


_travas: dict[str, threading.Lock] = {}
_trava_das_travas = threading.Lock()
_pendentes: set[threading.Thread] = set()


def _trava(caminho: Path) -> threading.Lock:
    with _trava_das_travas:
        return _travas.setdefault(str(caminho.resolve()), threading.Lock())


def sincronizar(
    con: sqlite3.Connection, raiz: Path, caminho_indice_: Path | None = None, esperar: bool = True,
    embeddings: Embeddings | None = None,
) -> ResumoSincronizacao:
    """Uma sincronização por índice de cada vez. Com esperar=False, quem chega durante outra sincronização não espera:
    devolve um aviso e quem chamou segue buscando no índice como ele está."""
    caminho = caminho_indice_ or caminho_indice(raiz)
    trava = _trava(caminho)
    if not trava.acquire(blocking=esperar):
        return ResumoSincronizacao(avisos=["sincronização em andamento; resultados podem ainda não incluir tudo"])
    try:
        try:
            return _sincronizar(con, raiz, caminho, embeddings)
        except sqlite3.DatabaseError as erro:
            if not eh_corrupcao(erro):
                raise
            descartar_indice(raiz, caminho)
            resumo = _sincronizar(con, raiz, caminho, embeddings)
            resumo.avisos.insert(0, "índice de busca estava corrompido e foi reconstruído")
            return resumo
    finally:
        trava.release()


def agendar_sincronizacao(raiz: Path, arquivo_banco: Path, embeddings: Embeddings | None = None) -> threading.Thread | None:
    """Sincroniza numa thread própria (com sua própria conexão), sem segurar quem pediu. Já havendo uma agendada para a
    mesma matéria, não agenda outra (devolve None)."""
    chave = str(raiz.resolve())
    if any(t.name == f"indexacao-{chave}" and t.is_alive() for t in list(_pendentes)):
        return None

    def rodar() -> None:
        con = conectar(arquivo_banco)
        try:
            sincronizar(con, raiz, embeddings=embeddings)
        except Exception:  # índice é derivável; a próxima busca tenta de novo
            pass
        finally:
            con.close()
            _pendentes.discard(threading.current_thread())

    tarefa = threading.Thread(target=rodar, name=f"indexacao-{chave}", daemon=True)
    _pendentes.add(tarefa)
    tarefa.start()
    return tarefa


def aguardar_sincronizacoes(timeout: float | None = None) -> bool:
    """Espera as sincronizações em segundo plano terminarem; True se todas terminaram dentro do prazo."""
    limite = None if timeout is None else time.monotonic() + timeout
    for tarefa in list(_pendentes):
        tarefa.join(None if limite is None else max(0.0, limite - time.monotonic()))
    return not any(t.is_alive() for t in list(_pendentes))


def _vetorizar(indice: sqlite3.Connection, embeddings: Embeddings) -> None:
    """Vetores dos trechos que ainda não têm; outro modelo (ou outra dimensão) apaga os antigos e refaz."""
    meta = dict(indice.execute("SELECT chave, valor FROM meta").fetchall())
    if meta.get("modelo") != embeddings.nome or meta.get("dimensao") != str(embeddings.dimensao):
        indice.execute("BEGIN")
        indice.execute("UPDATE trecho SET vetor = NULL")
        indice.execute("INSERT OR REPLACE INTO meta (chave, valor) VALUES ('modelo', ?), ('dimensao', ?)",
                       (embeddings.nome, str(embeddings.dimensao)))
        indice.execute("COMMIT")
    while True:
        lote = indice.execute("SELECT id, titulo, texto FROM trecho WHERE vetor IS NULL ORDER BY id LIMIT 64").fetchall()
        if not lote:
            return
        vetores = embeddings.de_trechos([f"{l['titulo']}\n{l['texto']}" for l in lote])
        indice.execute("BEGIN")
        indice.executemany("UPDATE trecho SET vetor = ? WHERE id = ?",
                           [(v.astype("float32").tobytes(), l["id"]) for v, l in zip(vetores, lote)])
        indice.execute("COMMIT")


def _sincronizar(
    con: sqlite3.Connection, raiz: Path, caminho_indice_: Path, embeddings: Embeddings | None = None
) -> ResumoSincronizacao:
    inicio = time.perf_counter()
    resumo = ResumoSincronizacao()
    atuais = {f"fonte:{r['id']}": assinatura_fonte(con, r["id"]) for r in con.execute("SELECT id FROM fonte")}
    atuais |= {
        f"documento:{r['id']}": assinatura_documento(con, raiz, r["id"]) for r in con.execute("SELECT id FROM documento")
    }
    indice = abrir_indice(raiz, caminho_indice_)
    try:
        estado = {r["origem"]: r["assinatura"] for r in indice.execute("SELECT origem, assinatura FROM estado")}
        for origem in set(estado) - set(atuais):
            indice.execute("BEGIN")
            indice.execute("DELETE FROM trecho WHERE origem = ?", (origem,))
            indice.execute("DELETE FROM estado WHERE origem = ?", (origem,))
            indice.execute("COMMIT")
            resumo.removidas += 1
        for origem, assinatura in sorted(atuais.items()):
            if estado.get(origem) == assinatura:
                continue
            tipo, numero = origem.split(":")
            indice.execute("BEGIN")
            indice.execute("DELETE FROM trecho WHERE origem = ?", (origem,))
            indice.execute("DELETE FROM estado WHERE origem = ?", (origem,))
            if tipo == "fonte":
                gravados = indexar_fonte(indice, con, raiz, int(numero), resumo.avisos)
            else:
                gravados = _indexar_documento(indice, con, raiz, int(numero), resumo.avisos)
            if gravados is not None:
                indice.execute(
                    "INSERT INTO estado (origem, assinatura, indexado_em) VALUES (?, ?, ?)",
                    (origem, assinatura, datetime.datetime.now().isoformat(timespec="seconds")),
                )
                resumo.indexadas += 1
            indice.execute("COMMIT")
        if embeddings is not None:
            _vetorizar(indice, embeddings)
        resumo.trechos = indice.execute("SELECT count(*) FROM trecho").fetchone()[0]
    except BaseException:
        if indice.in_transaction:
            indice.execute("ROLLBACK")
        raise
    finally:
        indice.close()
        invalidar_vetores(caminho_indice_)
    resumo.avisos += avisos_pendentes()
    resumo.tempo_ms = round((time.perf_counter() - inicio) * 1000)
    return resumo
