"""Pipeline de importação: arquivo → fonte → classificação → extração → proposta (rascunho) → confirmação.

A proposta é um JSON editável; nada do domínio é gravado antes de `confirmar`, que aplica tudo numa única operação
(desfazível). Itens extraídos ou vinculados com confiança abaixo do limiar vão marcados com "revisar": true.
"""

import dataclasses
import shutil
import sqlite3
from pathlib import Path, PurePath

from estudos.config import Settings
from estudos.erros import DadoInvalido
from estudos.historico import Operacao, operacao
from estudos.importacao.classificador import TIPOS, Classificacao, classificar
from estudos.importacao.idioma import normalizar
from estudos.importacao.parsers.calendario import extrair_calendario
from estudos.importacao.parsers.livro import extrair_livro
from estudos.importacao.parsers.lista import extrair_listas
from estudos.importacao.parsers.programa import TopicoExtraido, extrair_programa
from estudos.importacao.parsers.turma import extrair_turma
from estudos.importacao.pdf import DocumentoPdf, abrir_pdf
from estudos.importacao.vinculo import Candidato, melhores, unidade_majoritaria
from estudos.modelos import Importacao, QuestaoEntrada
from estudos.repos import _base, eventos, fontes, importacoes, listas, livros, materia, topicos, turma, unidades
from estudos.repos.fontes import sha256_arquivo
from estudos.seguranca import caminho_seguro

ORIGEM = "importado"
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


def _secoes_por_livro(con: sqlite3.Connection) -> dict[int, tuple[str, list[Candidato]]]:
    resultado = {}
    for livro in con.execute(
        "SELECT l.fonte_id, coalesce(nullif(l.titulo_obra, ''), f.titulo) AS titulo, l.papel FROM livro l "
        "JOIN fonte f ON f.id = l.fonte_id ORDER BY l.papel = 'principal' DESC, l.fonte_id"
    ):
        candidatos = [Candidato((s.id, s.codigo), f"{s.codigo} {s.titulo}") for s in livros.listar_secoes(con, livro["fonte_id"])]
        resultado[livro["fonte_id"]] = (livro["titulo"], candidatos)
    return resultado


def _unidade_por_numero(con: sqlite3.Connection) -> dict[int, int]:
    return {u.numero: u.id for u in unidades.listar(con)}


# ---------------- propostas por tipo ----------------
def _proposta_topico(t: TopicoExtraido, secoes: dict, existentes: dict[str, int], settings: Settings) -> dict:
    vinculos = []
    for fonte_id, (titulo_livro, candidatos) in secoes.items():
        for v in melhores(t.titulo, candidatos, settings.limiar_vinculo):
            secao_id, codigo = v.chave
            vinculos.append({"secao_id": secao_id, "codigo": codigo, "livro": titulo_livro, "confianca": v.confianca,
                             "aceito": True, "revisar": _revisar(v.confianca, settings)})
    return {
        "titulo": t.titulo,
        "existente_id": existentes.get(normalizar(t.titulo)),
        "secoes": vinculos,
        "filhos": [_proposta_topico(f, secoes, existentes, settings) for f in t.filhos],
    }


def _propor_programa(con, doc: DocumentoPdf, settings: Settings) -> dict:
    secoes = _secoes_por_livro(con)
    por_numero = _unidade_por_numero(con)
    propostas = []
    for u in extrair_programa(doc.texto()):
        existentes = {}
        if u.numero in por_numero:
            existentes = {normalizar(t.titulo): t.id for t in topicos.listar(con, por_numero[u.numero])}
        propostas.append({
            "numero": u.numero, "titulo": u.titulo, "existente_id": por_numero.get(u.numero),
            "topicos": [_proposta_topico(t, secoes, existentes, settings) for t in u.topicos],
        })
    return {"unidades": propostas, "revisar": not propostas}


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


def _propor_turma(con, doc: DocumentoPdf, settings: Settings) -> dict:
    t = extrair_turma(doc.texto())
    cadastrados = _livros_cadastrados(con)
    referencias = []
    for r in t.referencias:
        [v] = melhores(r.texto, cadastrados, settings.limiar_vinculo) or [None]
        referencias.append({"texto": r.texto, "papel": r.papel, "fonte_id": v.chave if v else None,
                            "confianca": v.confianca if v else 0.0, "revisar": bool(v) and _revisar(v.confianca, settings)})
    return {"professor": t.professor, "email": t.email, "horarios": [list(h) for h in t.horarios],
            "referencias": referencias, "criterios": t.criterios, "revisar": t.professor is None}


def _propor_livro(con, doc: DocumentoPdf, settings: Settings, nome: str) -> dict:
    extraido = extrair_livro(doc)
    principal = livros.principal(con)
    equivalencias = []
    if principal is not None:
        candidatos = [Candidato((s.id, s.codigo), f"{s.codigo} {s.titulo}") for s in livros.listar_secoes(con, principal.fonte_id)]
        for s in extraido.secoes:
            for v in melhores(s.titulo, candidatos, settings.limiar_vinculo):
                equivalencias.append({"codigo": s.codigo, "equivalente_id": v.chave[0], "equivalente_codigo": v.chave[1],
                                      "confianca": v.confianca, "aceito": True, "revisar": _revisar(v.confianca, settings)})
    return {
        "papel": "complementar" if principal else "principal",
        "titulo_obra": PurePath(nome).stem,
        "offset_pagina": extraido.offset_pagina,
        "gabarito": list(extraido.gabarito) if extraido.gabarito else None,
        "origem": extraido.origem,
        "sem_texto": extraido.sem_texto,
        "avisos": extraido.avisos,
        "secoes": [{**dataclasses.asdict(s), "revisar": _revisar(s.confianca, settings)} for s in extraido.secoes],
        "equivalencias": equivalencias,
        "revisar": extraido.offset_pagina is None or not extraido.secoes,
    }


def _unidade_da_secao(con, secao_id: int) -> list[int]:
    return [r[0] for r in con.execute(
        "SELECT u.numero FROM topico_secao ts JOIN topico t ON t.id = ts.topico_id JOIN unidade u ON u.id = t.unidade_id "
        "WHERE ts.secao_id = ?", (secao_id,)
    )]


def _propor_lista(con, doc: DocumentoPdf, settings: Settings, nome: str) -> dict:
    arquivo = extrair_listas(doc, nome)
    principal = livros.principal(con)
    todos_topicos = [
        (t, u.numero) for u in unidades.listar(con) for t in topicos.listar(con, u.id)
    ]
    candidatos_topico = [Candidato((t.id, numero), t.titulo) for t, numero in todos_topicos]
    vinculos_topicos = []
    for conteudo in arquivo.conteudos:
        for v in melhores(conteudo, candidatos_topico, settings.limiar_vinculo):
            vinculos_topicos.append({"topico_id": v.chave[0], "titulo": v.titulo, "unidade": v.chave[1],
                                     "confianca": v.confianca, "aceito": True, "revisar": _revisar(v.confianca, settings)})
    propostas = []
    for lista in arquivo.listas:
        secao = livros.secao_por_codigo(con, principal.fonte_id, lista.secao_livro) if principal and lista.secao_livro else None
        if arquivo.unidade is not None:
            numero, confianca = arquivo.unidade, 1.0
        else:
            votos = (_unidade_da_secao(con, secao.id) if secao else []) + [v["unidade"] for v in vinculos_topicos]
            numero, confianca = unidade_majoritaria(votos)
        existente = con.execute("SELECT id FROM lista WHERE codigo = ?", (lista.codigo,)).fetchone()
        diff = None
        if existente:
            atuais = {q.rotulo for q in listas.listar_questoes(con, existente["id"])}
            novos = [q.rotulo for q in lista.questoes]
            diff = {"lista_id": existente["id"], "novas": [r for r in novos if r not in atuais],
                    "mantidas": [r for r in novos if r in atuais], "ausentes": sorted(atuais - set(novos))}
        propostas.append({
            "codigo": lista.codigo, "titulo": lista.titulo, "secao_id": secao.id if secao else None,
            "unidade": {"numero": numero, "confianca": round(confianca, 4), "revisar": numero is None or _revisar(confianca, settings)},
            "topicos": vinculos_topicos,
            "questoes": [dataclasses.asdict(q) for q in lista.questoes],
            "existente": diff,
        })
    unidade_arquivo = {"numero": arquivo.unidade, "confianca": 1.0 if arquivo.unidade else 0.0}
    return {"formato": arquivo.formato, "modo": "mesclar", "titulo": arquivo.titulo, "unidade": unidade_arquivo,
            "referencia_livro": arquivo.referencia_livro, "conteudos": arquivo.conteudos, "avisos": arquivo.avisos,
            "listas": propostas, "revisar": not propostas}


def propor(con, doc: DocumentoPdf, tipo: str, nome: str, settings: Settings, classificacao: Classificacao | None) -> dict:
    if classificacao is not None:
        base = {"classificacao": {"tipo": classificacao.tipo, "confianca": classificacao.confianca,
                                  "sinais": classificacao.sinais, "revisar": _revisar(classificacao.confianca, settings)}}
    else:
        base = {"classificacao": {"tipo": tipo, "confianca": 1.0, "sinais": {}, "revisar": False}}
    if tipo == "programa":
        return {**base, **_propor_programa(con, doc, settings)}
    if tipo == "calendario":
        return {**base, **_propor_calendario(con, doc)}
    if tipo == "turma":
        return {**base, **_propor_turma(con, doc, settings)}
    if tipo == "livro":
        return {**base, **_propor_livro(con, doc, settings, nome)}
    if tipo == "lista":
        return {**base, **_propor_lista(con, doc, settings, nome)}
    return {**base, "observacao": "Arquivo registrado; o conteúdo será indexado para busca na Fase 4."}


# ---------------- entrada e reprocessamento ----------------
def receber_arquivo(con, raiz: Path, origem: Path, nome_original: str, settings: Settings) -> Importacao:
    sha = sha256_arquivo(origem)
    existente = con.execute("SELECT id FROM fonte WHERE sha256 = ?", (sha,)).fetchone()
    if existente:
        imp = importacoes.por_fonte(con, existente["id"])
        if imp is not None:
            return imp
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
    proposta = propor(con, doc, tipo, nome_original, settings, classificacao)
    return importacoes.obter(con, importacoes.criar(con, fonte_id, tipo, proposta))


def reprocessar(con, raiz: Path, importacao_id: int, tipo: str, settings: Settings) -> Importacao:
    if tipo not in TIPOS:
        raise DadoInvalido(f"Tipo desconhecido: {tipo}")
    imp = importacoes.obter(con, importacao_id)
    if imp.estado != "proposta":
        raise DadoInvalido(f"A importação {importacao_id} já está '{imp.estado}'.")
    fonte = _base.obter(con, "fonte", {"id": imp.fonte_id})
    doc = abrir_pdf(caminho_seguro(raiz, fonte["caminho"]))
    proposta = propor(con, doc, tipo, Path(fonte["caminho"]).name, settings, None)
    with operacao(con, f"Marcar {Path(fonte['caminho']).name} como {tipo}", raiz) as op:
        _base.atualizar(op, "fonte", {"id": imp.fonte_id}, {"tipo": tipo})
    importacoes.atualizar_proposta(con, importacao_id, proposta, tipo)
    return importacoes.obter(con, importacao_id)


def descartar(con, importacao_id: int) -> None:
    imp = importacoes.obter(con, importacao_id)
    if imp.estado != "proposta":
        raise DadoInvalido(f"A importação {importacao_id} já está '{imp.estado}'.")
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


def confirmar(con, raiz: Path, importacao_id: int) -> dict:
    imp = importacoes.obter(con, importacao_id)
    if imp.estado != "proposta":
        raise DadoInvalido(f"A importação {importacao_id} já está '{imp.estado}'.")
    fonte = _base.obter(con, "fonte", {"id": imp.fonte_id})
    resumo = dict.fromkeys(("unidades", "topicos", "eventos", "secoes", "listas", "questoes", "vinculos", "criterios"), 0)
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
        importacoes.marcar(con, importacao_id, "confirmada")
    return resumo
