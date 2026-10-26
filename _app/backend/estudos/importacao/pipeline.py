"""Pipeline de importação: arquivo → fonte → classificação → extração → proposta (rascunho) → confirmação.

A proposta é um JSON editável; nada do domínio é gravado antes de `confirmar`, que aplica tudo numa única operação
(desfazível). Itens extraídos ou vinculados com confiança abaixo do limiar vão marcados com "revisar": true.
"""

import copy
import dataclasses
import shutil
import sqlite3
from pathlib import Path, PurePath

from estudos.config import Settings
from estudos.erros import Conflito, DadoInvalido
from estudos.historico import Operacao, operacao
from estudos.importacao.classificador import TIPOS, Classificacao, classificar
from estudos.importacao.idioma import normalizar
from estudos.importacao.parsers.calendario import extrair_calendario
from estudos.importacao.parsers.livro import extrair_livro
from estudos.importacao.parsers.lista import extrair_listas
from estudos.importacao.parsers.programa import TopicoExtraido, extrair_programa
from estudos.importacao.parsers.turma import extrair_turma
from estudos.importacao.pdf import DocumentoPdf, abrir_pdf
from estudos.importacao.vinculo import Candidato, construir_idf, melhores, pontuar_com_motivo, semantica_de, unidade_majoritaria
from estudos.modelos import Importacao, QuestaoEntrada
from estudos.rag.indexador import agendar_sincronizacao
from estudos.workspace import ARQUIVO_DB
from estudos.repos import _base, eventos, fontes, importacoes, listas, livros, materia, topicos, turma, unidades
from estudos.repos.fontes import sha256_arquivo
from estudos.seguranca import caminho_seguro

ORIGEM = "importado"
_MAX_TOPICOS_POR_CONTEUDO = 3
_ERROS_DE_PROPOSTA = (KeyError, TypeError, ValueError, AttributeError, IndexError)
PASTA_POR_TIPO = {
    "programa": "fontes/documentos", "calendario": "fontes/documentos", "turma": "fontes/documentos",
    "livro": "fontes/livros", "lista": "fontes/listas", "slides": "fontes/slides", "prova": "fontes/provas",
    "anotacao": "fontes/anotacoes", "outro": "fontes/documentos",
}


# ---------------- utilidades ----------------
def _destino_livre(raiz: Path, pasta: str, nome: str) -> str:
    base = PurePath(nome)
    candidato, n = f"{pasta}/{base.name}", 2
    while (raiz / candidato).exists():
        candidato = f"{pasta}/{base.stem}-{n}{base.suffix}"
        n += 1
    return candidato


def _revisar(confianca: float, settings: Settings) -> bool:
    return confianca < settings.limiar_confianca


def contar_pendencias(proposta) -> int:
    """Quantos itens da proposta pedem revisão (chave "revisar": true em qualquer nível)."""
    if isinstance(proposta, dict):
        return int(proposta.get("revisar") is True) + sum(contar_pendencias(v) for v in proposta.values())
    if isinstance(proposta, list):
        return sum(contar_pendencias(v) for v in proposta)
    return 0


def _secoes_por_livro(con: sqlite3.Connection) -> list[tuple[str, list[Candidato], dict[str, float]]]:
    resultado = []
    for livro in con.execute(
        "SELECT l.fonte_id, coalesce(nullif(l.titulo_obra, ''), f.titulo) AS titulo, l.papel FROM livro l "
        "JOIN fonte f ON f.id = l.fonte_id ORDER BY l.papel = 'principal' DESC, l.fonte_id"
    ):
        candidatos = [Candidato((s.id, s.codigo), f"{s.codigo} {s.titulo}") for s in livros.listar_secoes(con, livro["fonte_id"])]
        resultado.append((livro["titulo"], candidatos, construir_idf([c.titulo for c in candidatos])))
    return resultado


def _unidade_por_numero(con: sqlite3.Connection) -> dict[int, int]:
    return {u.numero: u.id for u in unidades.listar(con)}


def _todos_topicos(con: sqlite3.Connection) -> list[tuple[object, int]]:
    return [(t, u.numero) for u in unidades.listar(con) for t in topicos.listar(con, u.id)]


# ---------------- propostas por tipo ----------------
# Cada proposta tem duas partes: o que foi extraído do arquivo (fixo) e o que é derivado do banco atual (vínculos,
# unidade das listas, itens já existentes). A parte derivada é refeita sempre que a proposta é lida ou confirmada,
# então a ordem em que os arquivos chegam não muda o resultado. As decisões da revisão sobrevivem ao recálculo:
# vínculo recusado ("aceito": false), vínculo incluído à mão e campo escolhido à mão ("manual": true).
def _mesclar(novos: list[dict], anteriores, chave) -> list[dict]:
    antigos = {}
    for v in anteriores if isinstance(anteriores, list) else []:
        if isinstance(v, dict):
            try:
                antigos[chave(v)] = v
            except (KeyError, TypeError):
                continue
    vistos = set()
    for v in novos:
        vistos.add(chave(v))
        anterior = antigos.get(chave(v))
        if anterior is not None and anterior.get("aceito") is False:
            v["aceito"] = False
        if anterior is not None and anterior.get("revisar") is False:
            v["revisar"] = False  # já conferido (na revisão ou num cálculo anterior): não volta a pedir revisão
    return novos + [v for k, v in antigos.items() if v.get("manual") and k not in vistos]


def _topico_extraido(t: TopicoExtraido) -> dict:
    return {"titulo": t.titulo, "filhos": [_topico_extraido(f) for f in t.filhos]}


def _propor_programa(doc: DocumentoPdf) -> dict:
    propostas = [
        {"numero": u.numero, "titulo": u.titulo, "topicos": [_topico_extraido(t) for t in u.topicos]}
        for u in extrair_programa(doc.texto())
    ]
    return {"unidades": propostas, "revisar": not propostas}


def _sentido(settings: Settings) -> dict:
    """Parâmetros de sentido dos vínculos (embeddings), vazios quando desligados: aí a nota é só a regra, como antes."""
    semantica = semantica_de(settings)
    return {"semantica": semantica, "peso": settings.peso_sentido_vinculo} if semantica is not None else {}


def _derivar_topico(item: dict, secoes: list, existentes: dict[str, int], settings: Settings, sentido: dict | None = None) -> None:
    sentido = _sentido(settings) if sentido is None else sentido
    vinculos = []
    for titulo_livro, candidatos, idf in secoes:
        for v in melhores(item["titulo"], candidatos, settings.limiar_vinculo, idf=idf, **sentido):
            secao_id, codigo = v.chave
            vinculos.append({"secao_id": secao_id, "codigo": codigo, "livro": titulo_livro, "confianca": v.confianca,
                             "por": v.por, "aceito": True, "revisar": _revisar(v.confianca, settings)})
    item["existente_id"] = existentes.get(normalizar(item["titulo"]))
    item["secoes"] = _mesclar(vinculos, item.get("secoes"), lambda v: v["secao_id"])
    for filho in item.get("filhos", []):
        _derivar_topico(filho, secoes, existentes, settings, sentido)


def _derivar_programa(con, proposta: dict, settings: Settings) -> None:
    secoes = _secoes_por_livro(con)
    sentido = _sentido(settings)
    por_numero = _unidade_por_numero(con)
    for u in proposta.get("unidades", []):
        existentes = {}
        if u["numero"] in por_numero:
            existentes = {normalizar(t.titulo): t.id for t in topicos.listar(con, por_numero[u["numero"]])}
        u["existente_id"] = por_numero.get(u["numero"])
        for t in u.get("topicos", []):
            _derivar_topico(t, secoes, existentes, settings, sentido)


def _propor_calendario(con, doc: DocumentoPdf) -> dict:
    periodo = materia.obter(con).periodo or ""
    ano_padrao = int(periodo[:4]) if periodo[:4].isdigit() else None
    cal = extrair_calendario(doc.texto(), ano_padrao)
    dados = dataclasses.asdict(cal)
    dados["revisar"] = cal.ano is None or not cal.unidades
    return dados


def _livros_cadastrados(con) -> list[Candidato]:
    return [
        Candidato(l["fonte_id"], f"{l['titulo_obra']} {l['titulo']} {l['caminho']}")
        for l in con.execute(
            "SELECT l.fonte_id, l.titulo_obra, f.titulo, f.caminho FROM livro l JOIN fonte f ON f.id = l.fonte_id"
        )
    ]


def _propor_turma(doc: DocumentoPdf) -> dict:
    t = extrair_turma(doc.texto())
    return {"professor": t.professor, "email": t.email, "horarios": [list(h) for h in t.horarios],
            "referencias": [{"texto": r.texto, "papel": r.papel} for r in t.referencias], "criterios": t.criterios,
            "revisar": t.professor is None or len(t.professor.split()) < 2}


def _derivar_turma(con, proposta: dict, settings: Settings) -> None:
    sentido = _sentido(settings)
    cadastrados = _livros_cadastrados(con)
    idf = construir_idf([c.titulo for c in cadastrados])
    for r in proposta.get("referencias", []):
        if r.get("manual"):
            continue
        [v] = melhores(r["texto"], cadastrados, settings.limiar_vinculo, idf=idf, **sentido) or [None]
        r.update(fonte_id=v.chave if v else None, confianca=v.confianca if v else 0.0, por=v.por if v else None,
                 revisar=bool(v) and _revisar(v.confianca, settings))


def _propor_livro(doc: DocumentoPdf, settings: Settings, nome: str) -> dict:
    extraido = extrair_livro(doc)
    return {
        "titulo_obra": PurePath(nome).stem,
        "offset_pagina": extraido.offset_pagina,
        "gabarito": list(extraido.gabarito) if extraido.gabarito else None,
        "origem": extraido.origem,
        "sem_texto": extraido.sem_texto,
        "avisos": extraido.avisos,
        "secoes": [{**dataclasses.asdict(s), "revisar": _revisar(s.confianca, settings)} for s in extraido.secoes],
        "revisar": extraido.offset_pagina is None or not extraido.secoes,
    }


def _derivar_livro(con, proposta: dict, settings: Settings, fonte_id: int) -> None:
    sentido = _sentido(settings)
    principal = livros.principal(con)
    outro = principal if principal is not None and principal.fonte_id != fonte_id else None
    if not proposta.get("papel_manual"):
        proposta["papel"] = "complementar" if outro else "principal"
    equivalencias = []
    if outro is not None:
        candidatos = [Candidato((s.id, s.codigo), f"{s.codigo} {s.titulo}") for s in livros.listar_secoes(con, outro.fonte_id)]
        idf = construir_idf([c.titulo for c in candidatos])
        for s in proposta.get("secoes", []):
            for v in melhores(s["titulo"], candidatos, settings.limiar_vinculo, idf=idf, **sentido):
                equivalencias.append({"codigo": s["codigo"], "equivalente_id": v.chave[0], "equivalente_codigo": v.chave[1],
                                      "confianca": v.confianca, "por": v.por, "aceito": True, "revisar": _revisar(v.confianca, settings)})
    proposta["equivalencias"] = _mesclar(equivalencias, proposta.get("equivalencias"),
                                         lambda e: (e["codigo"], e["equivalente_id"]))
    # Tópicos que já existem (programa importado antes do livro) ganham a seção mais parecida deste livro
    candidatos_secao = [Candidato(s["codigo"], f"{s['codigo']} {s['titulo']}") for s in proposta.get("secoes", [])]
    idf = construir_idf([c.titulo for c in candidatos_secao])
    vinculos = []
    for t, numero in _todos_topicos(con):
        for v in melhores(t.titulo, candidatos_secao, settings.limiar_vinculo, idf=idf, **sentido):
            vinculos.append({"topico_id": t.id, "titulo": t.titulo, "unidade": numero, "codigo": v.chave,
                             "confianca": v.confianca, "por": v.por, "aceito": True, "revisar": _revisar(v.confianca, settings)})
    proposta["topicos"] = _mesclar(vinculos, proposta.get("topicos"), lambda t: (t["topico_id"], t["codigo"]))


def _unidade_da_secao(con, secao_id: int) -> list[int]:
    return [r[0] for r in con.execute(
        "SELECT u.numero FROM topico_secao ts JOIN topico t ON t.id = ts.topico_id JOIN unidade u ON u.id = t.unidade_id "
        "WHERE ts.secao_id = ?", (secao_id,)
    )]


def _propor_lista(doc: DocumentoPdf, nome: str) -> dict:
    arquivo = extrair_listas(doc, nome)
    propostas = [
        {"codigo": lista.codigo, "titulo": lista.titulo, "secao_livro": lista.secao_livro,
         "questoes": [dataclasses.asdict(q) for q in lista.questoes], "revisar": not lista.questoes}
        for lista in arquivo.listas
    ]
    unidade_arquivo = {"numero": arquivo.unidade, "confianca": 1.0 if arquivo.unidade else 0.0}
    return {"formato": arquivo.formato, "modo": "mesclar", "titulo": arquivo.titulo, "unidade": unidade_arquivo,
            "referencia_livro": arquivo.referencia_livro, "conteudos": arquivo.conteudos, "avisos": arquivo.avisos,
            "listas": propostas, "revisar": not propostas or bool(arquivo.avisos)}


def _derivar_lista(con, proposta: dict, settings: Settings) -> None:
    sentido = _sentido(settings)
    principal = livros.principal(con)
    candidatos_topico = [Candidato((t.id, numero), t.titulo) for t, numero in _todos_topicos(con)]
    idf = construir_idf([c.titulo for c in candidatos_topico])
    # Cada conteúdo vota em cada unidade com o tópico mais parecido dela ("Limite e continuidade" casa com dois
    # tópicos da unidade 1); a unidade vencedora é a de maior soma, e só os tópicos dela viram vínculo da lista.
    # Para votar basta metade do limiar (é evidência somada); para virar vínculo vale o limiar inteiro.
    vinculos_topicos, votos_conteudos = [], []
    for conteudo in proposta.get("conteudos", []):
        pontuados = pontuar_com_motivo(conteudo, candidatos_topico, settings.limiar_vinculo / 2, idf=idf, **sentido)
        por_unidade: dict[int, float] = {}
        for score, c, _ in pontuados:
            por_unidade[c.chave[1]] = max(por_unidade.get(c.chave[1], 0.0), score)
        votos_conteudos += por_unidade.items()
        fortes = [(s, c, por) for s, c, por in pontuados if s >= settings.limiar_vinculo][:_MAX_TOPICOS_POR_CONTEUDO]
        for score, c, por in fortes:
            topico_id, numero = c.chave
            confianca = round(score, 4)
            vinculos_topicos.append({"topico_id": topico_id, "titulo": c.titulo, "unidade": numero,
                                     "confianca": confianca, "por": por, "aceito": True, "revisar": _revisar(confianca, settings)})
    explicita = (proposta.get("unidade") or {}).get("numero")
    por_secao = proposta.get("formato") == "por_secao"
    for item in proposta.get("listas", []):
        # Na lista por seção o código é o da seção (propostas antigas não guardavam "secao_livro")
        codigo_secao = item.get("secao_livro", item["codigo"] if por_secao else None)
        if not item.get("secao_manual") and ("secao_livro" in item or por_secao):
            secao = livros.secao_por_codigo(con, principal.fonte_id, codigo_secao) if principal and codigo_secao else None
            item["secao_id"] = secao.id if secao else None
        anterior = item.get("unidade") if isinstance(item.get("unidade"), dict) else {}
        if anterior.get("manual"):
            numero = anterior.get("numero")
        else:
            if explicita is not None:
                numero, confianca = explicita, 1.0
            else:
                votos = [(n, 1.0) for n in (_unidade_da_secao(con, item["secao_id"]) if item.get("secao_id") else [])]
                numero, confianca = unidade_majoritaria(votos + votos_conteudos)
            item["unidade"] = {"numero": numero, "confianca": round(confianca, 4),
                               "revisar": numero is None or _revisar(confianca, settings)}
        existente = con.execute("SELECT id FROM lista WHERE codigo = ?", (item["codigo"],)).fetchone()
        diff = None
        if existente:
            atuais = {q.rotulo for q in listas.listar_questoes(con, existente["id"])}
            novos = [q["rotulo"] for q in item.get("questoes", [])]
            diff = {"lista_id": existente["id"], "novas": [r for r in novos if r not in atuais],
                    "mantidas": [r for r in novos if r in atuais], "ausentes": sorted(atuais - set(novos))}
        unicos: dict[int, dict] = {}  # dois conteúdos podem casar com o mesmo tópico: fica o vínculo mais forte
        for v in vinculos_topicos:
            if (numero is None or v["unidade"] == numero) and v["confianca"] > unicos.get(v["topico_id"], {}).get("confianca", -1):
                unicos[v["topico_id"]] = dict(v)
        item["topicos"] = _mesclar(list(unicos.values()), item.get("topicos"), lambda t: t["topico_id"])
        item["existente"] = diff


def derivar(con, tipo: str, proposta: dict, settings: Settings, fonte_id: int) -> dict:
    """Recalcula a parte da proposta que depende do banco atual, mantendo as decisões da revisão; devolve uma cópia."""
    nova = copy.deepcopy(proposta)
    if tipo == "programa":
        _derivar_programa(con, nova, settings)
    elif tipo == "turma":
        _derivar_turma(con, nova, settings)
    elif tipo == "livro":
        _derivar_livro(con, nova, settings, fonte_id)
    elif tipo == "lista":
        _derivar_lista(con, nova, settings)
    return nova


def propor(con, doc: DocumentoPdf, tipo: str, nome: str, settings: Settings, classificacao: Classificacao | None,
           fonte_id: int) -> dict:
    if classificacao is not None:
        base = {"classificacao": {"tipo": classificacao.tipo, "confianca": classificacao.confianca,
                                  "sinais": classificacao.sinais, "revisar": _revisar(classificacao.confianca, settings)}}
    else:
        base = {"classificacao": {"tipo": tipo, "confianca": 1.0, "sinais": {}, "revisar": False}}
    if tipo == "programa":
        extraido = _propor_programa(doc)
    elif tipo == "calendario":
        extraido = _propor_calendario(con, doc)
    elif tipo == "turma":
        extraido = _propor_turma(doc)
    elif tipo == "livro":
        extraido = _propor_livro(doc, settings, nome)
    elif tipo == "lista":
        extraido = _propor_lista(doc, nome)
    else:
        extraido = {"observacao": "Arquivo registrado; o conteúdo entra na busca."}
    return derivar(con, tipo, {**base, **extraido}, settings, fonte_id)


def atualizar_derivados(con, imp: Importacao, settings: Settings) -> Importacao:
    """Refaz a parte derivada de uma proposta pendente com o banco atual. Grava só se ninguém mudou a proposta entre
    a leitura e a escrita (edição ou confirmação concorrente): nesse caso vale o que está no banco."""
    if imp.estado != "proposta":
        return imp
    nova = derivar(con, imp.tipo, imp.proposta, settings, imp.fonte_id)
    if nova != imp.proposta:
        importacoes.trocar_proposta(con, imp.id, imp.proposta, nova)
    return importacoes.obter(con, imp.id)


def para_leitura(con, imp: Importacao, settings: Settings) -> Importacao:
    """Para as rotas de leitura: proposta que não dá para recalcular (malformada na edição) volta como está; o erro
    aparece ao confirmar, com a mensagem de proposta inconsistente."""
    try:
        return atualizar_derivados(con, imp, settings)
    except _ERROS_DE_PROPOSTA:
        return imp


def _marcar_decisoes(tipo: str, antes: dict, depois: dict) -> None:
    """Compara a proposta editada com a que estava gravada e marca o que o usuário escolheu à mão."""
    def ids(itens, chave) -> set:
        return {chave(v) for v in itens or [] if isinstance(v, dict)}

    def novos_viram_manuais(itens, anteriores, chave) -> None:
        conhecidos = ids(anteriores, chave)
        for v in itens or []:
            if isinstance(v, dict) and chave(v) not in conhecidos:
                v["manual"] = True

    if tipo == "lista":
        anteriores = {l["codigo"]: l for l in antes.get("listas", []) if isinstance(l, dict) and "codigo" in l}
        for item in depois.get("listas", []):
            a = anteriores.get(item.get("codigo")) if isinstance(item, dict) else None
            if a is None:
                continue
            unidade, antiga = item.get("unidade"), a.get("unidade") or {}
            # Escolher outra unidade ou confirmar a sugerida (tirar o "revisar") é decisão do usuário
            if isinstance(unidade, dict) and (
                unidade.get("numero") != antiga.get("numero")
                or (unidade.get("revisar") is False and antiga.get("revisar") is True)
            ):
                unidade["manual"] = True
            if item.get("secao_id") != a.get("secao_id"):
                item["secao_manual"] = True
            novos_viram_manuais(item.get("topicos"), a.get("topicos"), lambda t: t.get("topico_id"))
    elif tipo == "livro":
        if depois.get("papel") != antes.get("papel"):
            depois["papel_manual"] = True
        novos_viram_manuais(depois.get("topicos"), antes.get("topicos"), lambda t: (t.get("topico_id"), t.get("codigo")))
        novos_viram_manuais(depois.get("equivalencias"), antes.get("equivalencias"),
                            lambda e: (e.get("codigo"), e.get("equivalente_id")))
    elif tipo == "turma":
        anteriores = {r.get("texto"): r for r in antes.get("referencias", []) if isinstance(r, dict)}
        for r in depois.get("referencias", []):
            a = anteriores.get(r.get("texto")) if isinstance(r, dict) else None
            if a is not None and r.get("fonte_id") != a.get("fonte_id"):
                r["manual"] = True


def editar(con, importacao_id: int, proposta: dict) -> Importacao:
    """Grava a proposta revisada. O que o usuário decidiu fica marcado e sobrevive aos recálculos seguintes."""
    atual = importacoes.obter(con, importacao_id)
    try:
        _marcar_decisoes(atual.tipo, atual.proposta, proposta)
    except _ERROS_DE_PROPOSTA:
        pass  # proposta malformada: grava como veio; confirmar devolve o erro de proposta inconsistente
    importacoes.atualizar_proposta(con, importacao_id, proposta)
    return importacoes.obter(con, importacao_id)


# ---------------- entrada e reprocessamento ----------------
def receber_arquivo(con, raiz: Path, origem: Path, nome_original: str, settings: Settings) -> Importacao:
    sha = sha256_arquivo(origem)
    existente = con.execute("SELECT id FROM fonte WHERE sha256 = ?", (sha,)).fetchone()
    if existente:
        imp = importacoes.por_fonte(con, existente["id"])
        if imp is not None and imp.estado == "proposta":
            return imp  # mesmo arquivo ainda em revisão; descartado ou já confirmado ganha proposta nova
    doc = abrir_pdf(origem)
    classificacao = classificar(doc, nome_original)
    tipo = classificacao.tipo
    if existente:
        fonte_id = existente["id"]
    else:
        caminho = _destino_livre(raiz, PASTA_POR_TIPO[tipo], nome_original)
        destino = caminho_seguro(raiz, caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino)
        try:
            with operacao(con, f"Receber {PurePath(nome_original).name}", raiz) as op:
                fonte_id = fontes.registrar(op, tipo, caminho, PurePath(nome_original).stem, doc.total_paginas, origem=ORIGEM)
        except BaseException:
            destino.unlink(missing_ok=True)
            raise
    proposta = propor(con, doc, tipo, nome_original, settings, classificacao, fonte_id)
    return importacoes.obter(con, importacoes.criar(con, fonte_id, tipo, proposta))


def reprocessar(con, raiz: Path, importacao_id: int, tipo: str, settings: Settings) -> Importacao:
    if tipo not in TIPOS:
        raise DadoInvalido(f"Tipo desconhecido: {tipo}")
    imp = importacoes.obter(con, importacao_id)
    if imp.estado != "proposta":
        raise Conflito(f"A importação {importacao_id} já está '{imp.estado}'.")
    fonte = _base.obter(con, "fonte", {"id": imp.fonte_id})
    doc = abrir_pdf(caminho_seguro(raiz, fonte["caminho"]))
    proposta = propor(con, doc, tipo, Path(fonte["caminho"]).name, settings, None, imp.fonte_id)
    with operacao(con, f"Marcar {Path(fonte['caminho']).name} como {tipo}", raiz) as op:
        _base.atualizar(op, "fonte", {"id": imp.fonte_id}, {"tipo": tipo})
    importacoes.atualizar_proposta(con, importacao_id, proposta, tipo)
    return importacoes.obter(con, importacao_id)


def descartar(con, importacao_id: int) -> None:
    imp = importacoes.obter(con, importacao_id)
    if imp.estado != "proposta":
        raise Conflito(f"A importação {importacao_id} já está '{imp.estado}'.")
    importacoes.marcar(con, importacao_id, "descartada")


# ---------------- aplicação (confirmar) ----------------
def _unidade(op: Operacao, numero: int, titulo: str = "") -> int:
    por_numero = _unidade_por_numero(op.con)
    if numero in por_numero:
        return por_numero[numero]
    return unidades.criar(op, numero, titulo, origem=ORIGEM)


def _aplicar_topico(op: Operacao, unidade_id: int, item: dict, pai_id: int | None, resumo: dict) -> None:
    existentes = {normalizar(t.titulo): t.id for t in topicos.listar(op.con, unidade_id)}
    tid = existentes.get(normalizar(item["titulo"]))
    if tid is None:
        tid = topicos.criar(op, unidade_id, item["titulo"], pai_id=pai_id, origem=ORIGEM)
        resumo["topicos"] += 1
    for s in item.get("secoes", []):
        if s.get("aceito"):
            livros.vincular_topico(op, tid, s["secao_id"], confianca=s.get("confianca"), confirmado=True)
            resumo["vinculos"] += 1
    for filho in item.get("filhos", []):
        _aplicar_topico(op, unidade_id, filho, tid, resumo)


def _aplicar_programa(op: Operacao, proposta: dict, resumo: dict) -> None:
    for u in proposta.get("unidades", []):
        antes = len(_unidade_por_numero(op.con))
        uid = _unidade(op, int(u["numero"]), u.get("titulo", ""))
        resumo["unidades"] += len(_unidade_por_numero(op.con)) - antes
        for t in u.get("topicos", []):
            _aplicar_topico(op, uid, t, None, resumo)


def _evento_existe(con, tipo: str, data: str, unidade_id: int | None) -> int | None:
    linha = con.execute(
        "SELECT id FROM evento WHERE tipo = ? AND data = ? AND unidade_id IS ?", (tipo, data, unidade_id)
    ).fetchone()
    return linha["id"] if linha else None


def _aplicar_calendario(op: Operacao, proposta: dict, resumo: dict) -> None:
    def criar(e: dict, unidade_id: int | None) -> None:
        if _evento_existe(op.con, e["tipo"], e["data"], unidade_id) is None:
            eventos.criar(op, e["tipo"], e["data"], unidade_id=unidade_id, hora_inicio=e.get("hora_inicio"),
                          hora_fim=e.get("hora_fim"), descricao=e.get("descricao", ""), origem=ORIGEM)
            resumo["eventos"] += 1

    for u in proposta.get("unidades", []):
        uid = _unidade(op, int(u["numero"]))
        for aula in u.get("aulas", []):
            criar(aula, uid)
        prova = u.get("prova")
        if prova:
            atual = op.con.execute("SELECT id FROM evento WHERE tipo = 'prova' AND unidade_id = ?", (uid,)).fetchone()
            if atual:
                _base.atualizar(op, "evento", {"id": atual["id"]}, {
                    "data": prova["data"], "hora_inicio": prova.get("hora_inicio"), "hora_fim": prova.get("hora_fim")})
            else:
                criar(prova, uid)
    for e in proposta.get("eventos", []):
        criar(e, None)


def _definir_principal(op: Operacao, fonte_id: int) -> None:
    for outro in op.con.execute("SELECT fonte_id FROM livro WHERE papel = 'principal' AND fonte_id <> ?", (fonte_id,)):
        _base.atualizar(op, "livro", {"fonte_id": outro["fonte_id"]}, {"papel": "complementar"})
    _base.atualizar(op, "livro", {"fonte_id": fonte_id}, {"papel": "principal"})


def _aplicar_turma(op: Operacao, proposta: dict, resumo: dict) -> None:
    campos = {k: v for k, v in (("professor", proposta.get("professor")), ("email_professor", proposta.get("email"))) if v}
    if campos:
        materia.atualizar(op, **campos)
    if proposta.get("horarios"):
        turma.definir_horarios(op, [tuple(h) for h in proposta["horarios"]])
    if proposta.get("criterios"):
        turma.definir_criterios(op, proposta["criterios"], origem=ORIGEM)
        resumo["criterios"] = len(proposta["criterios"])
    for r in proposta.get("referencias", []):
        if r.get("fonte_id") and r.get("papel") == "principal":
            _definir_principal(op, r["fonte_id"])


def _aplicar_livro(op: Operacao, proposta: dict, fonte_id: int, resumo: dict) -> None:
    if _base.obter(op.con, "livro", {"fonte_id": fonte_id}) is None:
        gabarito = proposta.get("gabarito") or [None, None]
        livros.criar(op, fonte_id, "complementar", titulo_obra=proposta.get("titulo_obra", ""),
                     offset_pagina=proposta.get("offset_pagina") or 0,
                     gabarito_pdf_ini=gabarito[0], gabarito_pdf_fim=gabarito[1])
    if proposta.get("papel") == "principal":
        _definir_principal(op, fonte_id)
    ids = {}
    for s in proposta.get("secoes", []):
        atual = livros.secao_por_codigo(op.con, fonte_id, s["codigo"])
        valores = {"titulo": s["titulo"], "pagina_pdf_ini": s["pagina_pdf_ini"], "pagina_pdf_fim": s["pagina_pdf_fim"]}
        if atual:
            _base.atualizar(op, "secao_livro", {"id": atual.id}, valores)
            ids[s["codigo"]] = atual.id
        else:
            ids[s["codigo"]] = livros.criar_secao(op, fonte_id, s["codigo"], s["titulo"], s["pagina_pdf_ini"],
                                                  s["pagina_pdf_fim"], nivel=s.get("nivel"), origem=ORIGEM,
                                                  confianca=s.get("confianca"))
            resumo["secoes"] += 1
    for e in proposta.get("equivalencias", []):
        if e.get("aceito") and e["codigo"] in ids:
            livros.vincular_equivalente(op, ids[e["codigo"]], e["equivalente_id"])
            resumo["vinculos"] += 1
    for t in proposta.get("topicos", []):
        if t.get("aceito") and t["codigo"] in ids and _base.obter(op.con, "topico", {"id": t["topico_id"]}):
            livros.vincular_topico(op, t["topico_id"], ids[t["codigo"]], confianca=t.get("confianca"), confirmado=True)
            resumo["vinculos"] += 1
    if proposta.get("papel") == "principal":
        # Listas por seção confirmadas antes do livro têm o código da seção ("15.4") e ainda nenhuma seção ligada;
        # só códigos com ponto, para uma lista "1" (nome de arquivo) não virar o capítulo 1
        for lista in op.con.execute(
            "SELECT id, codigo FROM lista WHERE id NOT IN (SELECT lista_id FROM lista_secao)"
        ).fetchall():
            if "." in lista["codigo"] and lista["codigo"] in ids:
                listas.vincular_secao(op, lista["id"], ids[lista["codigo"]])
                resumo["vinculos"] += 1


def _entradas_existentes(con, lista_id: int) -> list[QuestaoEntrada]:
    campos = ("rotulo", "linha", "enunciado_md", "expressao", "pagina_pdf", "figura", "chave_legada")
    return [
        QuestaoEntrada(**{c: l[c] for c in campos})
        for l in con.execute("SELECT * FROM questao WHERE lista_id = ? ORDER BY ordem, id", (lista_id,))
    ]


def _aplicar_lista(op: Operacao, proposta: dict, fonte_id: int, resumo: dict) -> None:
    modo = proposta.get("modo", "mesclar")
    if modo not in ("mesclar", "substituir"):
        raise DadoInvalido(f"Modo de importação de lista inválido: {modo}")
    for item in proposta.get("listas", []):
        numero = (item.get("unidade") or {}).get("numero")
        if numero is None:
            raise DadoInvalido(f"Defina a unidade da lista {item['codigo']} antes de confirmar.")
        unidade_id = _unidade(op, int(numero))
        existente = op.con.execute("SELECT id, fonte_id FROM lista WHERE codigo = ?", (item["codigo"],)).fetchone()
        if existente:
            lista_id = existente["id"]
            if existente["fonte_id"] is None:
                listas.atualizar(op, lista_id, fonte_id=fonte_id)
        else:
            lista_id = listas.criar(op, item["codigo"], item["titulo"], unidade_id, fonte_id=fonte_id, origem=ORIGEM)
            resumo["listas"] += 1
        novas = [QuestaoEntrada(rotulo=q["rotulo"], linha=q["linha"], enunciado_md=q.get("enunciado_md", ""),
                                pagina_pdf=q.get("pagina_pdf")) for q in item.get("questoes", [])]
        if modo == "substituir" or not existente:
            entradas = novas
        else:
            atuais = _entradas_existentes(op.con, lista_id)
            rotulos = {q.rotulo for q in atuais}
            importadas = {q.rotulo: q for q in novas}
            entradas = [
                dataclasses.replace(q, enunciado_md=q.enunciado_md or importadas[q.rotulo].enunciado_md,
                                    pagina_pdf=q.pagina_pdf or importadas[q.rotulo].pagina_pdf)
                if q.rotulo in importadas else q
                for q in atuais
            ] + [q for q in novas if q.rotulo not in rotulos]
        antes = len(listas.listar_questoes(op.con, lista_id))
        listas.sincronizar_questoes(op, lista_id, entradas)
        resumo["questoes"] += len(listas.listar_questoes(op.con, lista_id)) - antes
        if item.get("secao_id"):
            listas.vincular_secao(op, lista_id, item["secao_id"])
        for t in item.get("topicos", []):
            if t.get("aceito"):
                listas.vincular_topico(op, lista_id, t["topico_id"])
                resumo["vinculos"] += 1


def confirmar(con, raiz: Path, importacao_id: int, settings: Settings) -> dict:
    imp = importacoes.obter(con, importacao_id)
    if imp.estado != "proposta":
        raise Conflito(f"A importação {importacao_id} já está '{imp.estado}'.")
    fonte = _base.obter(con, "fonte", {"id": imp.fonte_id})
    resumo = dict.fromkeys(("unidades", "topicos", "eventos", "secoes", "listas", "questoes", "vinculos", "criterios"), 0)
    try:
        imp = atualizar_derivados(con, imp, settings)  # vínculos contra o banco de agora, não o do momento do envio
        if imp.estado != "proposta":
            raise Conflito(f"A importação {importacao_id} já está '{imp.estado}'.")
        _aplicar(con, raiz, imp, fonte, resumo)
    except DadoInvalido:
        raise
    except _ERROS_DE_PROPOSTA as e:
        raise DadoInvalido(f"Proposta inconsistente ({type(e).__name__}: {e}); corrija a revisão e confirme de novo.") from e
    # A importação já está gravada; indexar (pode levar segundos num livro) roda em segundo plano e nunca a desfaz
    agendar_sincronizacao(raiz, raiz / ARQUIVO_DB)
    resumo["indexacao"] = "em segundo plano"
    return resumo


def _aplicar(con, raiz: Path, imp: Importacao, fonte: dict, resumo: dict) -> None:
    with operacao(con, f"Importar {Path(fonte['caminho']).name}", raiz) as op:
        if imp.tipo == "programa":
            _aplicar_programa(op, imp.proposta, resumo)
        elif imp.tipo == "calendario":
            _aplicar_calendario(op, imp.proposta, resumo)
        elif imp.tipo == "turma":
            _aplicar_turma(op, imp.proposta, resumo)
        elif imp.tipo == "livro":
            _aplicar_livro(op, imp.proposta, imp.fonte_id, resumo)
        elif imp.tipo == "lista":
            _aplicar_lista(op, imp.proposta, imp.fonte_id, resumo)
        importacoes.marcar(con, imp.id, "confirmada")
