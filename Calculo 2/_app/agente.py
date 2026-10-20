#!/usr/bin/env python3
"""
Motor de Agente de Estudos com Multi-Busca no RAG, Skills Modulares (.md),
Function Calling (gemini-3.8-flash / gemini-4-argon), Modo Pacote RAG Offline
e Sistema de Backup/Undo (.historico_undo.json).
"""

import datetime
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.request

import rag


# ---------------- Configuração Local (API Key e Modelo Padrão) ----------------
def _caminho_config(pasta_app: pathlib.Path) -> pathlib.Path:
    d = pasta_app / "dados"
    d.mkdir(parents=True, exist_ok=True)
    return d / ".config.json"


def ler_config(pasta_app: pathlib.Path) -> dict:
    p = _caminho_config(pasta_app)
    cfg = {
        "modeloPadrao": "gemini-3.8-flash",
        "modoPadrao": "api",
        "temApiKey": False,
        "apiKeyMascarada": "",
    }
    key_env = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    dados = {}
    if p.exists():
        try:
            dados = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            dados = {}
    api_key = dados.get("apiKey", "").strip() or key_env.strip()
    if dados.get("modeloPadrao"):
        cfg["modeloPadrao"] = dados["modeloPadrao"]
    if dados.get("modoPadrao"):
        cfg["modoPadrao"] = dados["modoPadrao"]
    if api_key:
        cfg["temApiKey"] = True
        cfg["apiKeyMascarada"] = api_key[:4] + "••••••••" + api_key[-4:] if len(api_key) > 8 else "••••••••"
    cfg["_apiKeyReal"] = api_key
    return cfg


def salvar_config(pasta_app: pathlib.Path, nova: dict) -> dict:
    p = _caminho_config(pasta_app)
    atual = {}
    if p.exists():
        try:
            atual = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            atual = {}
    if "apiKey" in nova and nova["apiKey"] is not None:
        k = str(nova["apiKey"]).strip()
        if k and "••••" not in k:
            atual["apiKey"] = k
        elif k == "":
            atual["apiKey"] = ""
    if "modeloPadrao" in nova:
        atual["modeloPadrao"] = nova["modeloPadrao"]
    if "modoPadrao" in nova:
        atual["modoPadrao"] = nova["modoPadrao"]
    p.write_text(json.dumps(atual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    res = ler_config(pasta_app)
    res.pop("_apiKeyReal", None)
    return res


# ---------------- Sistema de Backup / Desfazer (Undo) ----------------
def _caminho_undo(raiz_disciplina: pathlib.Path) -> pathlib.Path:
    d = raiz_disciplina / "_app" / "dados"
    d.mkdir(parents=True, exist_ok=True)
    return d / ".historico_undo.json"


def registrar_backup_undo(raiz_disciplina: pathlib.Path, caminho_arquivo: pathlib.Path, descricao: str):
    p_undo = _caminho_undo(raiz_disciplina)
    hist = []
    if p_undo.exists():
        try:
            hist = json.loads(p_undo.read_text(encoding="utf-8"))
        except Exception:
            hist = []
    rel = caminho_arquivo.relative_to(raiz_disciplina).as_posix()
    existia = caminho_arquivo.exists()
    conteudo_antigo = caminho_arquivo.read_text(encoding="utf-8") if existia else None
    hist.append({
        "id": f"undo-{int(time.time() * 1000)}",
        "data": datetime.datetime.now().isoformat(timespec="seconds"),
        "descricao": descricao,
        "arquivo": rel,
        "existia": existia,
        "conteudoAnterior": conteudo_antigo,
    })
    hist = hist[-15:]
    p_undo.write_text(json.dumps(hist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def listar_historico_undo(raiz_disciplina: pathlib.Path) -> list:
    p_undo = _caminho_undo(raiz_disciplina)
    if not p_undo.exists():
        return []
    try:
        hist = json.loads(p_undo.read_text(encoding="utf-8"))
        return [
            {"id": h["id"], "data": h["data"], "descricao": h["descricao"], "arquivo": h["arquivo"]}
            for h in reversed(hist)
        ]
    except Exception:
        return []


def desfazer_ultima_acao(raiz_disciplina: pathlib.Path) -> dict:
    p_undo = _caminho_undo(raiz_disciplina)
    if not p_undo.exists():
        return {"ok": False, "erro": "Nenhuma ação no histórico para desfazer."}
    try:
        hist = json.loads(p_undo.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "erro": "Histórico de undo corrompido."}
    if not hist:
        return {"ok": False, "erro": "Nenhuma ação no histórico para desfazer."}

    ultimo = hist.pop()
    alvo = (raiz_disciplina / ultimo["arquivo"]).resolve()
    if not str(alvo).startswith(str(raiz_disciplina.resolve())):
        return {"ok": False, "erro": "Caminho inválido no histórico."}

    if ultimo.get("existia") and ultimo.get("conteudoAnterior") is not None:
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(ultimo["conteudoAnterior"], encoding="utf-8")
    elif alvo.exists():
        alvo.unlink()

    p_undo.write_text(json.dumps(hist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rag.sincronizar_indice(raiz_disciplina, forcar=False)
    return {
        "ok": True,
        "desfeito": ultimo["descricao"],
        "arquivo": ultimo["arquivo"],
        "restantes": len(hist),
    }


# ---------------- Leitura e Edição de Skills (.md) ----------------
def _parse_frontmatter(md_text: str) -> tuple[dict, str]:
    meta = {}
    corpo = md_text
    if md_text.startswith("---"):
        partes = md_text.split("---", 2)
        if len(partes) >= 3:
            raw_yaml = partes[1].strip()
            corpo = partes[2].strip()
            chave_lista = None
            for ln in raw_yaml.split("\n"):
                ln_s = ln.strip()
                if not ln_s or ln_s.startswith("#"):
                    continue
                if ln_s.startswith("- ") and chave_lista:
                    meta.setdefault(chave_lista, []).append(ln_s[2:].strip())
                elif ":" in ln_s:
                    k, v = ln_s.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    if v == "":
                        chave_lista = k
                        meta[k] = []
                    else:
                        chave_lista = None
                        meta[k] = v
    return meta, corpo


def listar_skills(pasta_app: pathlib.Path, raiz_disciplina: pathlib.Path) -> list:
    skills = []
    pasta_skills = pasta_app / "skills"
    pasta_skills.mkdir(parents=True, exist_ok=True)
    for p in sorted(pasta_skills.glob("*.md")):
        txt = p.read_text(encoding="utf-8")
        meta, corpo = _parse_frontmatter(txt)
        skills.append({
            "id": p.stem,
            "escopo": "global",
            "arquivo": f"_app/skills/{p.name}",
            "title": meta.get("title", p.stem),
            "description": meta.get("description", ""),
            "defaultModel": meta.get("default_model", "gemini-3.8-flash"),
            "allowedTools": meta.get("allowed_tools", []),
            "conteudo": txt,
            "corpo": corpo,
        })
    p_disc = raiz_disciplina / "SKILL-DISCIPLINA.md"
    if p_disc.exists():
        txt = p_disc.read_text(encoding="utf-8")
        meta, corpo = _parse_frontmatter(txt)
        skills.append({
            "id": "SKILL-DISCIPLINA",
            "escopo": "disciplina",
            "arquivo": "SKILL-DISCIPLINA.md",
            "title": meta.get("title", "Contexto da Disciplina"),
            "description": meta.get("description", "Regras específicas do professor e da disciplina"),
            "defaultModel": "gemini-3.8-flash",
            "allowedTools": [],
            "conteudo": txt,
            "corpo": corpo,
        })
    return skills


def salvar_skill(pasta_app: pathlib.Path, raiz_disciplina: pathlib.Path, skill_id: str, conteudo: str, escopo: str = "global") -> dict:
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", skill_id.strip())
    if escopo == "disciplina" or slug.upper() == "SKILL-DISCIPLINA":
        alvo = raiz_disciplina / "SKILL-DISCIPLINA.md"
        registrar_backup_undo(raiz_disciplina, alvo, "Edição de SKILL-DISCIPLINA.md")
    else:
        pasta_skills = pasta_app / "skills"
        pasta_skills.mkdir(parents=True, exist_ok=True)
        alvo = pasta_skills / f"{slug}.md"
    alvo.write_text(conteudo.strip() + "\n", encoding="utf-8")
    return {"ok": True, "id": slug, "arquivo": str(alvo.name)}


# ---------------- Implementação das Write Tools do Agente ----------------
def _tool_salvar_resumo(raiz_disciplina: pathlib.Path, nome_arquivo: str, conteudo_md: str) -> dict:
    nome_limpo = pathlib.Path(nome_arquivo).name
    if not nome_limpo.endswith(".md"):
        nome_limpo += ".md"
    pasta_resumos = raiz_disciplina / "resumos"
    pasta_resumos.mkdir(parents=True, exist_ok=True)
    alvo = pasta_resumos / nome_limpo
    registrar_backup_undo(raiz_disciplina, alvo, f"Agente salvou resumo {nome_limpo}")
    alvo.write_text(conteudo_md.strip() + "\n", encoding="utf-8")
    rag.sincronizar_indice(raiz_disciplina, forcar=False)
    return {"ok": True, "arquivo": f"resumos/{nome_limpo}", "bytes": len(conteudo_md)}


def _tool_salvar_resolucao(raiz_disciplina: pathlib.Path, id_exercicio: str, conteudo_md: str) -> dict:
    # Converte "15.4-22" -> "15-4-22.md" ou "L5-5" -> "L5-5.md"
    limpo = id_exercicio.strip().replace(".md", "")
    m = re.match(r"^(\d+)\.(\d+)-(.+)$", limpo)
    if m:
        nome_arq = f"{m.group(1)}-{m.group(2)}-{m.group(3)}.md"
    else:
        nome_arq = f"{limpo.replace('.', '-')}.md"
    pasta_sol = raiz_disciplina / "resolucoes"
    pasta_sol.mkdir(parents=True, exist_ok=True)
    alvo = pasta_sol / nome_arq
    registrar_backup_undo(raiz_disciplina, alvo, f"Agente salvou resolução {nome_arq}")
    alvo.write_text(conteudo_md.strip() + "\n", encoding="utf-8")
    rag.sincronizar_indice(raiz_disciplina, forcar=False)
    return {"ok": True, "arquivo": f"resolucoes/{nome_arq}", "idExercicio": id_exercicio}


def _tool_adicionar_formula(raiz_disciplina: pathlib.Path, unidade: int, titulo: str, formula: str, nota: str = "") -> dict:
    p_curso = raiz_disciplina / "_app" / "dados" / "curso.json"
    if not p_curso.exists():
        return {"ok": False, "erro": "curso.json não encontrado."}
    registrar_backup_undo(raiz_disciplina, p_curso, f"Agente adicionou fórmula '{titulo}' na {unidade}ª unidade")
    curso = json.loads(p_curso.read_text(encoding="utf-8"))
    u_key = str(unidade)
    if u_key not in curso.get("unidades", {}):
        return {"ok": False, "erro": f"Unidade {unidade} não existe em curso.json"}
    form_list = curso["unidades"][u_key].setdefault("formulario", [])
    # Atualiza se já existir mesmo título
    for card in form_list:
        if card.get("titulo", "").strip().lower() == titulo.strip().lower():
            card["fml"] = formula
            card["notas"] = [nota] if nota else card.get("notas", [])
            p_curso.write_text(json.dumps(curso, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return {"ok": True, "acao": "atualizado", "titulo": titulo, "unidade": unidade}
    form_list.append({
        "titulo": titulo,
        "fml": formula,
        "notas": [nota] if nota else [],
    })
    p_curso.write_text(json.dumps(curso, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "acao": "adicionado", "titulo": titulo, "unidade": unidade}


# ---------------- Declarações de Tools para Function Calling Gemini ----------------
GEMINI_TOOLS_DECLARATIONS = [
    {
        "name": "ler_secao_livro",
        "description": "Lê a seção teórica COMPLETA e todos os Exemplos Resolvidos de uma seção do livro (Stewart ou Guidorizzi), sem corte de palavras.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "livro": {"type": "STRING", "description": "Nome ou id do livro: 'stewart' ou 'guidorizzi'"},
                "secao": {"type": "STRING", "description": "Código da seção, ex: '15.4', '14.7', '15.8'"},
                "foco": {"type": "STRING", "description": "'teoria_e_exemplos', 'exercicios', 'gabarito' ou 'tudo'"},
            },
            "required": ["secao"],
        },
    },
    {
        "name": "buscar_rag",
        "description": "Faz uma busca textual e estrutural (BM25 FTS5) em todos os resumos, resoluções, listas em PDF e exemplos dos livros.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "consulta": {"type": "STRING", "description": "Termos de busca (ex: 'coordenadas polares jacobiano area')"},
                "secao": {"type": "STRING", "description": "Filtro opcional de seção (ex: '15.4', 'L5')"},
                "tipo": {"type": "STRING", "description": "Filtro opcional: 'resumo', 'resolucao', 'lista_pdf', 'livro_teoria'"},
                "top_k": {"type": "INTEGER", "description": "Quantidade máxima de blocos a retornar (padrão 5)"},
            },
            "required": ["consulta"],
        },
    },
    {
        "name": "consultar_contexto_exercicio",
        "description": "Busca o enunciado de um exercício e, se for questão PAR do Stewart (sem gabarito), traz automaticamente os exercícios ÍMPARES vizinhos (#n-1 e #n+1) e seus gabaritos no apêndice.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "secao": {"type": "STRING", "description": "Seção do exercício (ex: '15.4', '14.3', 'L5')"},
                "numero": {"type": "STRING", "description": "Número do exercício (ex: '22', '6(b)', '38(a)')"},
            },
            "required": ["secao", "numero"],
        },
    },
    {
        "name": "conferir_calculo_python",
        "description": "Executa um script Python com math, numpy e scipy.integrate (quad, dblquad, tplquad) para validar numericamente integrais, derivadas ou Jacobianos (essencial para questões pares sem gabarito).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo_python": {"type": "STRING", "description": "Código Python usando print() para exibir o resultado numérico"},
            },
            "required": ["codigo_python"],
        },
    },
    {
        "name": "ler_status_erros",
        "description": "Retorna o histórico de exercícios que o estudante acertou, errou (✗) ou marcou com dúvida (?) em status.json.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "unidade": {"type": "INTEGER", "description": "Unidade opcional (1, 2, 3) ou 0 para todas"},
            },
        },
    },
    {
        "name": "salvar_resumo",
        "description": "Grava um resumo teórico completo em Markdown na pasta resumos/ da disciplina (com backup automático).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "nome_arquivo": {"type": "STRING", "description": "Nome do arquivo, ex: '08-integrais-duplas-polares.md'"},
                "conteudo_md": {"type": "STRING", "description": "Conteúdo completo do resumo em Markdown"},
            },
            "required": ["nome_arquivo", "conteudo_md"],
        },
    },
    {
        "name": "salvar_resolucao",
        "description": "Grava a resolução completa (N4) de um exercício em resolucoes/ (com backup automático).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "id_exercicio": {"type": "STRING", "description": "ID do exercício, ex: '15.4-22' ou 'L5-5'"},
                "conteudo_md": {"type": "STRING", "description": "Conteúdo completo da resolução em Markdown no padrão de prova"},
            },
            "required": ["id_exercicio", "conteudo_md"],
        },
    },
    {
        "name": "adicionar_formula",
        "description": "Adiciona ou atualiza um cartão no Formulário essencial da unidade indicada.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "unidade": {"type": "INTEGER", "description": "Número da unidade (1, 2 ou 3)"},
                "titulo": {"type": "STRING", "description": "Título do cartão de fórmula"},
                "formula": {"type": "STRING", "description": "Fórmula matemática em texto monoespaçado"},
                "nota": {"type": "STRING", "description": "Observação ou armadilha de prova sobre a fórmula"},
            },
            "required": ["unidade", "titulo", "formula"],
        },
    },
    {
        "name": "propor_ajuste_cronograma",
        "description": "Propõe um ajuste ou nova sessão para o cronograma da unidade (exige 1 clique de confirmação do usuário na tela).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "unidade": {"type": "INTEGER", "description": "Unidade (1, 2 ou 3)"},
                "motivo": {"type": "STRING", "description": "Justificativa pedagógica para o ajuste"},
                "sessoes_sugeridas": {
                    "type": "ARRAY",
                    "description": "Lista de sessões propostas ({s, d, t, x})",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "s": {"type": "STRING"},
                            "d": {"type": "STRING"},
                            "t": {"type": "STRING"},
                            "x": {"type": "ARRAY", "items": {"type": "STRING"}},
                        },
                    },
                },
            },
            "required": ["unidade", "motivo", "sessoes_sugeridas"],
        },
    },
]


# ---------------- Executor Local de uma Chamada de Tool ----------------
def executar_tool_local(
    raiz_disciplina: pathlib.Path,
    nome_tool: str,
    args: dict,
    arquivos_salvos: list,
    propostas_cronograma: list,
) -> dict:
    args = args or {}
    if nome_tool == "ler_secao_livro":
        return rag.ler_secao_livro(
            raiz_disciplina,
            livro=str(args.get("livro", "stewart")),
            secao=str(args.get("secao", "15.4")),
            foco=str(args.get("foco", "teoria_e_exemplos")),
        )
    if nome_tool == "buscar_rag":
        return rag.buscar_rag(
            raiz_disciplina,
            consulta=str(args.get("consulta", "")),
            secao=str(args.get("secao", "")),
            tipo=str(args.get("tipo", "")),
            top_k=int(args.get("top_k", 5)),
        )
    if nome_tool == "consultar_contexto_exercicio":
        return rag.consultar_contexto_exercicio(
            raiz_disciplina,
            secao=str(args.get("secao", "")),
            numero=str(args.get("numero", "")),
        )
    if nome_tool == "conferir_calculo_python":
        return rag.conferir_calculo_python(str(args.get("codigo_python", "")))
    if nome_tool == "ler_status_erros":
        return rag.ler_status_erros(raiz_disciplina, unidade=int(args.get("unidade", 0) or 0))
    if nome_tool == "salvar_resumo":
        res = _tool_salvar_resumo(
            raiz_disciplina,
            nome_arquivo=str(args.get("nome_arquivo", "novo-resumo.md")),
            conteudo_md=str(args.get("conteudo_md", "")),
        )
        if res.get("ok"):
            arquivos_salvos.append(res["arquivo"])
        return res
    if nome_tool == "salvar_resolucao":
        res = _tool_salvar_resolucao(
            raiz_disciplina,
            id_exercicio=str(args.get("id_exercicio", "")),
            conteudo_md=str(args.get("conteudo_md", "")),
        )
        if res.get("ok"):
            arquivos_salvos.append(res["arquivo"])
        return res
    if nome_tool == "adicionar_formula":
        res = _tool_adicionar_formula(
            raiz_disciplina,
            unidade=int(args.get("unidade", 3)),
            titulo=str(args.get("titulo", "")),
            formula=str(args.get("formula", "")),
            nota=str(args.get("nota", "")),
        )
        if res.get("ok"):
            arquivos_salvos.append("curso.json (formulário)")
        return res
    if nome_tool == "propor_ajuste_cronograma":
        prop = {
            "unidade": int(args.get("unidade", 3)),
            "motivo": str(args.get("motivo", "")),
            "sessoes": args.get("sessoes_sugeridas", []),
        }
        propostas_cronograma.append(prop)
        return {"ok": True, "status": "Proposta enviada para confirmação de 1 clique na tela."}
    return {"erro": f"Tool desconhecida: {nome_tool}"}


# ---------------- Modo 1: Empacotador Multi-Busca RAG + Skill (Zero Tokens de API) ----------------
def montar_pacote_rag_enxuto(
    pasta_app: pathlib.Path,
    raiz_disciplina: pathlib.Path,
    skill_id: str,
    parametros: dict,
) -> dict:
    """
    Executa automaticamente as múltiplas buscas no RAG em Python para a tarefa pedida
    e monta um Prompt Cirúrgico completo (com os trechos recuperados do livro, gabaritos
    de vizinhos ímpares e regras da Skill), pronto para copiar e colar em qualquer chat IA.
    """
    skills = listar_skills(pasta_app, raiz_disciplina)
    skill_ativa = next((s for s in skills if s["id"] == skill_id), skills[0] if skills else {})
    skill_disc = next((s for s in skills if s["id"] == "SKILL-DISCIPLINA"), {})

    secao = str(parametros.get("secao", "")).strip()
    numero = str(parametros.get("numero", "")).strip()
    nivel = str(parametros.get("nivel", "N4")).strip()
    unidade = int(parametros.get("unidade", 3) or 3)
    instrucao_usuario = str(parametros.get("mensagem", "")).strip()
    texto_anexo = str(parametros.get("textoAnexo", "")).strip()

    tools_log = []
    blocos_contexto = []

    def _rodar_busca(nome_t, args_t):
        t0 = time.time()
        ret = executar_tool_local(raiz_disciplina, nome_t, args_t, [], [])
        dt = round((time.time() - t0) * 1000)
        txt_ret = json.dumps(ret, ensure_ascii=False, indent=2)
        tools_log.append({
            "tool": nome_t,
            "args": args_t,
            "tempoMs": dt,
            "charsRetorno": len(txt_ret),
        })
        return ret

    if skill_id == "tutor-progressivo" and secao and numero:
        ctx_ex = _rodar_busca("consultar_contexto_exercicio", {"secao": secao, "numero": numero})
        blocos_contexto.append(f"### Contexto do Exercício {secao} #{numero} (RAG Local)\n```json\n{json.dumps(ctx_ex, ensure_ascii=False, indent=2)}\n```")
        if re.match(r"^\d+\.\d+$", secao):
            sec_livro = _rodar_busca("ler_secao_livro", {"livro": "stewart", "secao": secao, "foco": "teoria_e_exemplos"})
            teoria_txt = sec_livro.get("teoria_e_exemplos", "")[:12000]
            blocos_contexto.append(f"### Teoria e Exemplos da Seção {secao} ({sec_livro.get('livro', 'Stewart')})\n{teoria_txt}")
    elif skill_id == "resumidor-aula" and secao:
        sec_stewart = _rodar_busca("ler_secao_livro", {"livro": "stewart", "secao": secao, "foco": "teoria_e_exemplos"})
        blocos_contexto.append(f"### Seção Completa no Livro Principal ({sec_stewart.get('livro', 'Stewart')} §{secao})\n{sec_stewart.get('teoria_e_exemplos', '')}")
        busca_extra = _rodar_busca("buscar_rag", {"consulta": secao, "secao": secao, "top_k": 4})
        blocos_contexto.append(f"### Materiais e Listas Correlatas na Pasta\n```json\n{json.dumps(busca_extra, ensure_ascii=False, indent=2)}\n```")
    elif skill_id == "estrategista-revisao":
        erros = _rodar_busca("ler_status_erros", {"unidade": 0})
        blocos_contexto.append(f"### Histórico de Acertos, Erros (✗) e Dúvidas (?) do Estudante\n```json\n{json.dumps(erros, ensure_ascii=False, indent=2)}\n```")
    else:
        q = instrucao_usuario or secao or "calculo"
        busca = _rodar_busca("buscar_rag", {"consulta": q, "secao": secao, "top_k": 5})
        blocos_contexto.append(f"### Resultados da Busca no RAG Local\n```json\n{json.dumps(busca, ensure_ascii=False, indent=2)}\n```")

    if texto_anexo:
        blocos_contexto.append(f"### Texto Extraído dos Slides / PDF Anexado\n{texto_anexo}")

    tarefa_fmt = instrucao_usuario
    if not tarefa_fmt:
        if skill_id == "tutor-progressivo":
            tarefa_fmt = f"Forneça ajuda no nível **{nivel}** para o exercício **{secao} #{numero}**."
        elif skill_id == "resumidor-aula":
            tarefa_fmt = f"Elabore o resumo teórico completo da seção **{secao}** ({unidade}ª unidade) no formato do caderno."
        elif skill_id == "estrategista-revisao":
            tarefa_fmt = "Analise meus erros e dúvidas atuais e monte um diagnóstico com roteiro de revisão priorizado."

    prompt_final = "\n\n".join([
        f"# Tarefa Solicitada\n{tarefa_fmt}",
        f"# Diretrizes da Skill ({skill_ativa.get('title', skill_id)})\n{skill_ativa.get('corpo', '')}",
        f"# Regras da Disciplina\n{skill_disc.get('corpo', '')}",
        "# Dados Recuperados pelo RAG Estruturado Local\n" + "\n\n".join(blocos_contexto),
    ])

    tokens_estimados = max(1, len(prompt_final) // 4)
    return {
        "ok": True,
        "modo": "pacote_rag",
        "skill": skill_id,
        "promptEmpacotado": prompt_final,
        "respostaMarkdown": (
            f"### 📦 Pacote RAG + Skill Gerado Localmente (0 Tokens de API)\n\n"
            f"O motor local executou **{len(tools_log)} busca(s)** no seu banco `rag.db` e montou um prompt cirúrgico "
            f"(~**{tokens_estimados} tokens**) contendo apenas os trechos exatos do livro, gabaritos de referência e as regras da Skill **`{skill_id}`**.\n\n"
            f"- Clique em **📋 Copiar Prompt RAG** abaixo para colar no Claude/Gemini Chat;\n"
            f"- Ou cole o Markdown gerado na aba **💾 Salvar Markdown** para gravar direto em `resumos/` ou `resolucoes/`."
        ),
        "arquivosSalvos": [],
        "propostasCronograma": [],
        "telemetria": {
            "modelo": "RAG Local (Offline)",
            "inputTokens": tokens_estimados,
            "outputTokens": 0,
            "totalTokens": tokens_estimados,
            "toolsExecutadas": tools_log,
        },
    }


# ---------------- Modo 2: Execução do Agente via Gemini API com Function Calling ----------------
def _chamar_gemini_rest(api_key: str, modelo: str, system_instruction: str, contents: list, tools: list) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "tools": [{"functionDeclarations": tools}],
        "generationConfig": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def executar_agente(
    pasta_app: pathlib.Path,
    raiz_disciplina: pathlib.Path,
    skill_id: str,
    parametros: dict,
) -> dict:
    modo = parametros.get("modo") or "api"
    cfg = ler_config(pasta_app)
    api_key = cfg.get("_apiKeyReal", "")
    modelo = parametros.get("modelo") or cfg.get("modeloPadrao") or "gemini-3.8-flash"

    # Substitui automaticamente modelos legados por gemini-3.8-flash
    if any(modelo.startswith(p) for p in ("gemini-2.", "gemini-1.")):
        modelo = "gemini-3.8-flash"

    if modo == "pacote_rag" or not api_key:
        res_pacote = montar_pacote_rag_enxuto(pasta_app, raiz_disciplina, skill_id, parametros)
        if modo == "api" and not api_key:
            res_pacote["avisoSemChave"] = (
                "Nenhuma API Key da Gemini foi configurada ainda — gerei o Pacote RAG + Skill localmente! "
                "Se quiser que o Agente execute direto via API, adicione sua chave gratuita do Google AI Studio em ⚙ Configurar API."
            )
        return res_pacote

    skills = listar_skills(pasta_app, raiz_disciplina)
    skill_ativa = next((s for s in skills if s["id"] == skill_id), skills[0] if skills else {})
    skill_disc = next((s for s in skills if s["id"] == "SKILL-DISCIPLINA"), {})

    secao = str(parametros.get("secao", "")).strip()
    numero = str(parametros.get("numero", "")).strip()
    nivel = str(parametros.get("nivel", "N4")).strip()
    unidade = int(parametros.get("unidade", 3) or 3)
    mensagem = str(parametros.get("mensagem", "")).strip()
    texto_anexo = str(parametros.get("textoAnexo", "")).strip()
    imagens_base64 = parametros.get("imagensBase64") or []

    system_prompt = (
        "Você é o Agente de Estudos autônomo da plataforma universitária do Enzo.\n"
        "Use SEMPRE as tools de busca no RAG ('ler_secao_livro', 'buscar_rag', 'consultar_contexto_exercicio') "
        "para embasar suas respostas nos livros e resumos reais da pasta. "
        "Você pode e deve fazer MÚLTIPLAS buscas se precisar cruzar seções, exemplos ou listas.\n"
        "Em exercícios pares do Stewart (sem gabarito oficial), SEMPRE use 'conferir_calculo_python' com numpy/scipy "
        "para validar numericamente suas integrais/derivadas antes de escrever a resolução.\n\n"
        f"=== SKILL ATIVA: {skill_ativa.get('title', skill_id)} ===\n{skill_ativa.get('corpo', '')}\n\n"
        f"=== REGRAS DA DISCIPLINA ===\n{skill_disc.get('corpo', '')}\n"
    )

    prompt_usuario = []
    if skill_id == "tutor-progressivo" and secao and numero:
        prompt_usuario.append(
            f"Preciso de ajuda no nível **{nivel}** para o exercício **{secao} #{numero}** (Unidade {unidade}). "
            f"{'Salve também a resolução completa em resolucoes/ usando salvar_resolucao.' if nivel == 'N4' else ''}"
        )
    elif skill_id == "resumidor-aula" and secao:
        prompt_usuario.append(
            f"Crie o resumo teórico completo da seção **{secao}** ({unidade}ª unidade), "
            f"grave em `resumos/` usando `salvar_resumo` e adicione os cartões de fórmula da seção usando `adicionar_formula`."
        )
    elif skill_id == "estrategista-revisao":
        prompt_usuario.append(
            f"Analise meu histórico de erros e dúvidas em `status.json` (foco na {unidade}ª unidade e pendências gerais) "
            f"e monte um diagnóstico com plano de ação."
        )
    if mensagem:
        prompt_usuario.append(f"Instrução adicional do estudante: {mensagem}")
    if texto_anexo:
        prompt_usuario.append(f"Texto extraído de PDF/slides anexados:\n{texto_anexo}")

    user_parts = [{"text": "\n\n".join(prompt_usuario) or "Olá! Analise o estado atual da disciplina."}]
    for img in imagens_base64[:6]:
        if isinstance(img, dict) and img.get("data"):
            user_parts.append({
                "inlineData": {
                    "mimeType": img.get("mimeType", "image/png"),
                    "data": img["data"],
                }
            })

    contents = [{"role": "user", "parts": user_parts}]
    tools_log = []
    arquivos_salvos = []
    propostas_cronograma = []
    in_tokens = 0
    out_tokens = 0
    resposta_final_md = ""

    try:
        # Loop de até 10 passos de Multi-Busca / Function Calling
        for passo in range(10):
            resp = _chamar_gemini_rest(api_key, modelo, system_prompt, contents, GEMINI_TOOLS_DECLARATIONS)
            usage = resp.get("usageMetadata", {})
            in_tokens += int(usage.get("promptTokenCount", 0))
            out_tokens += int(usage.get("candidatesTokenCount", 0))

            cands = resp.get("candidates", [])
            if not cands:
                break
            content_model = cands[0].get("content", {})
            parts = content_model.get("parts", [])
            contents.append({"role": "model", "parts": parts})

            fcalls = [p["functionCall"] for p in parts if "functionCall" in p]
            textos_turno = [p["text"] for p in parts if "text" in p and p["text"].strip()]
            if textos_turno:
                resposta_final_md = "\n\n".join(textos_turno)

            if not fcalls:
                break

            tool_response_parts = []
            for fc in fcalls:
                t_name = fc.get("name", "")
                t_args = fc.get("args", {})
                t0 = time.time()
                resultado_tool = executar_tool_local(
                    raiz_disciplina, t_name, t_args, arquivos_salvos, propostas_cronograma
                )
                dt = round((time.time() - t0) * 1000)
                tools_log.append({
                    "tool": t_name,
                    "args": t_args,
                    "tempoMs": dt,
                    "charsRetorno": len(json.dumps(resultado_tool, ensure_ascii=False)),
                })
                tool_response_parts.append({
                    "functionResponse": {
                        "name": t_name,
                        "response": {"result": resultado_tool},
                    }
                })

            contents.append({"role": "user", "parts": tool_response_parts})

        return {
            "ok": True,
            "modo": "api",
            "skill": skill_id,
            "respostaMarkdown": resposta_final_md or "Ação concluída com sucesso pelas tools do Agente.",
            "arquivosSalvos": arquivos_salvos,
            "propostasCronograma": propostas_cronograma,
            "telemetria": {
                "modelo": modelo,
                "inputTokens": in_tokens,
                "outputTokens": out_tokens,
                "totalTokens": in_tokens + out_tokens,
                "toolsExecutadas": tools_log,
            },
        }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "erro": f"Erro HTTP {e.code} na Gemini API: {err_body[:400]}"}
    except Exception as e:
        return {"ok": False, "erro": f"Falha na execução do Agente: {e}"}
