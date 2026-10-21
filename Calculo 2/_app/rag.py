#!/usr/bin/env python3
"""
Motor de RAG Estruturado em 2 Níveis (SQLite FTS5) + Extrator de PDFs + Verificador Matemático.
Roda 100% na CPU local usando sqlite3 (biblioteca padrão), pdfplumber e numpy/scipy.
"""

import json
import pathlib
import re
import sqlite3
import subprocess
import sys
import time

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


# ---------------- Limpeza de texto extraído de PDFs LaTeX ----------------
_LATEX_COMBINING = [
    (r"´a|a´", "á"), (r"´e|e´", "é"), (r"´ı|´i|i´|ı´", "í"), (r"´o|o´", "ó"), (r"´u|u´", "ú"),
    (r"´A|A´", "Á"), (r"´E|E´", "É"), (r"´I|I´", "Í"), (r"´O|O´", "Ó"), (r"´U|U´", "Ú"),
    (r"˜a|a˜", "ã"), (r"˜o|o˜", "õ"), (r"˜A|A˜", "Ã"), (r"˜O|O˜", "Õ"),
    (r"ˆa|aˆ", "â"), (r"ˆe|eˆ", "ê"), (r"ˆo|oˆ", "ô"),
    (r"`a|a`", "à"), (r"¸c|c¸", "ç"), (r"¸C|C¸", "Ç"),
    (r"\u0131", "i"), (r"\ufb01", "fi"), (r"\ufb02", "fl"),
]


def limpar_texto_pdf(texto: str) -> str:
    if not texto:
        return ""
    t = texto
    for padrao, sub in _LATEX_COMBINING:
        t = re.sub(padrao, sub, t)
    # Limpa códigos (cid:XX) comuns de integrais/símbolos em LaTeX
    t = re.sub(r"\(cid:90\)\s*\(cid:90\)\s*\(cid:90\)", "∭ ", t)
    t = re.sub(r"\(cid:82\)\s*\(cid:82\)\s*\(cid:82\)", "∭ ", t)
    t = re.sub(r"\(cid:90\)\s*\(cid:90\)", "∬ ", t)
    t = re.sub(r"\(cid:82\)\s*\(cid:82\)", "∬ ", t)
    t = re.sub(r"\(cid:90\)|\(cid:82\)", "∫ ", t)
    t = re.sub(r"\(cid:112\)", "√", t)
    t = re.sub(r"\(cid:\d+\)", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# ---------------- Conexão e Schema do Banco SQLite FTS5 ----------------
def caminho_db(raiz_disciplina: pathlib.Path) -> pathlib.Path:
    pasta_dados = raiz_disciplina / "_app" / "dados"
    pasta_dados.mkdir(parents=True, exist_ok=True)
    return pasta_dados / "rag.db"


def conectar_db(raiz_disciplina: pathlib.Path) -> sqlite3.Connection:
    db_path = caminho_db(raiz_disciplina)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS meta_arquivos (
            caminho TEXT PRIMARY KEY,
            mtime REAL,
            tipo TEXT
        );

        -- Nível 1: Seções teóricas completas + exemplos + exercícios + gabarito sem cortes
        CREATE TABLE IF NOT EXISTS secoes_completas (
            livro_id TEXT,
            secao TEXT,
            titulo TEXT,
            pg_livro INT,
            pg_pdf_ini INT,
            pg_pdf_fim INT,
            teoria_e_exemplos TEXT,
            bateria_exercicios TEXT,
            gabarito_secao TEXT,
            atualizado_em REAL,
            PRIMARY KEY (livro_id, secao)
        );

        -- Cache de páginas brutas de apêndices de gabarito
        CREATE TABLE IF NOT EXISTS paginas_gabarito (
            livro_id TEXT,
            pagina_pdf INT,
            texto TEXT,
            PRIMARY KEY (livro_id, pagina_pdf)
        );

        -- Nível 2: Unidades lógicas naturais para multi-busca cruzada (BM25)
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            fonte,
            tipo,
            secao,
            titulo,
            conteudo,
            pagina_pdf UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
    """)
    return con


def carregar_curso_json(raiz_disciplina: pathlib.Path) -> dict:
    p = raiz_disciplina / "_app" / "dados" / "curso.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


# ---------------- Indexação de Markdowns e PDFs da Disciplina ----------------
def _extrair_secao_de_nome_ou_texto(nome: str, texto: str) -> str:
    # 1. Prioriza o nome do arquivo em resoluções (ex: "15-4-22" -> "15.4", "L5-6(a)" -> "L5")
    m_res_num = re.match(r"^(\d{1,2})-(\d{1,2})-.+$", nome)
    if m_res_num:
        return f"{m_res_num.group(1)}.{m_res_num.group(2)}"
    m_res_lista = re.match(r"^(L\d+)-", nome, re.IGNORECASE)
    if m_res_lista:
        return m_res_lista.group(1).upper()

    # 2. Primeira linha (título H1 do resumo/documento, ex: "# 15.4 Integrais Duplas...")
    primeira_linha = (texto or "").lstrip().split("\n", 1)[0]
    m_h1 = re.search(r"\b(\d{1,2}\.\d{1,2}|L\d+)\b", primeira_linha)
    if m_h1:
        return m_h1.group(1)

    # 3. Nome de arquivo de lista em PDF (ex: "Lista 5 ...")
    m3 = re.search(r"Lista\s*(\d+)", nome, re.IGNORECASE)
    if m3:
        return f"L{m3.group(1)}"

    # 4. Cabeçalho (primeiros 400 chars)
    m = re.search(r"\b(\d{1,2}\.\d{1,2})\b", (texto or "")[:400])
    if m:
        return m.group(1)
    return ""


def _dividir_markdown_por_unidades_logicas(texto: str, titulo_padrao: str):
    """Divide um resumo .md pelas subseções naturais (## ...) sem cortar frases ou parágrafos."""
    linhas = texto.replace("\r", "").split("\n")
    blocos = []
    atual_titulo = titulo_padrao
    atual_linhas = []

    for ln in linhas:
        if ln.startswith("## "):
            if atual_linhas:
                blocos.append((atual_titulo, "\n".join(atual_linhas).strip()))
            atual_titulo = f"{titulo_padrao} — {ln[3:].strip()}"
            atual_linhas = [ln]
        else:
            atual_linhas.append(ln)
    if atual_linhas:
        blocos.append((atual_titulo, "\n".join(atual_linhas).strip()))
    return [(t, c) for t, c in blocos if c]


def sincronizar_indice(raiz_disciplina: pathlib.Path, forcar: bool = False) -> dict:
    """Indexa incrementalmente todos os .md e PDFs de disciplina/ no SQLite FTS5."""
    t0 = time.time()
    con = conectar_db(raiz_disciplina)
    if forcar:
        con.execute("DELETE FROM meta_arquivos;")
        con.execute("DELETE FROM chunks_fts;")
        con.execute("DELETE FROM secoes_completas;")
        con.commit()

    existentes = {
        r["caminho"]: r["mtime"]
        for r in con.execute("SELECT caminho, mtime FROM meta_arquivos").fetchall()
    }

    indexados = 0
    # 1. Arquivos Markdown (resumos, resoluções, referencia, exercicios, planos, SKILL-DISCIPLINA)
    padroes_md = [
        ("resumos/*.md", "resumo"),
        ("resolucoes/*.md", "resolucao"),
        ("referencia/*.md", "referencia"),
        ("exercicios/*.md", "lista_md"),
        ("plano-estudos-*.md", "plano"),
        ("00-INDICE.md", "indice"),
        ("SKILL-DISCIPLINA.md", "regras_disciplina"),
    ]
    for glob_pat, tipo in padroes_md:
        for p in sorted(raiz_disciplina.glob(glob_pat)):
            if not p.is_file() or p.name == "STATUS.md":
                continue
            rel = p.relative_to(raiz_disciplina).as_posix()
            mtime = p.stat().st_mtime
            if not forcar and existentes.get(rel) == mtime:
                continue

            texto = p.read_text(encoding="utf-8", errors="replace").strip()
            if not texto:
                continue
            con.execute("DELETE FROM chunks_fts WHERE fonte = ?", (rel,))
            secao = _extrair_secao_de_nome_ou_texto(p.stem, texto)
            prim_linha = texto.split("\n", 1)[0].lstrip("# ").strip() or p.stem

            if tipo == "resolucao":
                # Cada resolução fica 100% inteira como uma unidade
                con.execute(
                    "INSERT INTO chunks_fts (fonte, tipo, secao, titulo, conteudo, pagina_pdf) VALUES (?, ?, ?, ?, ?, ?)",
                    (rel, tipo, secao, f"Resolução {p.stem}", texto, ""),
                )
            else:
                # Resumos e documentos divididos por subseção natural (##), mantendo também visão completa se curto
                unidades = _dividir_markdown_por_unidades_logicas(texto, prim_linha)
                for tit_u, cont_u in unidades:
                    sec_u = _extrair_secao_de_nome_ou_texto(p.stem, cont_u) or secao
                    con.execute(
                        "INSERT INTO chunks_fts (fonte, tipo, secao, titulo, conteudo, pagina_pdf) VALUES (?, ?, ?, ?, ?, ?)",
                        (rel, tipo, sec_u, tit_u, cont_u, ""),
                    )

            con.execute(
                "INSERT OR REPLACE INTO meta_arquivos (caminho, mtime, tipo) VALUES (?, ?, ?)",
                (rel, mtime, tipo),
            )
            indexados += 1

    # 2. PDFs da pasta disciplina/ (Programa, Calendario, exercicios_*un.pdf, Lista1..6_2026-1.pdf)
    pasta_disc = raiz_disciplina / "disciplina"
    if pdfplumber and pasta_disc.exists():
        for p in sorted(pasta_disc.rglob("*.pdf")):
            rel = p.relative_to(raiz_disciplina).as_posix()
            mtime = p.stat().st_mtime
            if not forcar and existentes.get(rel) == mtime:
                continue
            try:
                con.execute("DELETE FROM chunks_fts WHERE fonte = ?", (rel,))
                secao = _extrair_secao_de_nome_ou_texto(p.stem, "")
                with pdfplumber.open(p) as pdf:
                    for idx, page in enumerate(pdf.pages):
                        raw = page.extract_text() or ""
                        limpo = limpar_texto_pdf(raw)
                        if not limpo:
                            continue
                        con.execute(
                            "INSERT INTO chunks_fts (fonte, tipo, secao, titulo, conteudo, pagina_pdf) VALUES (?, ?, ?, ?, ?, ?)",
                            (rel, "lista_pdf", secao, f"{p.name} (p. {idx + 1})", limpo, str(idx + 1)),
                        )
                con.execute(
                    "INSERT OR REPLACE INTO meta_arquivos (caminho, mtime, tipo) VALUES (?, ?, ?)",
                    (rel, mtime, "lista_pdf"),
                )
                indexados += 1
            except Exception as e:
                sys.stderr.write(f"Aviso ao indexar {rel}: {e}\n")

    con.commit()
    total_chunks = con.execute("SELECT count(*) FROM chunks_fts").fetchone()[0]
    total_secoes = con.execute("SELECT count(*) FROM secoes_completas").fetchone()[0]
    con.close()
    return {
        "arquivosAtualizados": indexados,
        "totalUnidadesFts": total_chunks,
        "secoesLivroEmCache": total_secoes,
        "tempoMs": round((time.time() - t0) * 1000),
    }


# ---------------- Nível 1: Seções Teóricas Completas + Exemplos dos Livros ----------------
def _dividir_teoria_e_exercicios_secao(texto_completo: str, secao: str):
    """Separa o texto integral da seção entre (Teoria + Exemplos Resolvidos) e (Bateria de Exercícios)."""
    # Procura cabeçalho da bateria de exercícios da seção (ex: "15.4 Exercícios" ou "Exercícios 15.4")
    sec_esc = re.escape(secao)
    padroes = [
        rf"\n\s*{sec_esc}\s+Exerc[íi]cios\b",
        rf"\n\s*Exerc[íi]cios\s+{sec_esc}\b",
        r"\n\s*Exerc[íi]cios\s*\n",
    ]
    for pat in padroes:
        m = re.search(pat, texto_completo, flags=re.IGNORECASE)
        if m and m.start() > len(texto_completo) * 0.25:
            return texto_completo[:m.start()].strip(), texto_completo[m.start():].strip()
    return texto_completo, ""


def _extrair_gabarito_secao_livro(con: sqlite3.Connection, raiz_disciplina: pathlib.Path, info_livro: dict, secao: str) -> str:
    """Localiza e extrai no Apêndice do livro (Stewart ou Guidorizzi) o bloco de respostas da seção."""
    if not pdfplumber:
        return ""
    livro_id = info_livro.get("id", "stewart")
    faixa = info_livro.get("gabaritoPdf")
    arq = info_livro.get("arquivo", "")
    caminho_pdf = raiz_disciplina / arq
    if not faixa or not caminho_pdf.exists():
        return ""

    pg_ini, pg_fim = int(faixa[0]), int(faixa[1])
    # Verifica se já temos páginas do apêndice em cache no SQLite
    cands = con.execute(
        "SELECT pagina_pdf, texto FROM paginas_gabarito WHERE livro_id = ? ORDER BY pagina_pdf",
        (livro_id,),
    ).fetchall()

    if not cands:
        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                max_p = min(len(pdf.pages), pg_fim)
                for pno in range(max(1, pg_ini), max_p + 1):
                    txt = limpar_texto_pdf(pdf.pages[pno - 1].extract_text() or "")
                    con.execute(
                        "INSERT OR REPLACE INTO paginas_gabarito (livro_id, pagina_pdf, texto) VALUES (?, ?, ?)",
                        (livro_id, pno, txt),
                    )
            con.commit()
            cands = con.execute(
                "SELECT pagina_pdf, texto FROM paginas_gabarito WHERE livro_id = ? ORDER BY pagina_pdf",
                (livro_id,),
            ).fetchall()
        except Exception as e:
            return f"Erro ao ler apêndice de gabarito: {e}"

    sec_esc = re.escape(secao)
    achados = []
    for row in cands:
        txt = row["texto"] or ""
        if re.search(rf"EXERC[ÍI]CIOS\s+{sec_esc}\b|\b{sec_esc}\b", txt, re.IGNORECASE):
            achados.append(f"[Apêndice PDF p. {row['pagina_pdf']}]\n{txt}")
    if not achados and "." in secao:
        cap, sub = secao.split(".", 1)
        if sub.isdigit():
            adj = [f"{cap}.{max(1, int(sub)-1)}", f"{cap}.{int(sub)+1}"]
            for row in cands:
                txt = row["texto"] or ""
                if any(re.search(rf"EXERC[ÍI]CIOS\s+{re.escape(a)}\b", txt, re.IGNORECASE) for a in adj):
                    achados.append(f"[Apêndice PDF p. {row['pagina_pdf']}]\n{txt}")
    return "\n\n".join(achados[:3])


def ler_secao_livro(raiz_disciplina: pathlib.Path, livro: str = "stewart", secao: str = "15.4", foco: str = "teoria_e_exemplos") -> dict:
    """
    Tool Nível 1: Retorna a seção teórica COMPLETA (todas as páginas de teoria e exemplos resolvidos,
    sem corte de palavras) ou a bateria de exercícios da seção no livro indicado.
    """
    curso = carregar_curso_json(raiz_disciplina)
    livros = curso.get("livros", [])
    livro_norm = livro.lower().strip()
    info_livro = None
    for lv in livros:
        if livro_norm in lv.get("id", "").lower() or livro_norm in lv.get("nome", "").lower():
            info_livro = lv
            break
    if not info_livro and livros:
        info_livro = livros[0]
    if not info_livro:
        return {"erro": "Nenhum livro configurado em curso.json"}

    livro_id = info_livro["id"]
    secoes_map = info_livro.get("secoes", {})
    sec_info = secoes_map.get(secao)
    # Se pediu no Guidorizzi usando código do Stewart (ex: "14.1" ou "14.8" -> procura em corresp)
    if not sec_info:
        for k, v in secoes_map.items():
            cor = str(v.get("corresp", ""))
            if secao == cor or secao in [x.strip() for x in cor.split(",")]:
                secao = k
                sec_info = v
                break
    if not sec_info:
        if livro_id == "guidorizzi" and str(secao).startswith("15."):
            return {
                "nota": (
                    f"O livro '{info_livro['nome']}' disponível na pasta cobre apenas Derivadas Parciais e Otimização "
                    "(Capítulos 8 a 16 = Stewart 14.1 a 14.8). No Guidorizzi, Integrais Duplas e Triplas (equivalentes ao "
                    "Capítulo 15 do Stewart) ficam no Volume 3. Para a seção "
                    f"{secao}, utilize ler_secao_livro(livro='stewart', secao='{secao}') e buscar_rag nas Listas 4, 5 e 6 da UFPE."
                ),
                "secoesDisponiveisGuidorizzi": list(secoes_map.keys()),
            }
        return {
            "erro": f"Seção '{secao}' não mapeada em {info_livro['nome']}. Seções disponíveis: {list(secoes_map.keys())}"
        }

    con = conectar_db(raiz_disciplina)
    row = con.execute(
        "SELECT * FROM secoes_completas WHERE livro_id = ? AND secao = ?",
        (livro_id, secao),
    ).fetchone()

    if row and not row["gabarito_secao"]:
        gab_novo = _extrair_gabarito_secao_livro(con, raiz_disciplina, info_livro, secao)
        if gab_novo:
            con.execute(
                "UPDATE secoes_completas SET gabarito_secao = ? WHERE livro_id = ? AND secao = ?",
                (gab_novo, livro_id, secao),
            )
            con.commit()
            row = con.execute(
                "SELECT * FROM secoes_completas WHERE livro_id = ? AND secao = ?",
                (livro_id, secao),
            ).fetchone()

    if not row:
        if not pdfplumber:
            con.close()
            return {"erro": "pdfplumber não disponível para extrair páginas do livro."}
        caminho_pdf = raiz_disciplina / info_livro["arquivo"]
        if not caminho_pdf.exists():
            con.close()
            return {"erro": f"Arquivo do livro não encontrado: {info_livro['arquivo']}"}

        pg_ini = int(sec_info["pgPdf"])
        pg_fim = int(sec_info.get("pgFimPdf", pg_ini + 8))
        paginas_txt = []
        with pdfplumber.open(caminho_pdf) as pdf:
            fim_real = min(len(pdf.pages), pg_fim)
            for pno in range(max(1, pg_ini), fim_real + 1):
                t = limpar_texto_pdf(pdf.pages[pno - 1].extract_text() or "")
                paginas_txt.append(f"--- [PDF p. {pno} · Livro p. {pno - info_livro.get('offsetPdf', 0)}] ---\n{t}")

        texto_bruto = "\n\n".join(paginas_txt)
        teoria_ex, bat_ex = _dividir_teoria_e_exercicios_secao(texto_bruto, secao)
        gab_sec = _extrair_gabarito_secao_livro(con, raiz_disciplina, info_livro, secao)

        con.execute(
            """INSERT OR REPLACE INTO secoes_completas
               (livro_id, secao, titulo, pg_livro, pg_pdf_ini, pg_pdf_fim,
                teoria_e_exemplos, bateria_exercicios, gabarito_secao, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                livro_id,
                secao,
                sec_info.get("titulo", secao),
                sec_info.get("pgLivro", 0),
                pg_ini,
                pg_fim,
                teoria_ex,
                bat_ex,
                gab_sec,
                time.time(),
            ),
        )
        # Também indexa os exemplos resolvidos da seção na tabela FTS5 para multi-buscas cruzadas
        fonte_sec = f"{info_livro['nome']} §{secao}"
        con.execute("DELETE FROM chunks_fts WHERE fonte = ?", (fonte_sec,))
        partes_ex = re.split(r"(?=\bEXEMPLO\s+\d+|\bTeorema\b|\bDefini[çc][ãa]o\b)", teoria_ex)
        for idx_p, parte in enumerate(partes_ex):
            parte = parte.strip()
            if len(parte) < 60:
                continue
            prim = parte.split("\n", 1)[0][:90]
            con.execute(
                "INSERT INTO chunks_fts (fonte, tipo, secao, titulo, conteudo, pagina_pdf) VALUES (?, ?, ?, ?, ?, ?)",
                (fonte_sec, "livro_teoria", secao, f"§{secao} — {prim}", parte, f"{pg_ini}-{pg_fim}"),
            )
        con.commit()
        row = con.execute(
            "SELECT * FROM secoes_completas WHERE livro_id = ? AND secao = ?",
            (livro_id, secao),
        ).fetchone()

    resultado = {
        "livro": info_livro["nome"],
        "secao": secao,
        "titulo": row["titulo"],
        "paginasPdf": f"{row['pg_pdf_ini']} a {row['pg_pdf_fim']}",
        "paginaLivroInicial": row["pg_livro"],
    }
    if foco == "exercicios":
        resultado["bateria_exercicios"] = row["bateria_exercicios"] or row["teoria_e_exemplos"]
    elif foco == "gabarito":
        resultado["gabarito_secao"] = row["gabarito_secao"]
    elif foco == "tudo":
        resultado["teoria_e_exemplos"] = row["teoria_e_exemplos"]
        resultado["bateria_exercicios"] = row["bateria_exercicios"]
        resultado["gabarito_secao"] = row["gabarito_secao"]
    else:
        resultado["teoria_e_exemplos"] = row["teoria_e_exemplos"]

    con.close()
    return resultado


# ---------------- Nível 2: Multi-Busca FTS5 (BM25) ----------------
def buscar_rag(raiz_disciplina: pathlib.Path, consulta: str, secao: str = "", tipo: str = "", top_k: int = 5) -> dict:
    """
    Tool Nível 2: Busca unidades semânticas completas (resumos, resoluções, listas PDF,
    exemplos de livros) via SQLite FTS5 BM25 + filtros opcionais de seção e tipo.
    """
    sincronizar_indice(raiz_disciplina, forcar=False)
    con = conectar_db(raiz_disciplina)

    # Prepara query FTS5 segura com OR entre termos relevantes
    termos = [t for t in re.findall(r"[\w\d\.]+", consulta, flags=re.UNICODE) if len(t) >= 2]
    fts_query = " OR ".join(f'"{t}"' for t in termos[:10]) if termos else ""

    sql = """
        SELECT fonte, tipo, secao, titulo, conteudo, pagina_pdf, bm25(chunks_fts) AS score
        FROM chunks_fts
        WHERE 1=1
    """
    params = []
    if fts_query:
        sql += " AND chunks_fts MATCH ?"
        params.append(fts_query)
    if secao:
        sql += " AND (secao = ? OR conteudo LIKE ?)"
        params.extend([secao, f"%{secao}%"])
    if tipo:
        sql += " AND tipo LIKE ?"
        params.append(f"%{tipo}%")

    if fts_query:
        sql += " ORDER BY score LIMIT ?"
    else:
        sql += " LIMIT ?"
    params.append(max(1, min(int(top_k), 12)))

    try:
        rows = con.execute(sql, params).fetchall()
    except Exception:
        rows = []

    resultados = []
    for r in rows:
        resultados.append({
            "fonte": r["fonte"],
            "tipo": r["tipo"],
            "secao": r["secao"],
            "titulo": r["titulo"],
            "paginaPdf": r["pagina_pdf"],
            "conteudo": r["conteudo"],
        })
    con.close()
    return {
        "consulta": consulta,
        "filtros": {"secao": secao, "tipo": tipo},
        "totalEncontrados": len(resultados),
        "resultados": resultados,
    }


# ---------------- Tool Especial para Exercícios (Pares sem Gabarito + Irmãos Ímpares) ----------------
def consultar_contexto_exercicio(raiz_disciplina: pathlib.Path, secao: str, numero: str) -> dict:
    """
    Investiga tudo sobre um exercício específico (ex: secao="15.4", numero="22" ou secao="L5", numero="5").
    Se for questão PAR do Stewart (sem gabarito oficial), busca automaticamente:
      1. O enunciado cadastrado em exercicios.json;
      2. A bateria da seção no PDF do Stewart contendo os vizinhos ÍMPARES (#N-1 e #N+1);
      3. O gabarito oficial dos vizinhos ímpares no Apêndice do Stewart;
      4. O resumo da seção correspondente.
    """
    sincronizar_indice(raiz_disciplina, forcar=False)
    num_str = str(numero).strip()
    ex_id = f"{secao}-{num_str}"

    # 1. Busca em exercicios.json
    p_ex = raiz_disciplina / "_app" / "dados" / "exercicios.json"
    enunciado_cadastrado = None
    vizinhos_cadastrados = []
    if p_ex.exists():
        try:
            secoes_ex = json.loads(p_ex.read_text(encoding="utf-8"))
            for s in secoes_ex:
                if str(s.get("sec")) == str(secao):
                    todos = [("Linha 1", x) for x in s.get("l1", [])] + [("Linha 2", x) for x in s.get("l2", [])]
                    for lin, item in todos:
                        if str(item[0]) == num_str:
                            enunciado_cadastrado = {
                                "numero": item[0],
                                "linha": lin,
                                "pede": item[1],
                                "expressao": item[2],
                                "figura": item[3],
                                "secaoNome": s.get("nome"),
                            }
                        else:
                            vizinhos_cadastrados.append({"numero": item[0], "pede": item[1], "expressao": item[2]})
        except Exception:
            pass

    # 2. Resolução já existente em resolucoes/
    arq_sol = f"{secao.replace('.', '-')}-{num_str}.md"
    p_sol = raiz_disciplina / "resolucoes" / arq_sol
    resolucao_existente = p_sol.read_text(encoding="utf-8") if p_sol.exists() else None

    # 3. Se for seção do Stewart (ex: 14.x ou 15.x), busca vizinhos ímpares e gabarito no livro
    recorte_bateria = ""
    recorte_gabarito = ""
    eh_par = False
    num_int = None
    m_num = re.match(r"^(\d+)", num_str)
    if m_num:
        num_int = int(m_num.group(1))
        eh_par = (num_int % 2 == 0)

    if re.match(r"^\d+\.\d+$", str(secao)):
        dados_sec = ler_secao_livro(raiz_disciplina, "stewart", str(secao), foco="tudo")
        bat = dados_sec.get("bateria_exercicios", "")
        gab = dados_sec.get("gabarito_secao", "")

        if bat and num_int is not None:
            # Localiza a região do exercício num_int (e os vizinhos num_int-1, num_int+1)
            m_pos = re.search(rf"(?:^|\n)\s*{num_int}\s*[\.\)]", bat)
            if not m_pos and num_int > 1:
                m_pos = re.search(rf"(?:^|\n)\s*{num_int - 1}\s*[\.\)]", bat)
            if m_pos:
                ini = max(0, m_pos.start() - 350)
                fim = min(len(bat), m_pos.start() + 1200)
                recorte_bateria = bat[ini:fim]
            else:
                recorte_bateria = bat[:1500]

        if gab and num_int is not None:
            # Procura no apêndice da seção o número (se ímpar) ou os vizinhos ímpares (num_int-1 e num_int+1)
            alvos_impares = [num_int] if not eh_par else [max(1, num_int - 1), num_int + 1]
            trechos_gab = []
            for alvo in alvos_impares:
                m_g = re.search(rf"(?:^|\n|\s){alvo}\.\s+([^\n]+(?:\n[^\n]+)?)", gab)
                if m_g:
                    ini_g = max(0, m_g.start() - 100)
                    fim_g = min(len(gab), m_g.end() + 250)
                    trechos_gab.append(f"Gabarito oficial Stewart #{alvo}: {gab[ini_g:fim_g].strip()}")
            recorte_gabarito = "\n---\n".join(trechos_gab) if trechos_gab else gab[:1200]
    elif str(secao).startswith("L"):
        # Lista da UFPE (L1..L6)
        busca_lista = buscar_rag(raiz_disciplina, f"{num_str}", secao=str(secao), tipo="lista_pdf", top_k=3)
        recorte_bateria = "\n\n".join(r["conteudo"] for r in busca_lista.get("resultados", []))

    # 4. Resumo teórico correlato da pasta resumos/
    resumo_correlato = buscar_rag(raiz_disciplina, str(secao), secao=str(secao), tipo="resumo", top_k=2)

    return {
        "idExercicio": ex_id,
        "secao": secao,
        "numero": num_str,
        "ehExercicioParSemGabaritoDireto": eh_par and re.match(r"^\d+\.\d+$", str(secao)) is not None,
        "notaGabarito": (
            f"O exercício #{num_str} é PAR (o Stewart só publica gabarito dos ímpares). "
            f"Abaixo estão os enunciados e gabaritos dos vizinhos ímpares (#{num_int-1} e #{num_int+1}) "
            f"para referência de formato. Use a tool 'conferir_calculo_python' com numpy/scipy para validar o resultado exato!"
            if (eh_par and num_int)
            else "Confira o gabarito e valide os cálculos."
        ),
        "enunciadoCadastrado": enunciado_cadastrado,
        "resolucaoExistente": resolucao_existente,
        "recorteBateriaPdf": recorte_bateria,
        "gabaritoOficialOuVizinhosImpares": recorte_gabarito,
        "resumosRelacionados": resumo_correlato.get("resultados", []),
    }


# ---------------- Tool de Verificação Numérica/Algébrica em Python (numpy/scipy) ----------------
def conferir_calculo_python(codigo_python: str) -> dict:
    """
    Executa código Python matemático (com math, numpy, scipy, scipy.integrate pré-importados)
    em processo isolado com timeout de 6s para conferir integrais duplas/triplas, derivadas,
    determinantes Jacobianos e valores numéricos de questões pares sem gabarito.
    """
    preambulo = (
        "import math\n"
        "import numpy as np\n"
        "try:\n"
        "    import scipy\n"
        "    from scipy import integrate\n"
        "    from scipy.integrate import quad, dblquad, tplquad\n"
        "except ImportError:\n"
        "    pass\n"
    )
    script_completo = preambulo + "\n" + codigo_python
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script_completo],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=6,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "erro": "Tempo limite de 6 segundos excedido no cálculo Python."}
    except Exception as e:
        return {"ok": False, "erro": str(e)}


# ---------------- Tool de Diagnóstico de Status/Erros do Estudante ----------------
def ler_status_erros(raiz_disciplina: pathlib.Path, unidade: int = 0) -> dict:
    p_status = raiz_disciplina / "status.json"
    p_ex = raiz_disciplina / "_app" / "dados" / "exercicios.json"
    marcacoes = {}
    if p_status.exists():
        try:
            marcacoes = json.loads(p_status.read_text(encoding="utf-8")).get("marcacoes", {})
        except Exception:
            marcacoes = {}

    secoes = []
    if p_ex.exists():
        try:
            secoes = json.loads(p_ex.read_text(encoding="utf-8"))
        except Exception:
            secoes = []

    erros = []
    duvidas = []
    acertos = []
    resumo_por_secao = []

    for s in secoes:
        if unidade and int(s.get("un", 0)) != int(unidade):
            continue
        sec_code = s.get("sec", "")
        c_ok = c_err = c_dub = c_tot = 0
        for rot, chave in (("Linha 1", "l1"), ("Linha 2", "l2")):
            for item in s.get(chave, []):
                c_tot += 1
                eid = f"{sec_code}-{item[0]}"
                st = marcacoes.get(eid)
                info_item = {
                    "id": eid,
                    "secao": sec_code,
                    "unidade": s.get("un"),
                    "linha": rot,
                    "pede": item[1],
                    "expressao": item[2],
                }
                if st == "err":
                    c_err += 1
                    erros.append(info_item)
                elif st == "dub":
                    c_dub += 1
                    duvidas.append(info_item)
                elif st == "ok":
                    c_ok += 1
                    acertos.append(eid)
        if c_ok or c_err or c_dub:
            resumo_por_secao.append({
                "secao": sec_code,
                "nome": s.get("nome"),
                "unidade": s.get("un"),
                "acertos": c_ok,
                "erros": c_err,
                "duvidas": c_dub,
                "total": c_tot,
            })

    return {
        "totalAcertos": len(acertos),
        "totalErros": len(erros),
        "totalDuvidas": len(duvidas),
        "resumoPorSecao": resumo_por_secao,
        "exerciciosComErro": erros,
        "exerciciosComDuvida": duvidas,
    }


# ---------------- Extrator Determinístico de Páginas e Questões de PDFs (Zero Tokens) ----------------
def extrair_paginas_ou_questoes_pdf(
    raiz_disciplina: pathlib.Path,
    arquivo_rel: str,
    pg_inicio: int = 1,
    pg_fim: int = 5,
    pagina_eh_do_livro: bool = False,
    offset_livro: int = 0,
) -> dict:
    if not pdfplumber:
        return {"erro": "pdfplumber não instalado."}
    caminho = (raiz_disciplina / arquivo_rel).resolve()
    if not str(caminho).startswith(str(raiz_disciplina.resolve())) or not caminho.exists():
        return {"erro": f"PDF não encontrado: {arquivo_rel}"}

    if pagina_eh_do_livro and offset_livro:
        pg_inicio = pg_inicio + offset_livro
        pg_fim = pg_fim + offset_livro

    textos = []
    with pdfplumber.open(caminho) as pdf:
        total_p = len(pdf.pages)
        ini = max(1, min(int(pg_inicio), total_p))
        fim = max(ini, min(int(pg_fim), total_p))
        for pno in range(ini, fim + 1):
            t = limpar_texto_pdf(pdf.pages[pno - 1].extract_text() or "")
            textos.append(f"--- Página PDF {pno} ---\n{t}")

    texto_unido = "\n\n".join(textos)
    # Parser determinístico de questões numeradas ("1. ...", "2. ...")
    questoes = []
    blocos = re.split(r"(?:^|\n)\s*(\d{1,3})\s*[\.\)]\s+", texto_unido)
    if len(blocos) >= 3:
        for i in range(1, len(blocos) - 1, 2):
            num_q = blocos[i].strip()
            corpo_q = re.sub(r"\s+", " ", blocos[i + 1]).strip()
            if corpo_q:
                questoes.append([int(num_q) if num_q.isdigit() else num_q, corpo_q[:420], None, None])

    return {
        "arquivo": arquivo_rel,
        "paginaPdfInicio": ini,
        "paginaPdfFim": fim,
        "totalPaginasPdf": total_p,
        "textoExtraido": texto_unido,
        "questoesDetectadas": questoes,
    }
