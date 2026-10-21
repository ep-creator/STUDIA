import datetime
import hashlib
import sqlite3
from pathlib import Path

from estudos.erros import DadoInvalido
from estudos.historico import Operacao
from estudos.modelos import ORIGENS, TIPOS_FONTE, Fonte, exigir_opcao
from estudos.repos import _base
from estudos.seguranca import caminho_seguro

_BLOCO = 1024 * 1024


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        while bloco := arquivo.read(_BLOCO):
            h.update(bloco)
    return h.hexdigest()


def registrar(
    op: Operacao,
    tipo: str,
    caminho_rel: str,
    titulo: str = "",
    paginas: int | None = None,
    origem: str = "manual",
) -> int:
    """Registra um arquivo já presente em `fontes/`. O sha256 impede cadastrar o mesmo arquivo duas vezes."""
    exigir_opcao(tipo, TIPOS_FONTE, "tipo de fonte")
    exigir_opcao(origem, ORIGENS, "origem")
    if op.raiz is None:
        raise DadoInvalido("Registrar fonte exige a pasta da matéria.")
    sha = sha256_arquivo(caminho_seguro(op.raiz, caminho_rel))
    existente = op.con.execute("SELECT caminho FROM fonte WHERE sha256 = ?", (sha,)).fetchone()
    if existente:
        raise DadoInvalido(f"Este arquivo já está cadastrado como {existente['caminho']}.")
    return _base.inserir(op, "fonte", {
        "tipo": tipo, "caminho": caminho_rel, "sha256": sha, "titulo": titulo, "paginas": paginas,
        "importada_em": datetime.datetime.now().isoformat(timespec="seconds"), "origem": origem,
    })


def obter_por_caminho(con: sqlite3.Connection, caminho_rel: str) -> Fonte | None:
    linha = con.execute("SELECT * FROM fonte WHERE caminho = ?", (caminho_rel,)).fetchone()
    return Fonte(**dict(linha)) if linha else None


def listar(con: sqlite3.Connection, tipo: str | None = None) -> list[Fonte]:
    if tipo is None:
        linhas = con.execute("SELECT * FROM fonte ORDER BY caminho")
    else:
        linhas = con.execute("SELECT * FROM fonte WHERE tipo = ? ORDER BY caminho", (tipo,))
    return [Fonte(**dict(l)) for l in linhas]
