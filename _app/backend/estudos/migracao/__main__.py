"""`python -m estudos.migracao "<pasta legada>" [--destino <pasta>] [--forcar]`

Saída: 0 se as contagens batem, 1 se não batem, 2 se a migração foi recusada ou o legado é inválido.
"""

import argparse
import sys
from pathlib import Path

from estudos.migracao.executar import MigracaoRecusada, migrar
from estudos.migracao.legado import LegadoInvalido


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="estudos.migracao", description="Migra uma matéria do app legado para o motor novo.")
    parser.add_argument("origem", type=Path, help="pasta da matéria no formato legado (ex.: 'Calculo 2')")
    parser.add_argument("--destino", type=Path, help="pasta da matéria nova (padrão: a mesma da origem)")
    parser.add_argument("--forcar", action="store_true", help="reconstrói mesmo se o app novo já tiver ações registradas")
    args = parser.parse_args(argv)

    try:
        relatorio = migrar(args.origem, args.destino or args.origem, forcar=args.forcar)
    except (MigracaoRecusada, LegadoInvalido) as e:
        print(f"Migração não executada: {e}", file=sys.stderr)
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    print(relatorio.markdown())
    return 0 if relatorio.bate() else 1


if __name__ == "__main__":
    sys.exit(main())
