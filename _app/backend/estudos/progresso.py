"""Progresso derivado e a tela Hoje.

Nada aqui pede registro manual: o estado das sessões e dos tópicos sai do plano (datas), das marcações e das resoluções
gravadas. As regras ficam explícitas para dar para conferir (spec 2026-11-05-redesenho-hoje-design, §5):

- questão trabalhada: tem marcação ou resolução gravada;
- sessão: feita (à mão ou com alguma questão trabalhada), hoje, passou ou futura;
- tópico: hoje (coberto pela sessão de hoje), visto (à mão, coberto por sessão que já passou, ou com questão
  trabalhada) ou a seguir. Tópico e sessão se cobrem quando têm uma seção em comum; sessão sem seção cobre os tópicos
  ligados às listas das suas questões.
"""

import re
import sqlite3
from datetime import date, timedelta

from estudos.repos import unidades

DIAS_RETA_FINAL = 7
DIAS_PROXIMOS = 7
CODIGO_SECAO = re.compile(r"(?<![\d.])(\d{1,2}\.\d{1,2})(?![\d.])")
NEGRITO = re.compile(r"\*\*(.+?)\*\*")


# ---------- leituras básicas ----------

def _marcacoes(con: sqlite3.Connection) -> dict[int, str]:
    return {l[0]: l[1] for l in con.execute("SELECT questao_id, estado FROM marcacao")}


def _resolucoes(con: sqlite3.Connection) -> dict[int, int]:
    """questão → documento de resolução gravado."""
    return {
        l[0]: l[1]
        for l in con.execute("SELECT questao_id, id FROM documento WHERE questao_id IS NOT NULL ORDER BY id")
    }


def _questoes(con: sqlite3.Connection) -> dict[int, dict]:
    """Todas as questões com a lista e a unidade, na ordem das listas."""
    return {
        l["id"]: dict(l)
        for l in con.execute(
            "SELECT q.id, q.rotulo, q.lista_id, l.codigo AS lista_codigo, l.titulo AS lista_titulo, u.numero AS unidade, "
            "l.unidade_id FROM questao q JOIN lista l ON l.id = q.lista_id JOIN unidade u ON u.id = l.unidade_id "
            "ORDER BY u.numero, l.ordem, l.id, q.ordem"
        )
    }


def _secoes_por_codigo(con: sqlite3.Connection) -> dict[str, int]:
    """Código → seção, do livro principal primeiro (o mesmo código pode existir em mais de um livro)."""
    mapa: dict[str, int] = {}
    for l in con.execute(
        "SELECT s.id, s.codigo FROM secao_livro s JOIN livro l ON l.fonte_id = s.livro_id "
        "ORDER BY l.papel = 'principal' DESC, l.fonte_id, s.pagina_pdf_ini"
    ):
        mapa.setdefault(l["codigo"], l["id"])
    return mapa


def _secoes_das_listas(con: sqlite3.Connection) -> dict[int, set[int]]:
    mapa: dict[int, set[int]] = {}
    for l in con.execute("SELECT lista_id, secao_id FROM lista_secao"):
        mapa.setdefault(l[0], set()).add(l[1])
    return mapa


def _secao(con: sqlite3.Connection, secao_id: int) -> dict:
    l = con.execute(
        "SELECT s.id AS secao_id, s.codigo, s.titulo, s.livro_id AS fonte_id, f.caminho, s.pagina_pdf_ini "
        "FROM secao_livro s JOIN fonte f ON f.id = s.livro_id WHERE s.id = ?",
        (secao_id,),
    ).fetchone()
    return dict(l)


def trabalhadas(con: sqlite3.Connection) -> set[int]:
    return set(_marcacoes(con)) | set(_resolucoes(con))


# ---------- sessões ----------

def _titulo_e_detalhe(foco_md: str) -> tuple[str, str]:
    """"**15.5 Aplicações** — massa, centro de massa" → ("15.5 Aplicações", "massa, centro de massa")."""
    primeira = next((l.strip() for l in foco_md.splitlines() if l.strip()), "")
    negrito = NEGRITO.search(primeira)
    if not negrito:
        return primeira, ""
    resto = (primeira[: negrito.start()] + primeira[negrito.end():]).strip()
    return negrito.group(1).strip(), resto.lstrip("—–-· ").strip()


def _estado_sessao(linha: sqlite3.Row, questoes: list[int], feitas: set[int], hoje: date) -> str:
    if linha["feito"] or any(q in feitas for q in questoes):
        return "feita"
    if not linha["data"]:
        return "futura"
    if linha["data"] == hoje.isoformat():
        return "hoje"
    return "passou" if linha["data"] < hoje.isoformat() else "futura"


def sessoes(con: sqlite3.Connection, hoje: date) -> list[dict]:
    """Todas as sessões do plano, em ordem de data, com estado derivado e as seções que cobrem."""
    feitas = trabalhadas(con)
    por_codigo = _secoes_por_codigo(con)
    secoes_lista = _secoes_das_listas(con)
    questoes = _questoes(con)
    resultado = []
    for l in con.execute(
        "SELECT s.*, u.numero AS unidade FROM sessao_estudo s JOIN unidade u ON u.id = s.unidade_id "
        "ORDER BY s.data IS NULL, s.data, u.numero, s.ordem"
    ):
        ids = [r[0] for r in con.execute(
            "SELECT questao_id FROM sessao_questao WHERE sessao_id = ?", (l["id"],)
        )]
        ids.sort(key=lambda q: list(questoes).index(q) if q in questoes else 0)
        secoes: set[int] = set()
        for q in ids:
            if q in questoes:
                secoes |= secoes_lista.get(questoes[q]["lista_id"], set())
        titulo, detalhe = _titulo_e_detalhe(l["foco_md"])
        for codigo in CODIGO_SECAO.findall(titulo):
            if codigo in por_codigo:
                secoes.add(por_codigo[codigo])
        resultado.append({
            "id": l["id"], "codigo": l["codigo"], "data": l["data"], "unidade": l["unidade"],
            "titulo": titulo, "detalhe": detalhe, "estado": _estado_sessao(l, ids, feitas, hoje),
            "questao_ids": ids, "secao_ids": sorted(secoes),
            "listas": sorted({questoes[q]["lista_id"] for q in ids if q in questoes}),
        })
    return resultado


def _foco(lista: list[dict], hoje: date) -> dict | None:
    """A sessão de hoje; senão, a próxima com data."""
    iso = hoje.isoformat()
    de_hoje = [s for s in lista if s["data"] == iso]
    if de_hoje:
        return de_hoje[0]
    futuras = [s for s in lista if s["data"] and s["data"] > iso]
    return futuras[0] if futuras else None


def _material(con: sqlite3.Connection, sessao: dict) -> dict:
    marcas = _marcacoes(con)
    resolucoes = _resolucoes(con)
    questoes = _questoes(con)
    secao_ids = sessao["secao_ids"]
    codigos = {_secao(con, s)["codigo"] for s in secao_ids}
    marca = ",".join("?" * len(secao_ids))
    resumos = [
        {"id": l["id"], "titulo": l["titulo"]}
        for l in con.execute(
            f"SELECT id, titulo FROM documento WHERE tipo = 'resumo' AND secao_id IN ({marca}) ORDER BY titulo", secao_ids
        )
    ] if secao_ids else []
    formulas = [
        {"id": l["id"], "titulo": l["titulo"]}
        for l in con.execute("SELECT id, titulo, secao_id FROM formula ORDER BY unidade_id, ordem")
        if l["secao_id"] in secao_ids or codigos & set(CODIGO_SECAO.findall(l["titulo"]))
    ]
    return {
        **{k: sessao[k] for k in ("id", "codigo", "data", "unidade", "titulo", "detalhe", "estado")},
        "secoes": [_secao(con, s) for s in secao_ids],
        "resumos": resumos,
        "formulas": formulas,
        "questoes": [
            {
                "id": q, "rotulo": questoes[q]["rotulo"], "lista_id": questoes[q]["lista_id"],
                "lista_codigo": questoes[q]["lista_codigo"], "unidade": questoes[q]["unidade"],
                "estado": marcas.get(q), "resolucao_id": resolucoes.get(q),
            }
            for q in sessao["questao_ids"] if q in questoes
        ],
    }


# ---------- tópicos ----------

def topicos(con: sqlite3.Connection, unidade_id: int, hoje: date, todas: list[dict] | None = None) -> list[dict]:
    """Tópicos da unidade com estado derivado e o placar das questões ligadas (listas do tópico ou das suas seções)."""
    todas = sessoes(con, hoje) if todas is None else todas
    marcas = _marcacoes(con)
    feitas = trabalhadas(con)
    questoes = _questoes(con)
    secoes_lista = _secoes_das_listas(con)
    foco = _foco(todas, hoje)
    iso = hoje.isoformat()
    resultado = []
    for t in con.execute("SELECT * FROM topico WHERE unidade_id = ? ORDER BY ordem, id", (unidade_id,)):
        secoes = {l[0] for l in con.execute("SELECT secao_id FROM topico_secao WHERE topico_id = ?", (t["id"],))}
        listas_ids = {l[0] for l in con.execute("SELECT lista_id FROM lista_topico WHERE topico_id = ?", (t["id"],))}
        listas_ids |= {lista for lista, ss in secoes_lista.items() if ss & secoes}
        ids = [q for q, d in questoes.items() if d["lista_id"] in listas_ids]

        def cobre(s: dict) -> bool:
            # a seção decide; a ligação lista→tópico só vale para sessão sem seção (listas como a "L5" ligam vários tópicos)
            if s["secao_ids"]:
                return bool(secoes & set(s["secao_ids"]))
            return bool(listas_ids & set(s["listas"]))

        if foco and foco["data"] == iso and cobre(foco):
            estado = "hoje"
        elif (
            t["status"] == "visto"
            or any(q in feitas for q in ids)
            or any(s["data"] and s["data"] < iso and cobre(s) for s in todas)
        ):
            estado = "visto"
        else:
            estado = "a seguir"
        codigos = [
            l[0] for l in con.execute(
                "SELECT s.codigo FROM topico_secao ts JOIN secao_livro s ON s.id = ts.secao_id "
                "WHERE ts.topico_id = ? ORDER BY s.pagina_pdf_ini", (t["id"],)
            )
        ]
        resultado.append({
            "id": t["id"], "titulo": t["titulo"], "estado": estado, "secoes": codigos,
            "total": len(ids), "trabalhadas": sum(1 for q in ids if q in feitas),
            "ok": sum(1 for q in ids if marcas.get(q) == "ok"),
            "err": sum(1 for q in ids if marcas.get(q) == "err"),
            "dub": sum(1 for q in ids if marcas.get(q) == "dub"),
        })
    return resultado


# ---------- revisar e próximos dias ----------

def revisar(con: sqlite3.Connection) -> list[dict]:
    """Questões com ✗ ou ? de todas as unidades, agrupadas por lista, na ordem das unidades e das listas."""
    marcas = _marcacoes(con)
    grupos: dict[int, dict] = {}
    for q, d in _questoes(con).items():
        if marcas.get(q) not in ("err", "dub"):
            continue
        g = grupos.setdefault(d["lista_id"], {
            "lista_id": d["lista_id"], "lista_codigo": d["lista_codigo"], "lista_titulo": d["lista_titulo"],
            "unidade": d["unidade"], "questoes": [],
        })
        g["questoes"].append({"id": q, "rotulo": d["rotulo"], "estado": marcas[q]})
    return list(grupos.values())


def proximos(con: sqlite3.Connection, hoje: date, todas: list[dict]) -> list[dict]:
    """Sessões e eventos de hoje até daqui a 7 dias, em ordem de data."""
    inicio, fim = hoje.isoformat(), (hoje + timedelta(days=DIAS_PROXIMOS)).isoformat()
    itens = [
        {"tipo": "sessao", "data": s["data"], "hora_inicio": None, "codigo": s["codigo"], "titulo": s["titulo"],
         "estado": s["estado"], "unidade": s["unidade"]}
        for s in todas if s["data"] and inicio <= s["data"] <= fim
    ]
    for e in con.execute(
        "SELECT e.tipo, e.data, e.hora_inicio, e.descricao, u.numero FROM evento e LEFT JOIN unidade u ON u.id = e.unidade_id "
        "WHERE e.data BETWEEN ? AND ?", (inicio, fim)
    ):
        itens.append({"tipo": e["tipo"], "data": e["data"], "hora_inicio": e["hora_inicio"], "codigo": None,
                      "titulo": e["descricao"], "estado": None, "unidade": e["numero"]})
    return sorted(itens, key=lambda i: (i["data"], i["tipo"] != "sessao", i["hora_inicio"] or ""))


# ---------- a tela ----------

def hoje(con: sqlite3.Connection, dia: date) -> dict:
    atual = unidades.unidade_atual(con, dia)
    todas = sessoes(con, dia)
    foco = _foco(todas, dia)
    prova = None
    if atual and atual.data_prova and atual.data_prova >= dia.isoformat():
        evento = con.execute(
            "SELECT data, hora_inicio FROM evento WHERE unidade_id = ? AND tipo = 'prova' AND data >= ? ORDER BY data LIMIT 1",
            (atual.id, dia.isoformat()),
        ).fetchone()
        dias = (date.fromisoformat(evento["data"]) - dia).days
        prova = {"data": evento["data"], "hora_inicio": evento["hora_inicio"], "unidade": atual.numero, "dias": dias}
    return {
        "data": dia.isoformat(),
        "unidade": atual.numero if atual else None,
        "prova": prova,
        "reta_final": bool(prova and prova["dias"] <= DIAS_RETA_FINAL),
        "sessao": _material(con, foco) if foco else None,
        "proximos": proximos(con, dia, todas),
        "revisar": revisar(con),
        "topicos": topicos(con, atual.id, dia, todas) if atual else [],
    }
