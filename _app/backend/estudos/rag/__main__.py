"""`python -m estudos.rag "<pasta da matéria>"` — sincroniza o índice de busca e mostra o resumo.

Saída: 0 se sincronizou, 2 se a pasta não é uma matéria.
"""

import argparse
import sys
from contextlib import closing
from pathlib import Path

from estudos.db.conexao import aplicar_migracoes, conectar
from estudos.rag.indexador import sincronizar
from estudos.workspace import ARQUIVO_DB


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="estudos.rag", description="Sincroniza o índice de busca de uma matéria.")
    parser.add_argument("pasta", type=Path, help="pasta da matéria (contém materia.db)")
    args = parser.parse_args(argv)
    if not (args.pasta / ARQUIVO_DB).is_file():
        print(f"{args.pasta} não é uma matéria (falta {ARQUIVO_DB}).", file=sys.stderr)
        return 2
    with closing(conectar(args.pasta / ARQUIVO_DB)) as con:
        aplicar_migracoes(con)
        r = sincronizar(con, args.pasta)
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{r.indexadas} origem(ns) indexada(s), {r.removidas} removida(s), {r.trechos} trechos no índice, {r.tempo_ms} ms")
    for aviso in r.avisos:
        print(f"  aviso: {aviso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
