"""Leitura de PDF com PyMuPDF: páginas de texto limpo, sumário embutido e rótulos de página."""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pymupdf

# Acento solto que o LaTeX coloca antes da letra ("Ciˆencias", "Mudan¸ca") → caractere combinante
_ACENTOS = {"ˆ": "̂", "´": "́", "˜": "̃", "¸": "̧", "`": "̀", "¨": "̈"}
_ACENTO_SOLTO = re.compile(r"([ˆ´˜¸`¨])\s?([A-Za-zı])")
_LIGADURAS = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "": "•"}
_CID = re.compile(r"\(cid:\d+\)")
_ESPACOS = re.compile(r"[ \t ]+")
_DIGITOS = re.compile(r"\d+")
_MIN_PAGINAS_REPETIDOS = 5
_FRACAO_REPETIDO = 0.3
_BORDA = 2               # linhas do topo e do rodapé onde cabeçalhos repetidos aparecem
_MIN_CARACTERES = 10     # página com menos caracteres úteis que isso conta como "sem texto"
_FRACAO_SEM_TEXTO = 0.9


class PdfInvalido(ValueError):
    pass


@dataclass(frozen=True)
class PaginaPdf:
    indice: int
    rotulo: str
    texto: str
    largura: float
    altura: float


@dataclass(frozen=True)
class EntradaSumario:
    nivel: int
    titulo: str
    pagina: int


@dataclass(frozen=True)
class DocumentoPdf:
    paginas: tuple[PaginaPdf, ...]
    sumario: tuple[EntradaSumario, ...]
    metadados: dict[str, str]
    total_paginas: int  # do arquivo inteiro, mesmo quando só parte das páginas foi lida

    @property
    def sem_texto(self) -> bool:
        if not self.paginas:
            return True
        vazias = sum(1 for p in self.paginas if len("".join(p.texto.split())) < _MIN_CARACTERES)
        return vazias / len(self.paginas) >= _FRACAO_SEM_TEXTO

    def texto(self, ini: int = 1, fim: int | None = None) -> str:
        fim = fim or len(self.paginas)
        return "\n".join(p.texto for p in self.paginas if ini <= p.indice <= fim)


def _juntar_acento(m: re.Match) -> str:
    letra = "i" if m.group(2) == "ı" else m.group(2)
    return unicodedata.normalize("NFC", letra + _ACENTOS[m.group(1)])


def limpar_texto(texto: str) -> str:
    t = _ACENTO_SOLTO.sub(_juntar_acento, texto)
    for de, para in _LIGADURAS.items():
        t = t.replace(de, para)
    t = _CID.sub("", t)
    return "\n".join(_ESPACOS.sub(" ", linha).strip() for linha in t.split("\n"))


def remover_repetidos(paginas: list[str]) -> list[str]:
    """Tira cabeçalhos/rodapés: linha das bordas que se repete (com dígitos normalizados) em ≥ 30% das páginas."""
    if len(paginas) < _MIN_PAGINAS_REPETIDOS:
        return paginas
    linhas = [p.split("\n") for p in paginas]

    def bordas(ls: list[str]) -> set[str]:
        nao_vazias = [l for l in ls if l.strip()]
        return {_DIGITOS.sub("#", l.strip()) for l in nao_vazias[:_BORDA] + nao_vazias[-_BORDA:]}

    contagem = Counter(chave for ls in linhas for chave in bordas(ls))
    repetidas = {chave for chave, n in contagem.items() if n >= _FRACAO_REPETIDO * len(paginas)}
    resultado = []
    for ls in linhas:
        candidatas = bordas(ls)
        resultado.append("\n".join(
            l for l in ls if not (l.strip() and _DIGITOS.sub("#", l.strip()) in repetidas & candidatas)
        ))
    return resultado


# ---- Leitura por fonte e posição (só o índice da busca usa) ---------------------------------------------------------
#
# A leitura "texto pronto" segue a ordem em que o PDF gravou os pedaços: fórmulas saem fora da frase, colunas se
# misturam. Aqui cada pedaço vem com fonte e caixa: o texto de cada fonte passa pela tabela dela (símbolos que a fonte
# guarda no lugar de letras) e a página é remontada pela posição — borda de cima e de baixo à parte, depois um corte
# recursivo em colunas (vão vertical) e faixas (vão horizontal), e em cada pedaço final as linhas por altura.

_FAIXA_BORDA = 0.06       # fração da altura: topo e rodapé (cabeçalho, número da página) saem à parte
_VAO_COLUNA = 0.015       # fração da largura: vão vertical que separa colunas
_VAO_FAIXA = 0.8          # × altura mediana dos pedaços: vão horizontal que separa faixas
_MARGEM_ESTREITA = 0.35   # coluna mais estreita que isso (fração do bloco) é margem: vai depois do texto
_TITULO = 1.2             # fonte 20% maior que a mediana do bloco: título (pode passar por cima de um vão)
_LINHAS_PARA_ICONE = 10   # blocos com 10 linhas de altura ou mais: glifo solto (≤ 2 letras) não fecha vão de coluna
_LINHAS_PARA_MARGEM = 3   # só blocos com ao menos 3 linhas de altura reordenam margens (uma fórmula partida não)
_GRUPOS_RECENTES = 8       # linhas abertas em que um pedaço novo ainda pode entrar
_SOBREPOSICAO = 0.5       # dois pedaços estão na mesma linha se se sobrepõem em metade da altura do menor
_PEQUENO = 0.8            # pedaço menor que 80% do maior da linha, acima ou abaixo do centro: expoente ou índice
_SOBRE = str.maketrans("0123456789+-−ni", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻ⁿⁱ")
_SOB = str.maketrans("0123456789+-−aeoxhklmnpstij", "₀₁₂₃₄₅₆₇₈₉₊₋₋ₐₑₒₓₕₖₗₘₙₚₛₜᵢⱼ")
_SEM_TRADUCAO = re.compile(r"[-\x00-\x08\x0b-\x1f]")   # uso privado e controles: sem tabela, saem
_PREFIXO_FONTE = re.compile(r"^[A-Z]{6}\+")


# Stewart: a Times-Roman desenha "M" em branco como espaço largo nas fórmulas ("2θ,Mr = cos 2θ"), e a vírgula vem em
# outro pedaço; em texto corrido depois de vírgula sempre vem espaço, então ",M" colado no que segue é esse espaço
_ESPACO_LARGO = re.compile(r",M(?=\S)")


def _traduzir(span: dict, tabelas: dict[str, dict[str, str]]) -> tuple[str, int]:
    familia = _PREFIXO_FONTE.sub("", span["font"])
    tabela = tabelas.get(familia, {})
    texto = "".join(tabela.get(c, c) for c in span["text"]) if tabela else span["text"]
    return _SEM_TRADUCAO.subn("", texto)


def _encaixar(linha: list[dict]) -> list[dict]:
    """Pedaço curto (uma variável, um símbolo) que cai dentro de um pedaço de texto da mesma linha divide o texto no
    espaço mais próximo da sua posição ("geradores para , isto é" + "W" → "geradores para W, isto é")."""
    curtos = [s for s in linha if len(s["texto"].strip()) <= 3]
    resultado = [s for s in linha if s not in curtos]
    for c in curtos:
        meio = (c["bbox"][0] + c["bbox"][2]) / 2
        alvo = next((t for t in resultado if len(t["texto"]) > 3
                     and t["bbox"][0] < meio < t["bbox"][2]), None)
        if alvo is not None:
            texto, x0, x1 = alvo["texto"], alvo["bbox"][0], alvo["bbox"][2]
            letra = (x1 - x0) / max(len(texto), 1)
            espacos = [i for i, ch in enumerate(texto) if ch == " " and 0 < i < len(texto) - 1]
            if espacos:
                # espaço antes de pontuação ("para , isto", "nulo .") é onde o glifo saiu: vence se estiver perto
                distancia = lambda i: abs(x0 + (i + 0.5) * letra - meio)
                antes_de_pontuacao = [i for i in espacos if texto[i + 1] in ",.;:)" and distancia(i) <= 3 * letra]
                i = min(antes_de_pontuacao or espacos, key=distancia)
                resultado.remove(alvo)  # as metades ficam de um lado e do outro do glifo encaixado
                resultado += [{**alvo, "texto": texto[:i + 1], "bbox": [x0, alvo["bbox"][1], c["bbox"][0], alvo["bbox"][3]]},
                              {**alvo, "texto": texto[i:], "bbox": [c["bbox"][2], alvo["bbox"][1], x1, alvo["bbox"][3]]}]
        resultado.append(c)
    return resultado


def _base(grupo: list[dict]) -> dict:
    """Pedaço de referência da linha (o texto corrido): o de mais letras; no empate, o maior."""
    return max(grupo, key=lambda o: (len(o["texto"].strip()), o["size"]))


def _linhas(spans: list[dict]) -> list[str]:
    """Pedaços de uma coluna → linhas: mesma altura juntam, da esquerda para a direita; expoentes e índices grudam."""
    grupos: list[list[dict]] = []
    bases: list[dict] = []   # base de cada grupo, atualizada ao entrar pedaço (recalcular a cada vez é quadrático)
    for s in sorted(spans, key=lambda s: ((s["bbox"][1] + s["bbox"][3]) / 2, s["bbox"][0])):
        y0, y1 = s["bbox"][1], s["bbox"][3]
        # os pedaços vêm por altura: só os grupos mais recentes podem ser da mesma linha (frações empilhadas
        # intercalam algumas linhas; 8 grupos cobrem isso)
        achou = False
        for k in range(max(0, len(grupos) - _GRUPOS_RECENTES), len(grupos)):
            base = bases[k]
            sobra = min(y1, base["bbox"][3]) - max(y0, base["bbox"][1])
            if sobra > _SOBREPOSICAO * min(y1 - y0, base["bbox"][3] - base["bbox"][1]):
                grupos[k].append(s)
                bases[k] = _base([base, s])
                achou = True
                break
        if not achou:
            grupos.append([s])
            bases.append(s)
    linhas = []
    for g in sorted(grupos, key=lambda g: min(s["bbox"][1] for s in g)):
        g = _encaixar(g)
        base = _base(g)
        meio, altura = (base["bbox"][1] + base["bbox"][3]) / 2, base["bbox"][3] - base["bbox"][1]
        texto, fim = "", None
        for s in sorted(g, key=lambda s: s["bbox"][0]):
            parte = s["texto"]
            centro = (s["bbox"][1] + s["bbox"][3]) / 2
            pequeno = s["size"] < _PEQUENO * base["size"]
            if pequeno and centro < meio - 0.15 * altura:
                parte = parte.strip().translate(_SOBRE)
            elif pequeno and centro > meio + 0.15 * altura:
                parte = parte.strip().translate(_SOB)
            elif fim is not None and s["bbox"][0] - fim > 0.15 * s["size"] and texto and not texto[-1].isspace() \
                    and not parte[:1].isspace():
                texto += " "
            texto += parte
            fim = s["bbox"][2]
        if texto.strip():
            linhas.append(texto)
    return linhas


def _vaos(intervalos: list[tuple[float, float]], ini: float, fim: float, minimo: float) -> list[float]:
    """Pontos de corte: meio de cada vão livre (≥ minimo) entre os intervalos, sem contar as margens de fora."""
    cortes, alcance = [], None
    for a, b in sorted(intervalos):
        if alcance is not None and a - alcance >= minimo:
            cortes.append((alcance + a) / 2)
        alcance = b if alcance is None else max(alcance, b)
    return [c for c in cortes if ini < c < fim]


def _pode_cruzar(s: dict, corpo: float, alto: bool) -> bool:
    """Pedaços que não fecham um vão de coluna: títulos (fonte 20% maior que a do bloco, como o título da seção que
    passa por cima da margem) e, em blocos altos, glifos soltos de até 2 letras (ícones no vão entre colunas)."""
    if s["size"] >= _TITULO * corpo:
        return True
    return alto and len(s["texto"].strip()) <= 2


def _cortar_xy(spans: list[dict], largura: float, altura: float, h_mediana: float, corpo: float) -> list[str]:
    """`h_mediana` e `corpo`: altura e tamanho de fonte medianos da página inteira (não do bloco)."""
    if len(spans) <= 1:
        return _linhas(spans)
    x0, x1 = min(s["bbox"][0] for s in spans), max(s["bbox"][2] for s in spans)
    y0, y1 = min(s["bbox"][1] for s in spans), max(s["bbox"][3] for s in spans)
    alto = (y1 - y0) >= _LINHAS_PARA_ICONE * h_mediana
    presos = [s for s in spans if not _pode_cruzar(s, corpo, alto)]
    colunas = _vaos([(s["bbox"][0], s["bbox"][2]) for s in presos], x0, x1, _VAO_COLUNA * largura)
    if colunas:
        limites = [x0 - 1, *colunas, x1 + 1]
        cruza = lambda s: any(s["bbox"][0] < c < s["bbox"][2] for c in colunas)  # título por cima da margem
        partes = [[s for s in spans if not cruza(s) and a <= (s["bbox"][0] + s["bbox"][2]) / 2 < b]
                  for a, b in zip(limites, limites[1:])]
        partes = [p for p in partes if p] or [[]]
        largo = lambda p: max(s["bbox"][2] for s in p) - min(s["bbox"][0] for s in p) if p else 0
        max(partes, key=largo).extend(s for s in spans if cruza(s))  # quem cruza fica com o texto principal
        if (y1 - y0) >= _LINHAS_PARA_MARGEM * h_mediana:  # margens estreitas (figuras, notas) depois do texto
            partes.sort(key=lambda p: largo(p) < _MARGEM_ESTREITA * (x1 - x0))
        return [l for p in partes for l in _cortar_xy(p, largura, altura, h_mediana, corpo)]
    faixas = _vaos([(s["bbox"][1], s["bbox"][3]) for s in spans], y0, y1, _VAO_FAIXA * h_mediana)
    if faixas:
        limites = [y0 - 1, *faixas, y1 + 1]
        partes = [[s for s in spans if a <= (s["bbox"][1] + s["bbox"][3]) / 2 < b] for a, b in zip(limites, limites[1:])]
        return [l for p in partes if p for l in _cortar_xy(p, largura, altura, h_mediana, corpo)]
    return _linhas(spans)


def montar_texto(spans: list[dict], largura: float, altura: float, tabelas: dict[str, dict[str, str]]) -> tuple[str, int]:
    """Texto da página a partir dos pedaços ({"font", "size", "bbox", "text"}) e quantos caracteres ficaram sem tradução."""
    sem_traducao = 0
    uteis = []
    for s in spans:
        texto, n = _traduzir(s, tabelas)
        sem_traducao += n
        if texto.strip():
            uteis.append({**s, "texto": texto})
    if not uteis:
        return "", sem_traducao
    topo = [s for s in uteis if s["bbox"][3] <= _FAIXA_BORDA * altura]
    rodape = [s for s in uteis if s["bbox"][1] >= (1 - _FAIXA_BORDA) * altura]
    nas_bordas = {id(s) for s in topo + rodape}
    meio = [s for s in uteis if id(s) not in nas_bordas]
    alturas = sorted(s["bbox"][3] - s["bbox"][1] for s in meio) or [1.0]
    h_mediana = alturas[len(alturas) // 2]
    tamanhos = sorted(s["size"] for s in meio) or [1.0]
    corpo = tamanhos[len(tamanhos) // 2]
    linhas = _linhas(topo) + _cortar_xy(meio, largura, altura, h_mediana, corpo) + _linhas(rodape)
    return _ESPACO_LARGO.sub(", ", limpar_texto("\n".join(linhas))), sem_traducao


_DIFERENCAS = re.compile(r"/Differences\s*\[(.*?)\]", re.S)


def _diferencas(doc: pymupdf.Document, xref: int) -> dict[int, str]:
    """Código → nome do glifo, da lista /Differences da codificação da fonte (vazio se não há)."""
    codificacao = doc.xref_get_key(xref, "Encoding")
    if codificacao[0] != "xref":
        return {}
    achado = _DIFERENCAS.search(doc.xref_object(int(codificacao[1].split()[0])))
    mapa, codigo = {}, 0
    for parte in achado.group(1).split() if achado else []:
        if parte.startswith("/"):
            mapa[codigo] = parte[1:]
            codigo += 1
        else:
            codigo = int(parte)
    return mapa


def traducao_por_nomes(diferencas: dict[int, str], familia: str) -> dict[str, str]:
    """Caractere que o PDF entrega (o próprio código) → texto, pelos nomes dos glifos da família."""
    from estudos.importacao.fontes_matematicas import por_nome
    nomes = por_nome(familia)
    return {chr(codigo): nomes[nome] for codigo, nome in diferencas.items() if nome in nomes}


def traducoes_da_pagina(doc: pymupdf.Document, pagina: pymupdf.Page) -> dict[str, dict[str, str]]:
    """Tabelas de tradução para os pedaços desta página: as fixas (por letra) mais as que saem dos nomes dos glifos
    das fontes da página (o mesmo nome de fonte pode ter outra codificação em outra página)."""
    from estudos.importacao.fontes_matematicas import TABELAS
    tabelas = {f: dict(t) for f, t in TABELAS.items()}
    for xref, _, _, base, *_ in pagina.get_fonts():
        familia = _PREFIXO_FONTE.sub("", base)
        if traducao := traducao_por_nomes(_diferencas(doc, xref), familia):
            tabelas.setdefault(familia, {}).update(traducao)
    return tabelas


def ler_paginas_limpas(caminho: Path, tabelas: dict[str, dict[str, str]] | None = None) -> tuple[list[PaginaPdf], int]:
    """Páginas com o texto remontado e o total de caracteres sem tradução retirados. Sem `tabelas`, cada página usa
    `traducoes_da_pagina`. Página em que a leitura detalhada falha usa a leitura de `abrir_pdf`."""
    try:
        doc = pymupdf.open(stream=caminho.read_bytes(), filetype="pdf")
    except Exception as e:  # mesmos casos de abrir_pdf
        raise PdfInvalido(f"Não foi possível abrir {caminho.name} como PDF: {e}") from None
    with doc:
        if not doc.is_pdf or doc.needs_pass:
            raise PdfInvalido(f"{caminho.name} não pode ser lido.")
        textos, total = [], 0
        for p in doc:
            try:
                blocos = p.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"]  # sem imagens: em PDF escaneado custam ~70x
                spans = [s for b in blocos for l in b.get("lines", []) for s in l["spans"]]
                texto, n = montar_texto(spans, p.rect.width, p.rect.height,
                                        tabelas if tabelas is not None else traducoes_da_pagina(doc, p))
                total += n
            except Exception:  # página com estrutura estranha: a leitura de sempre
                texto = limpar_texto(p.get_text())
            textos.append(texto)
        textos = remover_repetidos(textos)
        paginas = [PaginaPdf(indice=i + 1, rotulo=p.get_label() or "", texto=textos[i], largura=p.rect.width,
                             altura=p.rect.height) for i, p in enumerate(doc)]
    return paginas, total


def abrir_pdf(caminho: Path, limite_paginas: int | None = None) -> DocumentoPdf:
    try:
        # Abre a partir dos bytes: no Windows, um PDF que falha ao abrir ficaria preso pelo PyMuPDF
        doc = pymupdf.open(stream=caminho.read_bytes(), filetype="pdf")
    except Exception as e:  # PyMuPDF levanta tipos variados para arquivo inválido
        raise PdfInvalido(f"Não foi possível abrir {caminho.name} como PDF: {e}") from None
    with doc:
        if not doc.is_pdf:
            raise PdfInvalido(f"{caminho.name} não é um PDF.")
        if doc.needs_pass:
            raise PdfInvalido(f"{caminho.name} está protegido por senha.")
        total = doc.page_count if limite_paginas is None else min(doc.page_count, limite_paginas)
        brutas = [doc[i] for i in range(total)]
        textos = remover_repetidos([limpar_texto(p.get_text()) for p in brutas])
        paginas = tuple(
            PaginaPdf(indice=i + 1, rotulo=p.get_label() or "", texto=textos[i], largura=p.rect.width, altura=p.rect.height)
            for i, p in enumerate(brutas)
        )
        sumario = tuple(EntradaSumario(nivel=n, titulo=limpar_texto(t), pagina=pg) for n, t, pg, *_ in doc.get_toc())
        metadados = {k: v for k, v in (doc.metadata or {}).items() if v}
        total_paginas = doc.page_count
    return DocumentoPdf(paginas=paginas, sumario=sumario, metadados=metadados, total_paginas=total_paginas)
