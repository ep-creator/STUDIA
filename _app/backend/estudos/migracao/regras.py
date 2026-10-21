"""Regras explícitas que decidem cada mapeamento ambíguo do legado. Cada decisão cita a regra aplicada."""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath

from estudos.migracao.conversao import data_curta_para_iso
from estudos.migracao.legado import ItemLegado, Legado, SecaoLegado

_MARCADOR_UNIDADE = re.compile(r"\b([1-9])\s*[ªaº°]\s*unidade\b|\bunidade\s*:\s*([1-9])\b", re.I)
_CODIGO_SECAO = re.compile(r"\b(\d{1,2}\.\d{1,2}|L\d+)\b")
_CODIGO_SECAO_LIVRO = re.compile(r"\b(\d{1,2}\.\d{1,2})\b")
_CODIGO_CAPITULO_OU_SECAO = re.compile(r"\b(\d{1,2}(?:\.\d{1,2})?)\b")
_STATUS_TOPICO = {"seen": "visto", "next": "proxima", "later": "pendente"}
_LIMIAR_CRONOGRAMA = 0.5


@dataclass(frozen=True)
class Decisao:
    valor: object
    regra: str


def mapa_secao_unidade(legado: Legado) -> dict[str, int]:
    """Unidade de cada seção como o usuário cadastrou em exercicios.json — a única fonte explícita."""
    return {s.sec: s.un for s in legado.secoes}


def unidade_do_resumo(texto: str, mapa: dict[str, int]) -> Decisao:
    cabecalho = texto[:400]
    m = _MARCADOR_UNIDADE.search(cabecalho)
    if m:
        numero = int(m.group(1) or m.group(2))
        return Decisao(numero, f"marcador '{m.group(0)}' no cabeçalho")
    titulo = next((l for l in texto.splitlines() if l.strip()), "")
    if titulo.startswith("#"):
        for codigo in _CODIGO_SECAO.findall(titulo):
            if codigo in mapa:
                return Decisao(mapa[codigo], f"seção {codigo} do título, cadastrada na unidade {mapa[codigo]} (exercicios.json)")
    return Decisao(None, "sem marcador nem seção conhecida")


def status_topico(status_legado: str) -> str | None:
    """'prova' não vira tópico: a prova já é um evento da unidade."""
    return _STATUS_TOPICO.get(status_legado)


def fase_eh_cronograma(fase: dict, ano: int) -> bool:
    linhas = fase.get("linhas") or []
    if not linhas:
        return False
    com_data = sum(1 for l in linhas if data_curta_para_iso(str(l.get("d", "")), ano))
    return com_data / len(linhas) >= _LIMIAR_CRONOGRAMA


def liberacao(locked: bool, aberta_pela_regra_auto: bool) -> str:
    """Usa 'auto' só quando a regra automática já reproduz o estado do legado; senão fixa o estado atual."""
    if (not locked) == aberta_pela_regra_auto:
        return "auto"
    return "travada" if locked else "aberta"


def unificar_itens(secao: SecaoLegado) -> tuple[list[ItemLegado], list[str]]:
    """Um mesmo número nas duas linhas é uma única questão; fica a primeira ocorrência (linha 1)."""
    vistos: dict[str, ItemLegado] = {}
    avisos = []
    for item in secao.itens:
        if item.numero in vistos:
            avisos.append(
                f"{secao.sec} #{item.numero}: está nas linhas {vistos[item.numero].linha} e {item.linha}; "
                f"mantida como linha {vistos[item.numero].linha}"
            )
            continue
        vistos[item.numero] = item
    return list(vistos.values()), avisos


def _normalizar(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))


def secoes_citadas(where: str, livros: list[str]) -> list[tuple[str | None, str]]:
    """Cada trecho separado por '·' cita um livro pelo nome no início ('Stewart 14.3', 'Guidorizzi cap. 8').

    Os códigos de um trecho pertencem ao livro citado nele; trecho sem livro conhecido devolve (None, código),
    para virar aviso — nunca é atribuído ao livro principal por suposição.
    """
    citacoes = []
    for trecho in where.split("·"):
        palavras = _normalizar(trecho).split()
        livro = next((l for l in livros if palavras and palavras[0] == _normalizar(l)), None)
        padrao = _CODIGO_CAPITULO_OU_SECAO if livro else _CODIGO_SECAO_LIVRO
        citacoes += [(livro, codigo) for codigo in padrao.findall(trecho)]
    return citacoes


def tipo_documento_config(src: str) -> str:
    return "plano" if PurePosixPath(src).name.startswith("plano-estudos-") else "anotacao"
