"""Orquestra a migração: lê o legado, aplica as regras e grava tudo pelos repositórios numa única operação."""

import datetime
import re
import shutil
from contextlib import closing
from pathlib import Path, PurePosixPath

from estudos.db.conexao import conectar
from estudos.erros import DadoInvalido
from estudos.historico import Operacao, operacao
from estudos.migracao import regras
from estudos.migracao.arquivos import PASTA_FONTE_POR_TIPO, vincular_arquivo
from estudos.migracao.conversao import (
    data_curta_para_iso,
    html_para_md,
    nota_de_tags,
    periodo_e_instituicao,
    referencias_exercicios,
    tabela_markdown,
)
from estudos.migracao.legado import Legado, carregar
from estudos.migracao.relatorio import Relatorio
from estudos.modelos import ESTADOS_MARCACAO, QuestaoEntrada
from estudos.repos import _base, cronograma, documentos, eventos, fontes, formulas, listas, livros, marcacoes, materia, topicos, unidades
from estudos.repos.fontes import sha256_arquivo
from estudos.workspace import ARQUIVO_DB, inicializar_materia

ORIGEM = "migrado"
GERADOS = ("conteudo", "fontes", "figuras", ".versoes")
_RESOLUCAO = re.compile(r"^(\d+)-(\d+)-(.+)$")
_SEM_VALOR = {"", "—", "-"}
CAMPOS_UNIDADE_LEGADO = (
    ("eyebrow", "Sobrelinha"), ("subtitulo", "Subtítulo"), ("ondeEstamosSubtitulo", "Onde estamos"),
    ("cronogramaTitulo", "Título do cronograma"), ("cronogramaSubtitulo", "Subtítulo do cronograma"),
    ("resumosSubtitulo", "Subtítulo dos resumos"), ("formularioTitulo", "Título do formulário"),
    ("formularioSubtitulo", "Subtítulo do formulário"), ("tags", "Tags"),
)
CAMPOS_FASE_LEGADO = (("eyebrow", "Sobrelinha"), ("tag", "Etiqueta"), ("nota", "Nota"))


class MigracaoRecusada(RuntimeError):
    pass


# ---------------- preparação do destino ----------------
def _preparar_destino(destino: Path, forcar: bool) -> str | None:
    """Apaga o que a migração anterior gerou (só os itens de GERADOS e o banco) e devolve o uid a preservar."""
    banco = destino / ARQUIVO_DB
    if not banco.exists():
        # Primeira migração: as pastas que ela gera não podem existir, senão uma reexecução apagaria conteúdo alheio.
        existentes = [p for p in GERADOS if (destino / p).exists()]
        if existentes:
            raise MigracaoRecusada(
                f"{destino.name} já tem a(s) pasta(s) {', '.join(existentes)}, que a migração gera e apaga ao reexecutar. "
                "Renomeie-as antes de migrar."
            )
        return None
    with closing(conectar(banco)) as con:
        uid = con.execute("SELECT uid FROM materia").fetchone()[0]
        acoes = con.execute("SELECT count(*) FROM historico_grupo").fetchone()[0]
    if acoes and not forcar:
        raise MigracaoRecusada(
            f"O app novo já tem {acoes} ação(ões) registrada(s) em {destino.name}; migrar de novo apagaria essas mudanças. "
            "Use --forcar para reconstruir mesmo assim."
        )
    for sufixo in ("", "-wal", "-shm"):
        (destino / f"{ARQUIVO_DB}{sufixo}").unlink(missing_ok=True)
    for pasta in GERADOS:
        shutil.rmtree(destino / pasta, ignore_errors=True)
    return uid


class _Migracao:
    def __init__(self, legado: Legado, destino: Path, op: Operacao, relatorio: Relatorio, ano: int | None) -> None:
        self.legado = legado
        self.curso = legado.curso
        self.destino = destino
        self.op = op
        self.r = relatorio
        self.ano = ano
        self.unidade_id: dict[int, int] = {}
        self.fonte_por_pdf: dict[str, int] = {}
        self.secao_principal: dict[str, int] = {}
        self.secoes_por_livro: dict[str, dict[str, int]] = {}  # id do livro em curso.json → {código: secao_id}
        self.nome_livro: dict[str, str] = {}
        self.lista_id: dict[str, int] = {}
        self.questao_por_chave: dict[str, int] = {}
        self.unidade_da_questao: dict[int, int] = {}
        self.caminhos_documento: set[str] = set()
        self.notas_unidade: dict[int, list[str]] = {}

    # ---------------- utilidades ----------------
    def _md(self, texto: str | None, contexto: str) -> str:
        md, avisos = html_para_md(texto or "")
        self.r.avisos += [f"{contexto}: {a}" for a in avisos]
        return md

    def _unidade(self, numero: int) -> int:
        if numero not in self.unidade_id:
            self.unidade_id[numero] = unidades.criar(self.op, numero, "", origem=ORIGEM)
            self.r.decisoes.append(f"unidade {numero} criada porque exercicios.json a usa e curso.json não a declara")
        return self.unidade_id[numero]

    def _vincular(self, origem: Path, pasta_destino: str) -> str:
        """Leva o arquivo para `pasta_destino`, desviando de nomes ocupados por outro conteúdo. Devolve o caminho relativo."""
        nome = origem.name
        alvo = self.destino / pasta_destino / nome
        n = 2
        while alvo.exists() and sha256_arquivo(alvo) != sha256_arquivo(origem):
            alvo = self.destino / pasta_destino / f"{origem.stem}-{n}{origem.suffix}"
            n += 1
        modo = vincular_arquivo(origem, alvo)
        self.r.arquivos[modo] += 1
        return alvo.relative_to(self.destino).as_posix()

    def _registrar_fonte(self, rel_legado: str, tipo: str, titulo: str = "") -> int | None:
        origem = self.legado.pasta / rel_legado
        if not origem.is_file():
            self.r.nao_resolvidos.append(f"PDF citado não encontrado: {rel_legado}")
            return None
        caminho = self._vincular(origem, PASTA_FONTE_POR_TIPO[tipo])
        try:
            fonte_id = fontes.registrar(self.op, tipo, caminho, titulo or origem.stem, origem=ORIGEM)
        except DadoInvalido as e:
            self.r.avisos.append(f"{rel_legado}: {e}")
            sha = sha256_arquivo(origem)
            fonte_id = self.op.con.execute("SELECT id FROM fonte WHERE sha256 = ?", (sha,)).fetchone()[0]
        self.fonte_por_pdf[rel_legado] = fonte_id
        return fonte_id

    def _salvar_documento(self, tipo: str, nome: str, titulo: str, corpo: str, pai: str = "", **campos) -> int:
        caminho = f"{documentos.PASTA_POR_TIPO[tipo]}/{nome}"
        if caminho in self.caminhos_documento and pai:
            nome = f"{pai}-{nome}"
            caminho = f"{documentos.PASTA_POR_TIPO[tipo]}/{nome}"
        self.caminhos_documento.add(caminho)
        return documentos.salvar(self.op, tipo, nome, titulo, corpo, origem=ORIGEM, **campos)

    # ---------------- etapas ----------------
    def materia_e_unidades(self) -> None:
        periodo, instituicao = periodo_e_instituicao(self.curso.get("subtituloGeral", ""))
        if instituicao:
            materia.atualizar(self.op, instituicao=instituicao)
        for chave in sorted(self.curso["unidades"], key=int):
            u = self.curso["unidades"][chave]
            numero = int(chave)
            uid = unidades.criar(self.op, numero, u.get("tituloItalico", ""), origem=ORIGEM)
            self.unidade_id[numero] = uid
            if u.get("dataProva"):
                eventos.criar(self.op, "prova", u["dataProva"], unidade_id=uid, origem=ORIGEM)
            nota = nota_de_tags(u.get("tags") or [])
            if nota is not None:
                _base.inserir(self.op, "nota_avaliacao", {
                    "unidade_id": uid, "nota": nota, "registrada_em": datetime.date.today().isoformat(),
                })
                self.r.decisoes.append(f"unidade {numero}: tag de nota virou nota_avaliacao = {nota}")
            self.notas_unidade[numero] = _linhas_campos(u, CAMPOS_UNIDADE_LEGADO)

    def livros(self) -> None:
        for i, l in enumerate(self.curso.get("livros") or []):
            rel = l["arquivo"]
            fonte_id = self._registrar_fonte(rel, "livro", l.get("nome", ""))
            if fonte_id is None:
                continue
            gabarito = l.get("gabaritoPdf") or [None, None]
            livros.criar(
                self.op, fonte_id, "principal" if i == 0 else "complementar", titulo_obra=l.get("nome", ""),
                offset_pagina=int(l.get("offsetPdf", 0)), gabarito_pdf_ini=gabarito[0], gabarito_pdf_fim=gabarito[1],
            )
            ordenadas = sorted((l.get("secoes") or {}).items(), key=lambda kv: int(kv[1]["pgPdf"]))
            ids = {}
            for j, (codigo, s) in enumerate(ordenadas):
                ini = int(s["pgPdf"])
                if s.get("pgFimPdf"):
                    fim = int(s["pgFimPdf"])
                elif j + 1 < len(ordenadas):
                    fim = max(ini, int(ordenadas[j + 1][1]["pgPdf"]) - 1)
                    self.r.decisoes.append(f"{l.get('nome')} §{codigo}: fim = início da próxima seção − 1 ({fim})")
                else:
                    fim = ini
                    self.r.decisoes.append(f"{l.get('nome')} §{codigo}: sem página final; fim = início ({fim})")
                ids[codigo] = livros.criar_secao(self.op, fonte_id, codigo, s.get("titulo", codigo), ini, fim, origem=ORIGEM)
            self.secoes_por_livro[l["id"]] = ids
            self.nome_livro[l["id"]] = l.get("nome", l["id"])
            if i == 0:
                self.secao_principal = ids
                continue
            for codigo, s in ordenadas:
                for alvo in [c.strip() for c in str(s.get("corresp", "")).split(",") if c.strip()]:
                    if alvo in self.secao_principal:
                        livros.vincular_equivalente(self.op, ids[codigo], self.secao_principal[alvo])
                    else:
                        self.r.avisos.append(f"{l.get('nome')} §{codigo}: correspondência {alvo} não existe no livro principal")
        if not self.secao_principal:
            self.r.avisos.append("nenhum livro principal com seções; vínculos de seção não serão criados")

    def outros_pdfs(self) -> None:
        citados_lista = {
            s.pdf.split("#")[0] for s in self.legado.secoes if s.pdf and not s.pdf.split("#")[0].startswith("livros/")
        }
        for rel in (p.as_posix() for p in self.legado.pdfs):
            if rel in self.fonte_por_pdf:
                continue
            if rel.startswith("livros/"):
                fonte_id = self._registrar_fonte(rel, "livro")
                if fonte_id is not None:
                    livros.criar(self.op, fonte_id, "complementar", titulo_obra=Path(rel).stem)
                    self.r.decisoes.append(f"{rel}: livro sem cadastro em curso.json → complementar sem seções (Fase 3 lê o sumário)")
            elif rel in citados_lista:
                self._registrar_fonte(rel, "lista")
            else:
                self._registrar_fonte(rel, "outro")

    def listas_e_questoes(self) -> None:
        for secao in self.legado.secoes:
            unidade_id = self._unidade(secao.un)
            pdf = (secao.pdf or "").split("#")[0]
            fonte_id = self.fonte_por_pdf.get(pdf) if pdf and not pdf.startswith("livros/") else None
            lista_id = listas.criar(self.op, secao.sec, secao.nome, unidade_id, fonte_id=fonte_id, origem=ORIGEM)
            self.lista_id[secao.sec] = lista_id
            if secao.sec in self.secao_principal:
                listas.vincular_secao(self.op, lista_id, self.secao_principal[secao.sec])
            itens, avisos = regras.unificar_itens(secao)
            self.r.decisoes += avisos
            entradas = [
                QuestaoEntrada(
                    rotulo=item.numero, linha=item.linha,
                    enunciado_md=self._md(item.pede, f"{secao.sec} #{item.numero}"),
                    expressao=self._md(item.expressao, f"{secao.sec} #{item.numero}") if item.expressao else None,
                    figura=item.figura, chave_legada=f"{secao.sec}-{item.numero}",
                )
                for item in itens
            ]
            for rotulo, qid in listas.sincronizar_questoes(self.op, lista_id, entradas).items():
                self.questao_por_chave[f"{secao.sec}-{rotulo}"] = qid
                self.unidade_da_questao[qid] = unidade_id

    def marcacoes(self) -> None:
        for chave, estado in self.legado.marcacoes.items():
            if chave not in self.questao_por_chave:
                self.r.nao_resolvidos.append(f"marcação '{chave}' = {estado}: nenhuma questão com essa chave")
            elif estado not in ESTADOS_MARCACAO:
                self.r.avisos.append(f"marcação '{chave}': estado desconhecido {estado!r} ignorado")
            else:
                marcacoes.definir(self.op, self.questao_por_chave[chave], estado)

    def topicos(self) -> None:
        for chave in sorted(self.curso["unidades"], key=int):
            numero = int(chave)
            for item in self.curso["unidades"][chave].get("ondeEstamos") or []:
                status = regras.status_topico(item.get("status", ""))
                if status is None:
                    self.r.decisoes.append(
                        f"unidade {numero}: item '{item.get('titulo')}' (status {item.get('status')}) é a prova → já é evento"
                    )
                    continue
                where = (item.get("where") or "").strip()
                tid = topicos.criar(self.op, self.unidade_id[numero], self._md(item.get("titulo"), "tópico"),
                                    origem=ORIGEM, detalhe_md=self._detalhe_topico(item))
                topicos.definir_status(self.op, tid, status)
                for livro_id, codigo in regras.secoes_citadas(where, list(self.secoes_por_livro)):
                    secao_id = self.secoes_por_livro.get(livro_id, {}).get(codigo)
                    if secao_id is not None:
                        livros.vincular_topico(self.op, tid, secao_id, confianca=1.0, confirmado=True)
                    elif livro_id is None:
                        self.r.avisos.append(f"tópico '{item.get('titulo')}': {codigo} citado sem nome de livro → sem vínculo")
                    else:
                        nome = self.nome_livro.get(livro_id, livro_id)
                        self.r.avisos.append(f"tópico '{item.get('titulo')}': {nome} não tem a seção {codigo} cadastrada")
                for codigo in item.get("secoes") or []:
                    if codigo in self.lista_id:
                        listas.vincular_topico(self.op, self.lista_id[codigo], tid)
                    else:
                        self.r.avisos.append(f"tópico '{item.get('titulo')}': lista {codigo} não existe")

    def _detalhe_topico(self, item: dict) -> str:
        """Previsão de aula e referência viram cabeçalho do detalhe: nada do 'Onde estamos' se perde."""
        cabecalho = []
        lv = (item.get("lv") or "").strip()
        if lv and lv != "Visto":
            cabecalho.append(f"Previsto: {lv}")
        if (item.get("where") or "").strip():
            cabecalho.append(f"Onde: {item['where'].strip()}")
        detalhe = self._md(item.get("detalhe"), f"tópico {item.get('titulo')}")
        return "\n\n".join(p for p in ("\n".join(cabecalho), detalhe) if p)

    def liberacoes(self) -> None:
        for secao in self.legado.secoes:
            lista_id = self.lista_id[secao.sec]
            decisao = regras.liberacao(secao.locked, listas.obter(self.op.con, lista_id).aberta)
            if decisao != "auto":
                listas.definir_liberacao(self.op, lista_id, decisao)
                self.r.decisoes.append(
                    f"lista {secao.sec}: liberação fixada como '{decisao}' (a regra automática daria outro estado que o legado)"
                )

    def cronograma(self) -> None:
        for chave in sorted(self.curso["unidades"], key=int):
            numero = int(chave)
            for fase in self.curso["unidades"][chave].get("fases") or []:
                if _eh_cronograma(fase, self.ano):
                    for linha in fase.get("linhas") or []:
                        self._sessao(numero, linha)
                    if _fase_tem_textos(fase):
                        self.notas_unidade[numero] += ["", f"## {fase.get('titulo') or 'Cronograma'}", "",
                                                       *_linhas_campos(fase, CAMPOS_FASE_LEGADO)]
                else:
                    self._tabela_preservada(numero, fase)

    def _sessao(self, numero: int, linha: dict) -> None:
        d = str(linha.get("d") or "")
        data = data_curta_para_iso(d, self.ano)
        foco = self._md(linha.get("t"), f"sessão {linha.get('s')}")
        if d and data is None:
            foco = f"{d} — {foco}"
        exercicios = [str(x) for x in (linha.get("x") or []) if str(x).strip() not in _SEM_VALOR]
        if exercicios:
            foco += "\n\nExercícios: " + " · ".join(self._md(x, f"sessão {linha.get('s')}") for x in exercicios)
        sid = cronograma.criar_sessao(self.op, self.unidade_id[numero], str(linha.get("s", "")), data=data,
                                      foco_md=foco, origem=ORIGEM)
        if linha.get("feito"):
            cronograma.definir_feito(self.op, sid, True)
        ids = []
        for codigo, rotulo in (ref for x in exercicios for ref in referencias_exercicios(x)):
            qid = self.questao_por_chave.get(f"{codigo}-{rotulo}")
            if qid is None:
                self.r.avisos.append(f"sessão {linha.get('s')}: {codigo} #{rotulo} não é uma questão cadastrada")
            elif qid not in ids:
                ids.append(qid)
        if ids:
            cronograma.vincular_questoes(self.op, sid, ids)

    def _tabela_preservada(self, numero: int, fase: dict) -> None:
        colunas = list(fase.get("colunas") or [])
        linhas = []
        for linha in fase.get("linhas") or []:
            valores = [str(linha.get("s", "")), str(linha.get("d", "")), self._md(linha.get("t"), "tabela"),
                       *(self._md(str(x), "tabela") for x in linha.get("x") or [])]
            if len(valores) > len(colunas):
                valores = valores[1:]  # 's' é só o identificador interno da linha
            linhas.append((valores + [""] * len(colunas))[: len(colunas)])
        titulo = fase.get("titulo") or "Tabela"
        textos = _linhas_campos(fase, CAMPOS_FASE_LEGADO)
        self.notas_unidade[numero] += ["", f"## {titulo}", "", *textos, *([""] if textos else []),
                                       tabela_markdown(colunas, linhas)]
        self.r.decisoes.append(f"unidade {numero}: tabela '{titulo}' não é cronograma → preservada em legado-unidade-{numero}.md")

    def formulas(self) -> None:
        for chave in sorted(self.curso["unidades"], key=int):
            for f in self.curso["unidades"][chave].get("formulario") or []:
                notas = "\n".join(f"- {self._md(n, 'fórmula')}" for n in f.get("notas") or [])
                formulas.criar(self.op, self.unidade_id[int(chave)], f.get("titulo", ""), f.get("fml", ""),
                               notas_md=notas, origem=ORIGEM)

    def resumos(self) -> None:
        mapa = regras.mapa_secao_unidade(self.legado)
        extras = self.curso.get("resumosExtraUnidade") or {}
        for caminho in self.legado.resumos:
            texto = caminho.read_text(encoding="utf-8")
            decisao = regras.unidade_do_resumo(texto, mapa)
            unidade_id = self.unidade_id.get(decisao.valor) if decisao.valor else None
            if decisao.valor is None:
                self.r.nao_resolvidos.append(f"resumo {caminho.stem}: {decisao.regra} → ficou sem unidade")
            else:
                self.r.decisoes.append(f"resumo {caminho.stem}: unidade {decisao.valor} ({decisao.regra})")
            titulo = next((l.lstrip("#").strip() for l in texto.splitlines() if l.startswith("#")), caminho.stem)
            did = self._salvar_documento("resumo", caminho.name, titulo, texto, unidade_id=unidade_id)
            for numero in extras.get(caminho.stem, []):
                documentos.adicionar_unidade_extra(self.op, did, self._unidade(int(numero)))

    def resolucoes(self) -> None:
        mapa = regras.mapa_secao_unidade(self.legado)
        for caminho in self.legado.resolucoes:
            m = _RESOLUCAO.match(caminho.stem)
            chave = f"{m.group(1)}.{m.group(2)}-{m.group(3)}" if m else caminho.stem
            qid = self.questao_por_chave.get(chave)
            if qid is not None:
                unidade_id = self.unidade_da_questao[qid]
            else:
                secao = chave.split("-")[0]
                unidade_id = self.unidade_id.get(mapa[secao]) if secao in mapa else None
                self.r.nao_resolvidos.append(f"resolução {chave}: nenhuma questão com essa chave (salva sem questão)")
            self._salvar_documento("resolucao", caminho.name, f"Resolução {chave}", caminho.read_text(encoding="utf-8"),
                                   unidade_id=unidade_id, questao_id=qid)

    def documentos_config(self) -> None:
        todas = set(self.unidade_id)
        for d in self.curso.get("documentos") or []:
            src = d.get("src", "")
            origem = self.legado.pasta / src
            if not origem.is_file():
                self.r.nao_resolvidos.append(f"documento '{d.get('title')}': arquivo {src} não existe")
                continue
            unidades_doc = [int(u) for u in d.get("unidades") or []]
            principal_id = None
            if unidades_doc and set(unidades_doc) != todas:
                principal_id = self._unidade(unidades_doc[0])
            pai = PurePosixPath(src).parent.name
            did = self._salvar_documento(regras.tipo_documento_config(src), PurePosixPath(src).name, d.get("title", src),
                                         origem.read_text(encoding="utf-8"), pai=pai, unidade_id=principal_id)
            if principal_id:
                for numero in unidades_doc[1:]:
                    documentos.adicionar_unidade_extra(self.op, did, self._unidade(numero))
        skill = self.legado.pasta / "SKILL-DISCIPLINA.md"
        if skill.is_file():
            self._salvar_documento("contexto", "contexto.md", "Contexto da disciplina", skill.read_text(encoding="utf-8"))
        for numero, linhas in self.notas_unidade.items():
            if not any(l.strip() for l in linhas):
                continue
            corpo = "\n".join([f"# Dados do app legado — {numero}ª unidade", "", *linhas, ""])
            self._salvar_documento("anotacao", f"legado-unidade-{numero}.md", f"Legado — {numero}ª unidade", corpo,
                                   unidade_id=self.unidade_id[numero])

    def figuras(self) -> None:
        for figura in self.legado.figuras:
            self._vincular(figura, "figuras")


def _eh_cronograma(fase: dict, ano: int | None) -> bool:
    """Sem ano não há como ler as datas curtas: a fase é preservada como tabela."""
    return ano is not None and regras.fase_eh_cronograma(fase, ano)


def _contar(con, sql: str) -> int:
    return con.execute(sql).fetchone()[0]


def _linhas_campos(dados: dict, campos: tuple[tuple[str, str], ...]) -> list[str]:
    """Campos de texto do legado sem lugar no modelo novo, como itens de lista Markdown."""
    linhas = []
    for chave, rotulo in campos:
        valor = dados.get(chave)
        if isinstance(valor, list):
            valor = " · ".join(map(str, valor))
        if valor:
            linhas.append(f"- **{rotulo}:** {html_para_md(str(valor))[0]}")
    return linhas


def _fase_tem_textos(fase: dict) -> bool:
    return bool(_linhas_campos(fase, CAMPOS_FASE_LEGADO))


def _unidade_tem_dados_legados(u: dict, ano: int | None) -> bool:
    return bool(_linhas_campos(u, CAMPOS_UNIDADE_LEGADO)) or any(
        not _eh_cronograma(f, ano) or _fase_tem_textos(f) for f in u.get("fases") or []
    )


def _contagens_relacoes_legado(legado: Legado, ano: int | None) -> dict[str, int]:
    """Relações esperadas, calculadas só a partir dos arquivos legados (sem olhar o banco novo)."""
    curso = legado.curso
    unidades_legado = list(curso["unidades"].values())
    livros_ok = [l for l in curso.get("livros") or [] if (legado.pasta / l["arquivo"]).is_file()]
    codigos = {l["id"]: set(l.get("secoes") or {}) for l in livros_ok}
    principal = codigos[livros_ok[0]["id"]] if livros_ok else set()
    secoes_exercicio = {s.sec for s in legado.secoes}
    topicos_legado = [
        i for u in unidades_legado for i in u.get("ondeEstamos") or [] if regras.status_topico(i.get("status", ""))
    ]
    chaves = {f"{s.sec}-{i.numero}" for s in legado.secoes for i in s.itens}
    sessao_questao = 0
    for u in unidades_legado:
        for fase in u.get("fases") or []:
            if not _eh_cronograma(fase, ano):
                continue
            for linha in fase.get("linhas") or []:
                refs = {
                    f"{codigo}-{rotulo}"
                    for x in linha.get("x") or [] if str(x).strip() not in _SEM_VALOR
                    for codigo, rotulo in referencias_exercicios(str(x))
                }
                sessao_questao += len(refs & chaves)
    todas = {int(n) for n in curso["unidades"]}
    resumos = {p.stem for p in legado.resumos}
    extras = sum(len(set(v)) for k, v in (curso.get("resumosExtraUnidade") or {}).items() if k in resumos)
    for d in curso.get("documentos") or []:
        unidades_doc = [int(u) for u in d.get("unidades") or []]
        if (legado.pasta / d.get("src", "")).is_file() and unidades_doc and set(unidades_doc) != todas:
            extras += len(set(unidades_doc[1:]))
    figuras_legado = {p.stem for p in legado.figuras}
    unificados = [i for s in legado.secoes for i in regras.unificar_itens(s)[0]]
    return {
        "eventos_prova": sum(1 for u in unidades_legado if u.get("dataProva")),
        "notas": sum(1 for u in unidades_legado if nota_de_tags(u.get("tags") or []) is not None),
        "lista_secao": sum(1 for s in legado.secoes if s.sec in principal),
        "lista_topico": sum(len({c for c in i.get("secoes") or [] if c in secoes_exercicio}) for i in topicos_legado),
        "topico_secao": sum(
            len({(l, c) for l, c in regras.secoes_citadas(i.get("where") or "", list(codigos)) if c in codigos.get(l, ())})
            for i in topicos_legado
        ),
        "secao_equivalente": 2 * sum(
            1 for l in livros_ok[1:] for s in (l.get("secoes") or {}).values()
            for c in str(s.get("corresp", "")).split(",") if c.strip() in principal
        ),
        "sessao_questao": sessao_questao,
        "extras_documento": extras,
        "figuras_referenciadas": sum(1 for i in unificados if i.figura in figuras_legado),
        "itens_brutos": sum(len(s.itens) for s in legado.secoes),
    }


def _contagens_legado(legado: Legado, ano: int | None) -> dict[str, int]:
    curso = legado.curso
    unidades_legado = curso["unidades"].values()
    documentos_esperados = (
        sum(1 for d in curso.get("documentos") or [] if (legado.pasta / d.get("src", "")).is_file())
        + (legado.pasta / "SKILL-DISCIPLINA.md").is_file()
        + sum(1 for u in unidades_legado if _unidade_tem_dados_legados(u, ano))
    )
    livros_extra = [p for p in legado.pdfs if p.parts[0] == "livros"
                    and p.as_posix() not in {l["arquivo"] for l in curso.get("livros") or []}]
    questoes = sum(len(regras.unificar_itens(s)[0]) for s in legado.secoes)
    chaves = {f"{s.sec}-{i.numero}" for s in legado.secoes for i in s.itens}
    sessoes = sum(
        len(f.get("linhas") or []) for u in unidades_legado for f in u.get("fases") or [] if _eh_cronograma(f, ano)
    )
    return {
        "unidades": len(curso["unidades"]),
        "topicos": sum(1 for u in unidades_legado for i in u.get("ondeEstamos") or [] if regras.status_topico(i.get("status", ""))),
        "livros": len([l for l in curso.get("livros") or [] if (legado.pasta / l["arquivo"]).is_file()]) + len(livros_extra),
        "secoes_livro": sum(len(l.get("secoes") or {}) for l in curso.get("livros") or [] if (legado.pasta / l["arquivo"]).is_file()),
        "listas": len(legado.secoes),
        "questoes": questoes,
        "marcacoes": sum(1 for k, v in legado.marcacoes.items() if k in chaves and v in ESTADOS_MARCACAO),
        "sessoes": sessoes,
        "formulas": sum(len(u.get("formulario") or []) for u in unidades_legado),
        "resumos": len(legado.resumos),
        "resolucoes": len(legado.resolucoes),
        "documentos": documentos_esperados,
        "figuras": len(legado.figuras),
        "fontes": len(legado.pdfs),
        **_contagens_relacoes_legado(legado, ano),
    }


def _contagens_novo(con, destino: Path, duplicados: int) -> dict[str, int]:
    figuras_novas = {p.stem for p in (destino / "figuras").glob("*.png")}
    referenciadas = [r[0] for r in con.execute("SELECT figura FROM questao WHERE figura IS NOT NULL")]
    questoes = _contar(con, "SELECT count(*) FROM questao")
    return {
        "unidades": _contar(con, "SELECT count(*) FROM unidade"),
        "topicos": _contar(con, "SELECT count(*) FROM topico"),
        "livros": _contar(con, "SELECT count(*) FROM livro"),
        "secoes_livro": _contar(con, "SELECT count(*) FROM secao_livro"),
        "listas": _contar(con, "SELECT count(*) FROM lista"),
        "questoes": questoes,
        "marcacoes": _contar(con, "SELECT count(*) FROM marcacao"),
        "sessoes": _contar(con, "SELECT count(*) FROM sessao_estudo"),
        "formulas": _contar(con, "SELECT count(*) FROM formula"),
        "resumos": _contar(con, "SELECT count(*) FROM documento WHERE tipo = 'resumo'"),
        "resolucoes": _contar(con, "SELECT count(*) FROM documento WHERE tipo = 'resolucao'"),
        "documentos": _contar(con, "SELECT count(*) FROM documento WHERE tipo NOT IN ('resumo', 'resolucao')"),
        "figuras": len(figuras_novas),
        "fontes": _contar(con, "SELECT count(*) FROM fonte"),
        "eventos_prova": _contar(con, "SELECT count(*) FROM evento WHERE tipo = 'prova'"),
        "notas": _contar(con, "SELECT count(*) FROM nota_avaliacao"),
        "lista_secao": _contar(con, "SELECT count(*) FROM lista_secao"),
        "lista_topico": _contar(con, "SELECT count(*) FROM lista_topico"),
        "topico_secao": _contar(con, "SELECT count(*) FROM topico_secao"),
        "secao_equivalente": _contar(con, "SELECT count(*) FROM secao_equivalente"),
        "sessao_questao": _contar(con, "SELECT count(*) FROM sessao_questao"),
        "extras_documento": _contar(con, "SELECT count(*) FROM documento_unidade_extra"),
        "figuras_referenciadas": sum(1 for f in referenciadas if f in figuras_novas),
        "itens_brutos": questoes + duplicados,  # questões gravadas + repetições unificadas (listadas nas decisões)
    }


def migrar(origem: Path, destino: Path, forcar: bool = False) -> Relatorio:
    legado = carregar(origem)
    uid = _preparar_destino(destino, forcar)
    periodo, _ = periodo_e_instituicao(legado.curso.get("subtituloGeral", ""))
    ano = int(periodo[:4]) if periodo else None
    ref = inicializar_materia(destino, legado.curso["nome"], periodo, uid)
    relatorio = Relatorio(materia=ref.nome, gerado_em=datetime.datetime.now().isoformat(timespec="seconds"))
    if ano is None:
        relatorio.avisos.append("período sem ano (AAAA.S) em subtituloGeral: datas curtas do cronograma ficam como texto")

    with closing(conectar(ref.db)) as con:
        with operacao(con, "Migração do app legado", destino) as op:
            m = _Migracao(legado, destino, op, relatorio, ano)
            m.materia_e_unidades()
            m.livros()
            m.outros_pdfs()
            m.listas_e_questoes()
            m.marcacoes()
            m.topicos()
            m.liberacoes()
            m.cronograma()
            m.formulas()
            m.resumos()
            m.resolucoes()
            m.documentos_config()
            m.figuras()
        con.execute("DELETE FROM historico_grupo")
        duplicados = sum(len(regras.unificar_itens(s)[1]) for s in legado.secoes)
        novo = _contagens_novo(con, destino, duplicados)

    esperado = _contagens_legado(legado, ano)
    relatorio.contagens = {chave: (esperado[chave], novo[chave]) for chave in esperado}
    pasta_relatorio = destino / ".migracao"
    pasta_relatorio.mkdir(exist_ok=True)
    (pasta_relatorio / "relatorio.md").write_text(relatorio.markdown(), encoding="utf-8", newline="\n")
    return relatorio
