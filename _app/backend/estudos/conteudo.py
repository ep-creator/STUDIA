"""Markdown com frontmatter (`chave: valor`) e escrita versionada pelo histórico."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from estudos.historico import Operacao, versionar_arquivo

_DELIMITADOR = "---"
_AMBIGUO = re.compile(r'^(\d+|null|\s.*|.*\s|".*)$|\n')


@dataclass
class DocumentoMd:
    meta: dict[str, str | int | None]
    corpo: str


def _valor(texto: str) -> str | int | None:
    if texto.startswith('"'):
        return json.loads(texto)
    if texto in ("", "null"):
        return None
    return int(texto) if texto.isdigit() else texto


def _texto(valor: str | int | None) -> str:
    if valor is None:
        return "null"
    if isinstance(valor, int):
        return str(valor)
    return json.dumps(valor, ensure_ascii=False) if (valor == "" or _AMBIGUO.search(valor)) else valor


def analisar_md(texto: str) -> DocumentoMd:
    if not texto.startswith(_DELIMITADOR + "\n"):
        return DocumentoMd({}, texto)
    fim = texto.find("\n" + _DELIMITADOR + "\n", len(_DELIMITADOR))
    if fim < 0:
        return DocumentoMd({}, texto)
    meta = {}
    for linha in texto[len(_DELIMITADOR) + 1:fim].split("\n"):
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            meta[chave.strip()] = _valor(valor.strip())
    return DocumentoMd(meta, texto[fim + len(_DELIMITADOR) + 2:])


def serializar_md(doc: DocumentoMd) -> str:
    if not doc.meta:
        return doc.corpo
    linhas = [f"{chave}: {_texto(valor)}" for chave, valor in doc.meta.items()]
    return "\n".join([_DELIMITADOR, *linhas, _DELIMITADOR, ""]) + doc.corpo


def ler_md(caminho: Path) -> DocumentoMd:
    return analisar_md(caminho.read_text(encoding="utf-8"))


def escrever_md(op: Operacao, caminho_rel: str, doc: DocumentoMd) -> None:
    alvo = versionar_arquivo(op, caminho_rel)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(serializar_md(doc), encoding="utf-8", newline="\n")


def apagar_md(op: Operacao, caminho_rel: str) -> None:
    alvo = versionar_arquivo(op, caminho_rel)
    alvo.unlink(missing_ok=True)
