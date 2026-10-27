"""Corte de um livro em teoria, exercícios e respostas, para a busca separar o que explica do que pede para resolver.

O texto das páginas é lido como um fluxo só: cada seção começa na linha do seu título (o resto da página é da seção
anterior), e dentro dela a linha "Exercícios" separa a teoria dos exercícios numerados. O gabarito do fim do livro é
cortado pelo código da seção e pelo número de cada resposta.
"""

import dataclasses
import re
from dataclasses import dataclass

from estudos.importacao.idioma import sem_acento
from estudos.rag.trechos import _PARAGRAFO, TrechoNovo, _agrupar, _cortar

LIMITE_TEORIA = 1200       # caracteres por trecho de teoria (escolhido pela avaliação do passo 1 da B2)
_MIN_EXERCICIO = 200       # exercício mais curto que isso se junta ao seguinte
_ITEM = re.compile(r"^\s*(\d{1,3})\.(\s|$)")                     # "1. texto" ou "1." sozinho (Stewart)
_CABECALHO_EXERCICIOS = re.compile(r"^([\d.]+\s+)?exercicios(\s+[\d.]+)?[\s=\-–—_]*$")  # "14.2 Exercícios", "Exercícios 14.2"
_CABECALHO_GABARITO = re.compile(r"^(?:exercicios\s+)?(\d+(?:\.\d+)+)(?:\s+exercicios)?$")  # "14.1", "EXERCÍCIOS 14.1"


@dataclass(frozen=True)
class SecaoCorte:
    id: int
    codigo: str
    titulo: str
    pagina_ini: int
    pagina_fim: int


def _normal(texto: str) -> str:
    return " ".join(sem_acento(texto).lower().split())


def _abre_secao(linhas: list[tuple[int, str]], i: int, s: SecaoCorte) -> bool:
    """A linha i (ou ela com a seguinte) é o título da seção: código + título, ou só o título."""
    titulo, codigo = _normal(s.titulo), s.codigo
    atual = _normal(linhas[i][1])
    if atual == titulo or (atual.startswith(codigo) and titulo in atual):
        return True
    if atual == codigo and i + 1 < len(linhas):
        return titulo in _normal(linhas[i + 1][1])
    return False


def _inicios(linhas: list[tuple[int, str]], secoes: list[SecaoCorte]) -> list[int]:
    """Índice da linha onde cada seção começa: o título na página inicial; sem título, o começo da página."""
    inicios: list[int] = []
    for k, s in enumerate(secoes):
        minimo = inicios[-1] + 1 if inicios else 0
        na_pagina = [i for i in range(minimo, len(linhas)) if linhas[i][0] == s.pagina_ini]
        achado = next((i for i in na_pagina if _abre_secao(linhas, i, s)), None)
        if k == 0:
            inicio = 0        # o que vem antes da primeira seção (abertura do capítulo) fica com ela
        elif achado is not None:
            inicio = achado
        elif na_pagina:
            inicio = na_pagina[0]
        else:
            inicio = next((i for i in range(minimo, len(linhas)) if linhas[i][0] >= s.pagina_ini), len(linhas))
        inicios.append(max(inicio, minimo))
    return inicios


def _pecas(linhas: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Linhas → parágrafos por página, no formato que `_agrupar` recebe."""
    por_pagina: list[tuple[int, list[str]]] = []
    for pagina, linha in linhas:
        if por_pagina and por_pagina[-1][0] == pagina:
            por_pagina[-1][1].append(linha)
        else:
            por_pagina.append((pagina, [linha]))
    return [(p, par.strip()) for p, ls in por_pagina for par in _PARAGRAFO.split("\n".join(ls)) if par.strip()]


def _itens(linhas: list[tuple[int, str]], em_sequencia: bool) -> list[tuple[int | None, list[tuple[int, str]]]]:
    """Linhas → itens numerados. Com `em_sequencia`, abre item um número ainda não visto e perto do maior já visto (até
    10 acima ou até 20 abaixo: a leitura às vezes troca um item ou uma coluna de lugar), ou um 1 que reinicia a contagem
    (só quando o próximo item numerado é 2: um rodapé "1. Dicas…" no fim da página não reinicia)."""
    itens: list[tuple[int | None, list[tuple[int, str]]]] = []
    numeros = [int(m.group(1)) if (m := _ITEM.match(l)) else None for _, l in linhas]
    seguinte = [None] * len(numeros)  # próximo número de item depois de cada linha
    proximo = None
    for i in range(len(numeros) - 1, -1, -1):
        seguinte[i] = proximo
        if numeros[i] is not None:
            proximo = numeros[i]
    ultimo, vistos = 0, set()
    for i, (pagina, linha) in enumerate(linhas):
        n = numeros[i]
        reinicia = n == 1 and seguinte[i] == 2
        if n is None:
            abre = False
        elif not em_sequencia:
            abre = n > ultimo
        elif reinicia and 1 in vistos:
            abre, vistos, ultimo = True, set(), 0
        else:
            abre = n not in vistos and (ultimo - 20 <= n <= ultimo + 10)
        if abre:
            itens.append((n, [(pagina, linha)]))
            vistos.add(n)
            ultimo = max(ultimo, n)
        elif itens:
            itens[-1][1].append((pagina, linha))
        else:
            itens.append((None, [(pagina, linha)]))   # texto antes do primeiro item
    return itens


def _trechos_de_itens(itens, titulo: str, parte: str, secao_id: int, limite: int, juntar: bool) -> list[TrechoNovo]:
    if juntar:  # prefixo e itens curtos se juntam ao seguinte, com o número do primeiro
        juntos: list[tuple[int | None, list[tuple[int, str]]]] = []
        pendente: tuple[int | None, list[tuple[int, str]]] | None = None
        for numero, ls in itens:
            if pendente is not None:
                numero, ls = (pendente[0] if pendente[0] is not None else numero), pendente[1] + ls
                pendente = None
            if len("\n".join(l for _, l in ls)) < _MIN_EXERCICIO:
                pendente = (numero, ls)
            else:
                juntos.append((numero, ls))
        if pendente is not None:
            juntos.append(pendente)
        itens = juntos
    trechos = []
    for numero, ls in itens:
        texto = "\n".join(l for _, l in ls).strip()
        if not texto:
            continue
        for parte_texto in _cortar(texto, limite):
            trechos.append(TrechoNovo(titulo, parte_texto, ls[0][0], 0, ls[-1][0], parte, numero, secao_id))
    return trechos


def _separar_exercicios(linhas: list[tuple[int, str]], codigo: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """(teoria, exercícios): tudo depois do primeiro cabeçalho "Exercícios" é exercício; os cabeçalhos saem."""
    for i, (_, linha) in enumerate(linhas):
        if _CABECALHO_EXERCICIOS.match(_normal(linha)):
            resto = [(p, l) for p, l in linhas[i + 1:] if not _CABECALHO_EXERCICIOS.match(_normal(l))]
            if resto and resto[0][1].strip() == codigo:   # "Exercícios" numa linha e o código na seguinte
                resto = resto[1:]
            return linhas[:i], resto
    return linhas, []


def _numerar(trechos: list[TrechoNovo]) -> list[TrechoNovo]:
    return [dataclasses.replace(t, ordem=i) for i, t in enumerate(trechos, 1)]


def cortar_livro(paginas: list[tuple[int, str]], secoes: list[SecaoCorte], limite: int) -> list[TrechoNovo]:
    """`secoes` são as folhas, em ordem de página. Cada trecho sai com a seção, a parte e (exercícios) o número.
    Páginas fora de todas as seções (capítulos não cadastrados entre duas seções) ficam fora."""
    dentro = {p for s in secoes for p in range(s.pagina_ini, s.pagina_fim + 1)}
    linhas = [(p, l) for p, texto in paginas if p in dentro for l in (texto or "").split("\n")]
    if not secoes or not linhas:
        return []
    inicios = _inicios(linhas, secoes) + [len(linhas)]
    trechos: list[TrechoNovo] = []
    for k, s in enumerate(secoes):
        # até onde vai: as páginas da seção e, se a seguinte começa no meio de uma página, o topo dessa página
        ultima = max(s.pagina_fim, secoes[k + 1].pagina_ini if k + 1 < len(secoes) else s.pagina_fim)
        trecho_linhas = [(p, l) for p, l in linhas[inicios[k]:inicios[k + 1]] if p <= ultima]
        titulo = f"{s.codigo} {s.titulo}"
        teoria, exercicios = _separar_exercicios(trecho_linhas, s.codigo)
        trechos += [dataclasses.replace(t, secao_id=s.id) for t in _agrupar(_pecas(teoria), titulo, limite)]
        trechos += _trechos_de_itens(_itens(exercicios, em_sequencia=True), titulo, "exercicio", s.id, limite, juntar=True)
    return _numerar(trechos)


def cortar_gabarito(paginas: list[tuple[int, str]], codigos: dict[str, int], limite: int) -> list[TrechoNovo]:
    """Respostas por seção (linha só com o código) e número; seções desconhecidas ficam fora."""
    blocos: list[tuple[str, list[tuple[int, str]]]] = []
    atual: str | None = None
    for pagina, texto in paginas:
        for linha in (texto or "").split("\n"):
            cabecalho = _CABECALHO_GABARITO.match(_normal(linha))
            if cabecalho:
                atual = cabecalho.group(1) if cabecalho.group(1) in codigos else None
                if atual is not None:
                    blocos.append((atual, []))
            elif atual is not None:
                blocos[-1][1].append((pagina, linha))
    trechos: list[TrechoNovo] = []
    for codigo, ls in blocos:
        itens = [(n, l) for n, l in _itens(ls, em_sequencia=False) if n is not None]
        trechos += _trechos_de_itens(itens, f"Respostas {codigo}", "resposta", codigos[codigo], limite, juntar=False)
    return _numerar(trechos)
