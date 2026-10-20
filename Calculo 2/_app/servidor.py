#!/usr/bin/env python3
"""
Servidor Desktop da Plataforma Multi-Disciplinas de Estudos (127.0.0.1:8765).

Recursos:
  - Gerencia múltiplas disciplinas (pastas irmãs em WORKSPACE_RAIZ);
  - Grava marcações (status.json + exercicios/STATUS.md), curso.json, exercicios.json e Markdowns;
  - Mantém histórico de backup/desfazer (.historico_undo.json);
  - Serve PDFs de listas e livros localmente com suporte a #page=N;
  - Integra o motor de RAG Estruturado em 2 níveis (rag.py) e o Agente com Skills (agente.py).
"""

import argparse
import datetime
import json
import mimetypes
import pathlib
import re
import socket
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import agente
import rag


class Servidor(ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


PLATAFORMA = "estudos-desktop"
AQUI = pathlib.Path(__file__).resolve().parent           # .../Calculo 2/_app
RAIZ_PADRAO = AQUI.parent                                # .../Calculo 2
WORKSPACE_RAIZ = RAIZ_PADRAO.parent                      # .../Refatoração Site Estudos
WEB = AQUI / "web"

ROTULO = {"ok": "acertei", "err": "errei", "dub": "dúvida"}
_trava = threading.Lock()


def listar_disciplinas() -> list:
    """Descobre todas as pastas de disciplinas dentro de WORKSPACE_RAIZ."""
    res = []
    for p in sorted(WORKSPACE_RAIZ.iterdir()):
        if not p.is_dir() or p.name.startswith(".") or p.name.startswith("_"):
            continue
        tem_curso = (p / "_app" / "dados" / "curso.json").exists()
        tem_status = (p / "status.json").exists() or (p / "resumos").exists()
        if not (tem_curso or tem_status):
            continue
        nome_exibicao = p.name
        sub = ""
        p_curso = p / "_app" / "dados" / "curso.json"
        if p_curso.exists():
            try:
                c = json.loads(p_curso.read_text(encoding="utf-8"))
                nome_exibicao = c.get("nome", p.name)
                sub = c.get("subtituloGeral", "")
            except Exception:
                pass
        res.append({
            "pasta": p.name,
            "nome": nome_exibicao,
            "subtitulo": sub,
        })
    return res


def resolver_raiz_disciplina(nome_pasta: str | None) -> pathlib.Path:
    if not nome_pasta:
        return RAIZ_PADRAO
    limpo = pathlib.Path(urllib.parse.unquote(nome_pasta)).name
    cand = (WORKSPACE_RAIZ / limpo).resolve()
    if cand.is_dir() and cand.parent == WORKSPACE_RAIZ.resolve():
        return cand
    return RAIZ_PADRAO


def criar_nova_disciplina(dados: dict) -> dict:
    nome = str(dados.get("nome", "")).strip()
    if not nome:
        raise ValueError("Informe o nome da disciplina.")
    nome_pasta = re.sub(r'[<>:"/\\|?*]', "", nome).strip()
    raiz_nova = WORKSPACE_RAIZ / nome_pasta
    if raiz_nova.exists():
        raise ValueError(f"A pasta '{nome_pasta}' já existe.")

    subtitulo = str(dados.get("subtitulo", "UFPE · 2026.2")).strip()
    for sub in ("resumos", "resolucoes", "disciplina", "livros", "exercicios", "referencia", "_app/dados", "_app/img"):
        (raiz_nova / sub).mkdir(parents=True, exist_ok=True)

    curso_inicial = {
        "id": re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-"),
        "nome": nome,
        "subtituloGeral": subtitulo,
        "atualizadoEm": datetime.date.today().strftime("%d/%m/%Y"),
        "livros": [],
        "documentos": [
            {"key": "indice", "title": "Índice da disciplina", "src": "00-INDICE.md", "unidades": [1, 2, 3], "inicial": True}
        ],
        "resumosExtraUnidade": {},
        "unidades": {},
    }
    for u, ord_str, nome_ext in ((1, "1ª", "Primeira unidade"), (2, "2ª", "Segunda unidade"), (3, "3ª", "Terceira unidade")):
        curso_inicial["unidades"][str(u)] = {
            "numero": u,
            "ordinal": ord_str,
            "eyebrow": f"{subtitulo} · {ord_str} unidade",
            "titulo": nome,
            "tituloItalico": nome_ext,
            "subtitulo": f"Acompanhamento de aulas, cronograma, listas de exercícios e resumos da {ord_str} unidade.",
            "dataProva": "",
            "tags": [f"{ord_str} unidade"],
            "ondeEstamosSubtitulo": f"Programa da {ord_str} unidade — adicione os tópicos abaixo",
            "ondeEstamos": [],
            "cronogramaTitulo": f"Cronograma — {ord_str} unidade",
            "cronogramaSubtitulo": "Sessões planejadas",
            "fases": [
                {
                    "estilo": "f1",
                    "eyebrow": "Plano de estudo",
                    "titulo": f"Sessões da {ord_str} unidade",
                    "tag": "em andamento",
                    "colunas": ["Sessão", "Data", "Foco", "Exercícios"],
                    "linhas": [],
                    "nota": "",
                }
            ],
            "resumosSubtitulo": f"Teoria da {ord_str} unidade",
            "formularioTitulo": f"Formulário essencial — {ord_str} unidade",
            "formularioSubtitulo": "Fórmulas e teoremas que precisam estar na ponta da língua",
            "formulario": [],
        }

    (raiz_nova / "_app" / "dados" / "curso.json").write_text(
        json.dumps(curso_inicial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (raiz_nova / "_app" / "dados" / "exercicios.json").write_text("[]\n", encoding="utf-8")
    (raiz_nova / "status.json").write_text('{"atualizado": "", "marcacoes": {}}\n', encoding="utf-8")
    (raiz_nova / "00-INDICE.md").write_text(
        f"# {nome} — {subtitulo}\n\nCaderno de estudos estruturado.\n", encoding="utf-8"
    )
    (raiz_nova / "SKILL-DISCIPLINA.md").write_text(
        f"---\nname: skill-disciplina-{curso_inicial['id']}\ntitle: Contexto e Regras — {nome}\n---\n\n"
        f"# Contexto da Disciplina: {nome} ({subtitulo})\n\n"
        f"- Descreva aqui as regras de correção do professor, livros-base e pontos de atenção.\n",
        encoding="utf-8",
    )
    rag.sincronizar_indice(raiz_nova, forcar=True)
    return {"ok": True, "pasta": nome_pasta, "curso": curso_inicial}


def titulo_de(texto: str, alternativa: str) -> str:
    for linha in texto.split("\n"):
        linha = linha.strip()
        if linha.startswith("# "):
            return linha[2:].split(" — ")[0].split(" · ")[0].strip()
    return alternativa


def ler_status(raiz_disc: pathlib.Path) -> dict:
    p = raiz_disc / "status.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        m = d.get("marcacoes", {})
        return m if isinstance(m, dict) else {}
    except Exception:
        return {}


def escrever_status(raiz_disc: pathlib.Path, marcacoes: dict):
    agora = datetime.datetime.now().isoformat(timespec="seconds")
    p_status = raiz_disc / "status.json"
    p_status.write_text(
        json.dumps({"atualizado": agora, "marcacoes": marcacoes}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    escrever_espelho(raiz_disc, marcacoes, agora)


def escrever_espelho(raiz_disc: pathlib.Path, marcacoes: dict, agora: str):
    p_ex = raiz_disc / "_app" / "dados" / "exercicios.json"
    try:
        ex = json.loads(p_ex.read_text(encoding="utf-8"))
    except Exception:
        return
    linhas = [
        "# Status dos exercícios",
        "",
        f"Gerado automaticamente pelo app em {agora}. Não edite à mão — o app sobrescreve.",
        "",
    ]
    for sec in ex:
        marcados = []
        for linha, nome in (("l1", "linha 1"), ("l2", "linha 2")):
            for item in sec.get(linha, []):
                v = marcacoes.get(f"{sec['sec']}-{item[0]}")
                if v:
                    marcados.append((item[0], nome, v))
        if not marcados:
            continue
        linhas.append(f"## {sec['sec']} — {sec['nome']}")
        linhas.append("")
        linhas.append("| Exercício | Linha | Status |")
        linhas.append("|---|---|---|")
        for n, nome, v in marcados:
            linhas.append(f"| {n} | {nome} | {ROTULO.get(v, v)} |")
        linhas.append("")
    errados = sorted(k for k, v in marcacoes.items() if v in ("err", "dub"))
    if errados:
        linhas += ["## A revisar", "", ", ".join(errados), ""]
    espelho = raiz_disc / "exercicios" / "STATUS.md"
    espelho.parent.mkdir(parents=True, exist_ok=True)
    espelho.write_text("\n".join(linhas), encoding="utf-8")


def montar_dados(raiz_disc: pathlib.Path) -> dict:
    p_curso = raiz_disc / "_app" / "dados" / "curso.json"
    curso = {}
    if p_curso.exists():
        try:
            curso = json.loads(p_curso.read_text(encoding="utf-8"))
        except Exception as e:
            print("ERRO lendo curso.json:", e)

    resumos = []
    pasta_resumos = raiz_disc / "resumos"
    if pasta_resumos.exists():
        for p in sorted(pasta_resumos.glob("*.md")):
            texto = p.read_text(encoding="utf-8")
            # Permite definir unidade no frontmatter ou pelo número inicial
            un_explicita = None
            m_un = re.search(r"unidade:\s*(\d+)", texto[:250], re.IGNORECASE)
            if m_un:
                un_explicita = int(m_un.group(1))
            resumos.append({
                "key": p.stem,
                "title": titulo_de(texto, p.stem),
                "src": "resumos/" + p.name,
                "grupo": "resumo",
                "un": un_explicita,
                "md": texto,
            })

    docs_cfg = curso.get("documentos", [])
    for doc in docs_cfg:
        rel = doc.get("src", "")
        p = raiz_disc / rel
        if p.exists() and p.is_file():
            resumos.append({
                "key": doc.get("key", p.stem),
                "title": doc.get("title", p.stem),
                "src": rel,
                "grupo": "documento",
                "unidades": doc.get("unidades", [1, 2, 3]),
                "inicial": bool(doc.get("inicial", False)),
                "md": p.read_text(encoding="utf-8"),
            })

    resolucoes = {}
    pasta_sol = raiz_disc / "resolucoes"
    if pasta_sol.exists():
        for p in sorted(pasta_sol.glob("*.md")):
            m = re.match(r"^(\d+)-(\d+)-(.+)$", p.stem)
            if m:
                resolucoes[f"{m.group(1)}.{m.group(2)}-{m.group(3)}"] = p.read_text(encoding="utf-8")
            else:
                resolucoes[p.stem] = p.read_text(encoding="utf-8")

    p_ex = raiz_disc / "_app" / "dados" / "exercicios.json"
    try:
        exercicios = json.loads(p_ex.read_text(encoding="utf-8")) if p_ex.exists() else []
    except Exception as e:
        exercicios = []
        print("ERRO lendo exercicios.json:", e)

    pasta_img = raiz_disc / "_app" / "img"
    figuras = sorted(p.stem for p in pasta_img.glob("*.png")) if pasta_img.exists() else []

    # Lista PDFs disponíveis em disciplina/ e livros/
    pdfs = []
    for sub in ("disciplina", "livros"):
        d_sub = raiz_disc / sub
        if d_sub.exists():
            for pdf_p in sorted(d_sub.rglob("*.pdf")):
                pdfs.append({
                    "nome": pdf_p.name,
                    "caminho": pdf_p.relative_to(raiz_disc).as_posix(),
                    "grupo": sub,
                })

    cfg_agente = agente.ler_config(AQUI)
    cfg_agente.pop("_apiKeyReal", None)

    return {
        "disciplinaAtual": raiz_disc.name,
        "disciplinas": listar_disciplinas(),
        "curso": curso,
        "resumos": resumos,
        "resolucoes": resolucoes,
        "exercicios": exercicios,
        "figuras": figuras,
        "arquivosPdf": pdfs,
        "status": ler_status(raiz_disc),
        "historicoUndo": agente.listar_historico_undo(raiz_disc),
        "configAgente": cfg_agente,
        "skills": agente.listar_skills(AQUI, raiz_disc),
        "lidoEm": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def expandir_intervalo_questoes(texto_numeros: str, instrucao_padrao: str = "Resolva o exercício.") -> list:
    """
    Converte uma string rápida como "1..4, *5, 6a, 6b, 7-10" em itens de exercicios.json:
    [[numero, enunciado, expressao, img], ...]
    """
    itens = []
    partes = [p.strip() for p in re.split(r"[,;\n]+", texto_numeros) if p.strip()]
    for parte in partes:
        estrela = False
        if parte.startswith("*") or parte.startswith("⭐"):
            estrela = True
            parte = parte.lstrip("*⭐ ").strip()
        m_range = re.match(r"^(\d+)\s*(?:\.\.|-|a|até)\s*(\d+)$", parte, re.IGNORECASE)
        if m_range:
            ini, fim = int(m_range.group(1)), int(m_range.group(2))
            passo = 1 if fim >= ini else -1
            for n in range(ini, fim + passo, passo):
                lbl = f"<b>[⭐ Prioridade]</b> {instrucao_padrao}" if estrela else instrucao_padrao
                itens.append([n, lbl, None, None])
        else:
            num_val = int(parte) if parte.isdigit() else parte
            lbl = f"<b>[⭐ Prioridade]</b> {instrucao_padrao}" if estrela else instrucao_padrao
            itens.append([num_val, lbl, None, None])
    return itens


class Handler(BaseHTTPRequestHandler):
    server_version = "PlataformaEstudosDesktop/2.0"

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("  %s\n" % (fmt % args))

    def _envia(self, corpo, tipo="application/json; charset=utf-8", codigo=200):
        if isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _arquivo(self, caminho: pathlib.Path):
        if not caminho.is_file():
            self._envia('{"erro":"nao encontrado"}', codigo=404)
            return
        tipo = mimetypes.guess_type(caminho.name)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo.endswith("javascript") or tipo.endswith("json"):
            tipo += "; charset=utf-8"
        self._envia(caminho.read_bytes(), tipo)

    def _ler_json_body(self) -> dict:
        n = int(self.headers.get("Content-Length", "0"))
        if n > 15_000_000:
            raise ValueError("Corpo da requisição grande demais.")
        raw = self.rfile.read(n) if n > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _query_params(self) -> dict:
        parsed = urllib.parse.urlparse(self.path)
        return dict(urllib.parse.parse_qsl(parsed.query))

    # ---------------- Rotas GET ----------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        rota = parsed.path
        qs = self._query_params()
        raiz_disc = resolver_raiz_disciplina(qs.get("disciplina"))

        if rota in ("/", "/index.html"):
            return self._arquivo(WEB / "index.html")
        if rota == "/api/ping":
            return self._envia(json.dumps({
                "plataforma": PLATAFORMA,
                "caderno": "calculo-2",
                "raiz": str(RAIZ_PADRAO),
                "workspace": str(WORKSPACE_RAIZ),
            }, ensure_ascii=False))
        if rota == "/api/disciplinas":
            return self._envia(json.dumps({"disciplinas": listar_disciplinas()}, ensure_ascii=False))
        if rota == "/api/dados":
            return self._envia(json.dumps(montar_dados(raiz_disc), ensure_ascii=False))
        if rota == "/api/status":
            return self._envia(json.dumps({"marcacoes": ler_status(raiz_disc)}, ensure_ascii=False))
        if rota == "/api/skills":
            return self._envia(json.dumps({"skills": agente.listar_skills(AQUI, raiz_disc)}, ensure_ascii=False))
        if rota == "/api/rag/status":
            info = rag.sincronizar_indice(raiz_disc, forcar=False)
            return self._envia(json.dumps(info, ensure_ascii=False))

        if rota.startswith("/img/"):
            partes = [urllib.parse.unquote(p) for p in rota[5:].split("/") if p]
            if len(partes) >= 2:
                r_d = resolver_raiz_disciplina(partes[0])
                return self._arquivo(r_d / "_app" / "img" / pathlib.Path(partes[-1]).name)
            elif len(partes) == 1:
                return self._arquivo(raiz_disc / "_app" / "img" / pathlib.Path(partes[0]).name)

        if rota.startswith("/arquivos/"):
            # Ex: /arquivos/Calculo%202/disciplina/listas-2026-1/Lista5_2026-1.pdf
            partes = [urllib.parse.unquote(p) for p in rota[len("/arquivos/"):].split("/") if p]
            if len(partes) >= 2:
                r_d = resolver_raiz_disciplina(partes[0])
                rel = pathlib.Path(*partes[1:])
                alvo = (r_d / rel).resolve()
                if str(alvo).startswith(str(r_d.resolve())) and alvo.is_file():
                    return self._arquivo(alvo)
            return self._envia('{"erro":"arquivo nao encontrado"}', codigo=404)

        nome = pathlib.Path(rota.lstrip("/")).name
        if nome in ("estilo.css", "app.js"):
            return self._arquivo(WEB / nome)
        self._envia('{"erro":"rota desconhecida"}', codigo=404)

    # ---------------- Rotas POST ----------------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        rota = parsed.path
        qs = self._query_params()

        try:
            corpo = self._ler_json_body()
            raiz_disc = resolver_raiz_disciplina(corpo.get("disciplina") or qs.get("disciplina"))

            if rota == "/api/status":
                novas = corpo.get("marcacoes")
                if not isinstance(novas, dict):
                    raise ValueError("Faltou o dicionário 'marcacoes'.")
                limpas = {str(k): str(v) for k, v in novas.items() if str(v) in ("ok", "err", "dub")}
                with _trava:
                    escrever_status(raiz_disc, limpas)
                return self._envia(json.dumps({"ok": True, "total": len(limpas)}))

            if rota == "/api/curso":
                novo_curso = corpo.get("curso")
                if not isinstance(novo_curso, dict):
                    raise ValueError("Objeto 'curso' inválido.")
                motivo = str(corpo.get("descricao", "Edição em curso.json na interface"))
                p_curso = raiz_disc / "_app" / "dados" / "curso.json"
                with _trava:
                    agente.registrar_backup_undo(raiz_disc, p_curso, motivo)
                    novo_curso["atualizadoEm"] = datetime.date.today().strftime("%d/%m/%Y")
                    p_curso.write_text(json.dumps(novo_curso, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    # Se informou secoesDestravar, já destrava em exercicios.json!
                    destravar = corpo.get("destravarSecoes") or []
                    if destravar:
                        p_ex = raiz_disc / "_app" / "dados" / "exercicios.json"
                        if p_ex.exists():
                            agente.registrar_backup_undo(raiz_disc, p_ex, f"Destravar seções {destravar}")
                            exs = json.loads(p_ex.read_text(encoding="utf-8"))
                            for s in exs:
                                if s.get("sec") in destravar:
                                    s["locked"] = False
                            p_ex.write_text(json.dumps(exs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                return self._envia(json.dumps({"ok": True}))

            if rota == "/api/exercicios":
                p_ex = raiz_disc / "_app" / "dados" / "exercicios.json"
                acao = corpo.get("acao", "salvar_tudo")
                with _trava:
                    exs = json.loads(p_ex.read_text(encoding="utf-8")) if p_ex.exists() else []
                    if acao == "salvar_tudo":
                        novos_ex = corpo.get("exercicios")
                        if not isinstance(novos_ex, list):
                            raise ValueError("Lista 'exercicios' inválida.")
                        agente.registrar_backup_undo(raiz_disc, p_ex, str(corpo.get("descricao", "Edição de exercícios")))
                        exs = novos_ex
                    elif acao == "toggle_lock":
                        sec_alvo = str(corpo.get("sec", ""))
                        agente.registrar_backup_undo(raiz_disc, p_ex, f"Alternar trava da seção {sec_alvo}")
                        for s in exs:
                            if str(s.get("sec")) == sec_alvo:
                                s["locked"] = not bool(s.get("locked", False))
                    elif acao == "criar_secao_rapida":
                        sec_cod = str(corpo.get("sec", "")).strip()
                        nome_sec = str(corpo.get("nome", "")).strip()
                        un_sec = int(corpo.get("un", 3))
                        pg_sec = str(corpo.get("pg", "")).strip()
                        pdf_sec = str(corpo.get("pdf", "")).strip()
                        inst_padrao = str(corpo.get("instrucaoPadrao", "Resolva o exercício.")).strip()
                        l1_raw = corpo.get("l1Itens")
                        l2_raw = corpo.get("l2Itens")
                        l1_str = str(corpo.get("l1Numeros", "")).strip()
                        l2_str = str(corpo.get("l2Numeros", "")).strip()

                        if not sec_cod or not nome_sec:
                            raise ValueError("Informe o código (ex: L7 ou 15.6) e o nome da seção/lista.")
                        l1_final = l1_raw if isinstance(l1_raw, list) else expandir_intervalo_questoes(l1_str, inst_padrao)
                        l2_final = l2_raw if isinstance(l2_raw, list) else expandir_intervalo_questoes(l2_str, inst_padrao)

                        agente.registrar_backup_undo(raiz_disc, p_ex, f"Criar lista/seção {sec_cod}")
                        exs = [s for s in exs if str(s.get("sec")) != sec_cod]
                        nova_sec = {
                            "sec": sec_cod,
                            "un": un_sec,
                            "nome": nome_sec,
                            "pg": pg_sec or f"{un_sec}ª unidade",
                            "pdf": pdf_sec or None,
                            "locked": False,
                            "l1": l1_final,
                            "l2": l2_final,
                        }
                        exs.append(nova_sec)
                    p_ex.write_text(json.dumps(exs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                return self._envia(json.dumps({"ok": True, "totalSecoes": len(exs)}))

            if rota == "/api/disciplinas":
                res = criar_nova_disciplina(corpo)
                return self._envia(json.dumps(res, ensure_ascii=False))

            if rota == "/api/markdown":
                tipo_md = str(corpo.get("tipo", "resumo"))
                nome_arq = str(corpo.get("nomeArquivo", "")).strip()
                conteudo = str(corpo.get("conteudo", "")).strip()
                if not nome_arq or not conteudo:
                    raise ValueError("Informe o nome do arquivo e o conteúdo Markdown.")
                if tipo_md == "resolucao":
                    res = agente._tool_salvar_resolucao(raiz_disc, nome_arq, conteudo)
                else:
                    res = agente._tool_salvar_resumo(raiz_disc, nome_arq, conteudo)
                return self._envia(json.dumps(res, ensure_ascii=False))

            if rota == "/api/extrair-pdf":
                res = rag.extrair_paginas_ou_questoes_pdf(
                    raiz_disc,
                    arquivo_rel=str(corpo.get("arquivo", "")),
                    pg_inicio=int(corpo.get("pgInicio", 1)),
                    pg_fim=int(corpo.get("pgFim", 3)),
                    pagina_eh_do_livro=bool(corpo.get("paginaEhDoLivro", False)),
                    offset_livro=int(corpo.get("offsetLivro", 0)),
                )
                return self._envia(json.dumps(res, ensure_ascii=False))

            if rota == "/api/rag/buscar":
                modo_b = corpo.get("modoBusca", "fts")
                if modo_b == "secao_livro":
                    res = rag.ler_secao_livro(
                        raiz_disc,
                        livro=str(corpo.get("livro", "stewart")),
                        secao=str(corpo.get("secao", "15.4")),
                        foco=str(corpo.get("foco", "teoria_e_exemplos")),
                    )
                elif modo_b == "exercicio":
                    res = rag.consultar_contexto_exercicio(
                        raiz_disc,
                        secao=str(corpo.get("secao", "15.4")),
                        numero=str(corpo.get("numero", "22")),
                    )
                else:
                    res = rag.buscar_rag(
                        raiz_disc,
                        consulta=str(corpo.get("consulta", "")),
                        secao=str(corpo.get("secao", "")),
                        tipo=str(corpo.get("tipo", "")),
                        top_k=int(corpo.get("topK", 5)),
                    )
                return self._envia(json.dumps(res, ensure_ascii=False))

            if rota == "/api/rag/reindexar":
                res = rag.sincronizar_indice(raiz_disc, forcar=True)
                return self._envia(json.dumps(res, ensure_ascii=False))

            if rota == "/api/skills":
                res = agente.salvar_skill(
                    AQUI,
                    raiz_disc,
                    skill_id=str(corpo.get("id", "")),
                    conteudo=str(corpo.get("conteudo", "")),
                    escopo=str(corpo.get("escopo", "global")),
                )
                return self._envia(json.dumps(res, ensure_ascii=False))

            if rota == "/api/config":
                res = agente.salvar_config(AQUI, corpo)
                return self._envia(json.dumps(res, ensure_ascii=False))

            if rota == "/api/agente/executar":
                skill_id = str(corpo.get("skill", "tutor-progressivo"))
                res = agente.executar_agente(AQUI, raiz_disc, skill_id, corpo)
                return self._envia(json.dumps(res, ensure_ascii=False))

            if rota == "/api/undo":
                res = agente.desfazer_ultima_acao(raiz_disc)
                return self._envia(json.dumps(res, ensure_ascii=False))

            self._envia('{"erro":"rota POST desconhecida"}', codigo=404)
        except Exception as e:
            self._envia(json.dumps({"ok": False, "erro": str(e)}, ensure_ascii=False), codigo=400)


def quem_esta_na_porta(porta: int):
    import urllib.request
    try:
        abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with abridor.open(f"http://127.0.0.1:{porta}/api/ping", timeout=1) as r:
            d = json.loads(r.read().decode("utf-8"))
        if d.get("plataforma") == PLATAFORMA and d.get("workspace") == str(WORKSPACE_RAIZ):
            return "eu"
        return "outro"
    except Exception:
        # Verifica se há qualquer socket escutando na porta
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", porta)) == 0:
                return "outro"
        return None


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--porta", type=int, default=8780)
    ap.add_argument("--sem-navegador", action="store_true")
    a = ap.parse_args()

    host = "127.0.0.1"
    porta = a.porta
    srv = None

    for tentativa in range(20):
        porta_atual = porta + tentativa
        url = f"http://127.0.0.1:{porta_atual}/"
        dono = quem_esta_na_porta(porta_atual)
        if dono == "eu":
            print("=" * 62)
            print("  Plataforma de Estudos JA ESTA ABERTA em", url)
            print("=" * 62)
            if not a.sem_navegador:
                webbrowser.open(url)
            return
        if dono == "outro":
            continue
        try:
            srv = Servidor((host, porta_atual), Handler)
            porta = porta_atual
            break
        except OSError:
            continue

    if srv is None:
        sys.exit(
            f"Nao foi possivel encontrar porta livre a partir de {a.porta}.\n"
            f"Tente rodar: python servidor.py --porta 8780"
        )
    url = f"http://127.0.0.1:{porta}/"

    # Garante sincronização inicial rápida do índice RAG
    try:
        rag.sincronizar_indice(RAIZ_PADRAO, forcar=False)
    except Exception as e:
        sys.stderr.write(f"Aviso ao sincronizar RAG inicial: {e}\n")

    print("=" * 62)
    print("  Plataforma de Estudos Desktop (Multi-Disciplinas + RAG + Agente)")
    print("=" * 62)
    print("  workspace        :", WORKSPACE_RAIZ)
    print("  no navegador     :", url)
    print("  Para parar       : Ctrl+C (ou feche esta janela).")
    print("=" * 62)
    if not a.sem_navegador:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nservidor encerrado.")


if __name__ == "__main__":
    main()
