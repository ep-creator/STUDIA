"""Listas de exercícios → questões. Dois formatos reconhecidos:

* por seção: "Seção 15.4" seguida de linhas "o 7,8,11" (1ª linha = linha 1, 2ª = linha 2);
* numerada: "1. enunciado", "2. enunciado"… (só aceita a numeração seguinte à anterior).
"""

import re
from dataclasses import dataclass, field
from pathlib import PurePath

from estudos.importacao.idioma import normalizar, ordinal_para_int
from estudos.importacao.pdf import DocumentoPdf

_SECAO = re.compile(r"^se[çc][ãa]o\s+(\d+(?:\.\d+)*)\s*$", re.I)
_LINHA_ROTULOS = re.compile(r"^o\s+(.+)$")
_UNIDADE_TITULO = re.compile(r"exercicios d[ao] (\w+) unidade")
_LISTA_TITULO = re.compile(r"^(\w+)\s+lista\b", re.I)
_LISTA_ARQUIVO = re.compile(r"lista\s*(\d+)", re.I)
_QUESTAO = re.compile(r"^(\d{1,3})\.\s*(.*)$")
_ITEM = re.compile(r"^[a-z]\.\s")
_CONTEUDOS = re.compile(r"^conte[úu]dos?\s*:\s*(.*)$", re.I)


@dataclass
class QuestaoExtraida:
    rotulo: str
    linha: int
    enunciado_md: str = ""
    pagina_pdf: int | None = None


@dataclass
class ListaExtraida:
    codigo: str
    titulo: str
    secao_livro: str | None
    questoes: list[QuestaoExtraida] = field(default_factory=list)


@dataclass
class ArquivoListas:
    formato: str
    titulo: str
    unidade: int | None
    referencia_livro: str | None
    conteudos: list[str] = field(default_factory=list)
    listas: list[ListaExtraida] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def _linhas(doc: DocumentoPdf) -> list[tuple[int, str]]:
    return [(p.indice, l.strip()) for p in doc.paginas for l in p.texto.split("\n") if l.strip()]


def _rotulos(texto: str) -> list[str]:
    return [r.strip() for r in texto.split(",") if r.strip()]


def _por_secao(linhas: list[tuple[int, str]], arquivo: ArquivoListas) -> None:
    atual: ListaExtraida | None = None
    linha_atual = 0
    for _, linha in linhas:
        m = _SECAO.match(linha)
        if m:
            atual = ListaExtraida(m.group(1), f"Seção {m.group(1)}", m.group(1))
            arquivo.listas.append(atual)
            linha_atual = 0
            continue
        m = _LINHA_ROTULOS.match(linha)
        if not (m and atual):
            continue
        linha_atual += 1
        if linha_atual > 2:
            arquivo.avisos.append(f"{atual.codigo}: mais de duas linhas de questões; a {linha_atual}ª conta como linha 2")
        existentes = {q.rotulo: q for q in atual.questoes}
        for rotulo in _rotulos(m.group(1)):
            if rotulo in existentes:
                arquivo.avisos.append(
                    f"{atual.codigo} #{rotulo}: está nas linhas {existentes[rotulo].linha} e {min(linha_atual, 2)}; "
                    f"mantida como linha {existentes[rotulo].linha}"
                )
                continue
            existentes[rotulo] = QuestaoExtraida(rotulo, min(linha_atual, 2))
            atual.questoes.append(existentes[rotulo])


def _codigo_numerada(titulo: str, nome_arquivo: str) -> str:
    m = _LISTA_TITULO.match(titulo)
    if m and (n := ordinal_para_int(m.group(1))):
        return f"L{n}"
    m = _LISTA_ARQUIVO.search(nome_arquivo)
    if m:
        return f"L{int(m.group(1))}"
    return PurePath(nome_arquivo).stem or "Lista"


def _conteudos(linhas: list[tuple[int, str]]) -> list[str]:
    for i, (_, linha) in enumerate(linhas):
        m = _CONTEUDOS.match(linha)
        if not m:
            continue
        texto = m.group(1)
        j = i + 1
        while not texto.rstrip().endswith(".") and j < len(linhas) and texto.rstrip().endswith(","):
            texto = f"{texto} {linhas[j][1]}"
            j += 1
        return [c.strip().rstrip(".") for c in texto.split(",") if c.strip().rstrip(".")]
    return []


def _numerada(linhas: list[tuple[int, str]], arquivo: ArquivoListas, nome_arquivo: str) -> None:
    titulo = next((l for _, l in linhas if "lista de exercicios" in normalizar(l)), arquivo.titulo)
    lista = ListaExtraida(_codigo_numerada(titulo, nome_arquivo), titulo, None)
    arquivo.listas.append(lista)
    esperado = 1
    for pagina, linha in linhas:
        m = _QUESTAO.match(linha)
        if m and int(m.group(1)) == esperado:
            lista.questoes.append(QuestaoExtraida(m.group(1), 1, m.group(2).strip(), pagina))
            esperado += 1
            continue
        if not lista.questoes:
            continue
        q = lista.questoes[-1]
        separador = "\n" if _ITEM.match(linha) else " "
        q.enunciado_md = f"{q.enunciado_md}{separador}{linha}".strip()


def extrair_listas(doc: DocumentoPdf, nome_arquivo: str = "") -> ArquivoListas:
    linhas = _linhas(doc)
    titulo = next((l for _, l in linhas if "exercicio" in normalizar(l) or "lista" in normalizar(l)),
                  linhas[0][1] if linhas else PurePath(nome_arquivo).stem)
    m = _UNIDADE_TITULO.search(normalizar(titulo))
    unidade = ordinal_para_int(m.group(1)) if m else None
    referencia = next((l for _, l in linhas if l.count(",") >= 2 and re.match(r"^[A-Z]\.\s*[A-Z]", l)), None)
    formato = "por_secao" if any(_SECAO.match(l) for _, l in linhas) else "numerada"
    arquivo = ArquivoListas(formato, titulo, unidade, referencia, _conteudos(linhas))
    if formato == "por_secao":
        _por_secao(linhas, arquivo)
    else:
        _numerada(linhas, arquivo, nome_arquivo)
    return arquivo
