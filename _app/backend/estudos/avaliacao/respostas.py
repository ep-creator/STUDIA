"""Respostas aceitas do gabarito e como um resultado da busca casa com elas.

Formatos:
    secao:<código>                         seção de qualquer livro com esse código
    documento:<título>[#<bloco>]           documento (resumo, resolução…); bloco = âncora do título ## (slug)
    fonte:<título ou nome do arquivo>[#p<N>[-<M>]]   arquivo (slide, lista, prova…); página ou faixa de páginas

Dois níveis: "arquivo" (qualquer página ou bloco do que foi aceito) e "trecho" (só a página ou o bloco indicados —
o que a IA precisa para citar o lugar certo). Sem página nem bloco, os dois níveis são iguais.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath

from estudos.rag.busca import Resultado

TIPOS = ("secao", "documento", "fonte")
_PAGINAS = re.compile(r"^p(\d+)(?:-(\d+))?$")


@dataclass(frozen=True)
class Aceita:
    tipo: str
    valor: str
    pag_ini: int | None = None
    pag_fim: int | None = None
    bloco: str | None = None

    @property
    def precisa(self) -> bool:
        return self.pag_ini is not None or self.bloco is not None


def ler_aceita(texto: str) -> Aceita:
    tipo, _, resto = texto.partition(":")
    if tipo not in TIPOS or not resto.strip():
        raise ValueError(f"resposta aceita inválida: {texto!r} (use secao:, documento: ou fonte:)")
    valor, _, ancora = resto.partition("#")
    if not ancora:
        return Aceita(tipo, valor.strip())
    if tipo == "documento":
        return Aceita(tipo, valor.strip(), bloco=ancora.strip())
    m = _PAGINAS.match(ancora.strip())
    if not m:
        raise ValueError(f"página inválida em {texto!r} (use #p5 ou #p5-7)")
    ini, fim = int(m.group(1)), int(m.group(2) or m.group(1))
    if fim < ini:
        raise ValueError(f"faixa de páginas invertida em {texto!r}")
    return Aceita(tipo, valor.strip(), ini, fim)


def _slug(texto: str) -> str:
    """A mesma âncora que o frontend dá aos títulos ## (markdown.ts: slugTitulo)."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def casa(
    fontes: dict[int, tuple[str, str]], documentos: dict[int, str], r: Resultado, aceita: Aceita, trecho: bool
) -> bool:
    """`fontes`: id → (título, caminho); `documentos`: id → título. Com `trecho`, página e bloco também precisam bater."""
    if aceita.tipo == "secao":
        ok = r.secao_codigo == aceita.valor
    elif aceita.tipo == "documento":
        ok = r.documento_id is not None and documentos.get(r.documento_id) == aceita.valor
        if ok and trecho and aceita.bloco:
            _, _, titulo_bloco = r.titulo.rpartition(" — ")
            ok = bool(titulo_bloco) and _slug(titulo_bloco) == aceita.bloco
        return ok
    else:
        titulo, caminho = fontes.get(r.fonte_id, ("", "")) if r.fonte_id is not None else ("", "")
        ok = r.fonte_id is not None and aceita.valor in (titulo, PurePosixPath(caminho).stem)
    if ok and trecho and aceita.pag_ini is not None:
        # o trecho cobre [pagina, pagina_fim]: acerta se a faixa aceita e a do trecho se cruzam
        fim = r.pagina_fim if r.pagina_fim is not None else r.pagina
        ok = r.pagina is not None and r.pagina <= aceita.pag_fim and fim >= aceita.pag_ini
    return ok
