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
# "1. …", "1) …", "Questão 1. …", "Questão 2) …"
_QUESTAO = re.compile(r"^(?:quest[ãa]o\s+)?(\d{1,3})\s*[.)]\s*(.*)$", re.I)
_MAX_LINHAS_CONTEUDOS = 4
_ITEM = re.compile(r"^[a-z]\.\s")
_CONTEUDOS = re.compile(r"^conte[úu]dos?\s*:\s*(.*)$", re.I)
_FIM_CONTEUDOS = re.compile(r":\s*$|@|^prof(?:\.|essor)", re.I)  # cabeçalho ("Equipe:"), e-mail, "Prof. Fulano"
_NUMERO_SOLTO = re.compile(r"^\d+$")  # resto de fração/expoente ("x^{1/2}" vira "1" numa linha e "2." na outra)
_JANELA_REPETICAO = 4  # linhas entre a falsa questão e a repetição do número
_PARTE_ROMANA = re.compile(r"^[IVX]{1,4}\.\s+(\S.+)$")  # "II. Subespaços e bases": título de parte da lista


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
        # A frase de conteúdos termina no ponto final, mesmo quebrando linha no meio de um item; um cabeçalho
        # ("Equipe de professores:"), e-mail, nome de professor ou questão já é outra parte do documento
        for _, seguinte in linhas[i + 1: i + 1 + _MAX_LINHAS_CONTEUDOS]:
            if texto.rstrip().endswith(".") or _FIM_CONTEUDOS.search(seguinte) or _QUESTAO.match(seguinte):
                break
            texto = f"{texto} {seguinte}"
        itens = (c.strip().rstrip(".") for c in texto.split(","))
        return [re.sub(r"^e\s+", "", c) for c in itens if c]
    return []


def _numerada(linhas: list[tuple[int, str]], arquivo: ArquivoListas, nome_arquivo: str) -> None:
    titulo = next((l for _, l in linhas if "lista de exercicios" in normalizar(l)), arquivo.titulo)
    lista = ListaExtraida(_codigo_numerada(titulo, nome_arquivo), titulo, None)
    arquivo.listas.append(lista)
    esperado = 1
    # Questão suspeita: começou logo depois de um número solto na mesma página ("x^{1/2}" vira "1" e "2. …").
    # Se o mesmo número reaparece poucas linhas depois, a primeira ocorrência era o expoente e volta para a anterior.
    suspeita: int | None = None  # índice da linha em que a questão suspeita começou
    reiniciou = False  # depois de a numeração reiniciar (gabarito no fim) a regra não vale mais
    anterior = (None, "")
    for i, (pagina, linha) in enumerate(linhas):
        m = _QUESTAO.match(linha)
        if m and int(m.group(1)) == esperado:
            suspeita = i if anterior[0] == pagina and _NUMERO_SOLTO.match(anterior[1]) and not reiniciou else None
            lista.questoes.append(QuestaoExtraida(m.group(1), 1, m.group(2).strip(), pagina))
            esperado += 1
            anterior = (pagina, linha)
            continue
        if (m and int(m.group(1)) == esperado - 1 and suspeita is not None and len(lista.questoes) >= 2
                and i - suspeita <= _JANELA_REPETICAO):
            falsa = lista.questoes.pop()
            q = lista.questoes[-1]
            q.enunciado_md = f"{q.enunciado_md} {falsa.rotulo}. {falsa.enunciado_md}".strip()
            lista.questoes.append(QuestaoExtraida(m.group(1), 1, m.group(2).strip(), pagina))
            arquivo.avisos.append(
                f"{lista.codigo} #{m.group(1)}: número repetido; a primeira ocorrência (depois de um número solto, "
                f"provável expoente) ficou na questão {q.rotulo} — revise"
            )
            suspeita = None
            anterior = (pagina, linha)
            continue
        anterior = (pagina, linha)
        if _PARTE_ROMANA.match(linha):
            continue  # título de parte não é texto de questão
        if m and int(m.group(1)) == 1 and lista.questoes:
            reiniciou, suspeita = True, None
            arquivo.avisos.append(
                f"{lista.codigo}: a numeração reinicia em 1 depois da questão {esperado - 1} (página {pagina}); "
                "o trecho seguinte ficou junto da última questão — revise"
            )
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
    # Sem linha de "Conteúdos:", os títulos de parte em romanos ("I. Matrizes…") fazem o papel de conteúdos
    conteudos = _conteudos(linhas) or [m.group(1).strip() for _, l in linhas if (m := _PARTE_ROMANA.match(l))]
    arquivo = ArquivoListas(formato, titulo, unidade, referencia, conteudos)
    if formato == "por_secao":
        _por_secao(linhas, arquivo)
    else:
        _numerada(linhas, arquivo, nome_arquivo)
    return arquivo
