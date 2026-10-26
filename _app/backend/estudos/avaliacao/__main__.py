"""`python -m estudos.avaliacao busca --materia "Calculo 2"` — mede a busca contra o gabarito e imprime a tabela.

A matéria só é lida: cada configuração usa um índice temporário. Com --gravar, a tabela vai para docs/avaliacoes/.
Saída: 0 se avaliou, 2 se a matéria ou o gabarito não existem.
"""

import argparse
import datetime
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from estudos.avaliacao.busca import Configuracao, avaliar
from estudos.avaliacao.gabarito import ler_busca
from estudos.avaliacao.relatorio import gravar, tabela_busca
from estudos.db.conexao import conectar
from estudos.workspace import ARQUIVO_DB

APP_DIR = Path(__file__).resolve().parents[3]          # _app/
WORKSPACE = APP_DIR.parent
GABARITOS = Path(__file__).resolve().parent / "gabaritos"
CONFIGS_BUSCA = {"texto": Configuracao("texto", "texto", None)}


def _arquivo_gabarito(materia: str, tipo: str) -> Path:
    nome = "".join(c for c in materia.lower().replace(" ", "") if c.isalnum())
    return GABARITOS / f"{nome}_{tipo}.toml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="estudos.avaliacao", description="Avalia a busca de uma matéria contra o gabarito.")
    parser.add_argument("tipo", choices=["busca"])
    parser.add_argument("--materia", required=True, help="nome da pasta da matéria (ex.: \"Calculo 2\")")
    parser.add_argument("--gabarito", type=Path, help="arquivo TOML (padrão: gabaritos/<matéria>_<tipo>.toml)")
    parser.add_argument("--configs", default="texto", help=f"separadas por vírgula: {', '.join(CONFIGS_BUSCA)}")
    parser.add_argument("--gravar", action="store_true", help="grava a tabela em docs/avaliacoes/")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    pasta = WORKSPACE / args.materia
    if not (pasta / ARQUIVO_DB).is_file():
        print(f"{pasta} não é uma matéria (falta {ARQUIVO_DB}).", file=sys.stderr)
        return 2
    arquivo = args.gabarito or _arquivo_gabarito(args.materia, args.tipo)
    if not arquivo.is_file():
        print(f"gabarito não encontrado: {arquivo}", file=sys.stderr)
        return 2
    try:
        configs = [CONFIGS_BUSCA[n.strip()] for n in args.configs.split(",") if n.strip()]
    except KeyError as e:
        print(f"configuração desconhecida: {e}", file=sys.stderr)
        return 2
    perguntas = ler_busca(arquivo)
    with closing(conectar(pasta / ARQUIVO_DB)) as con, tempfile.TemporaryDirectory() as temp:
        linhas = avaliar(con, pasta, perguntas, configs, Path(temp))
    tabela = tabela_busca(linhas)
    print(f"{len(perguntas)} perguntas · {arquivo.name}\n\n{tabela}")
    if args.gravar:
        texto = f"# Avaliação da busca — {args.materia}\n\nGabarito: `{arquivo.name}` ({len(perguntas)} perguntas)\n\n{tabela}"
        print(f"gravado em {gravar(texto, WORKSPACE / 'docs' / 'avaliacoes', args.tipo, datetime.date.today())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
