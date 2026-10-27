"""`python -m estudos.avaliacao busca|vinculos --materia "Calculo 2"` — mede contra o gabarito e imprime a tabela.

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
from estudos.avaliacao.gabarito import ler_busca, ler_relacionados, ler_vinculos
from estudos.avaliacao.gerar import perguntas_das_questoes
from estudos.avaliacao.relatorio import gravar, slug as _slug, tabela_busca, tabela_vinculos
from estudos.avaliacao.vinculos import ConfigVinculo, avaliar as avaliar_vinculos
from estudos.config import carregar_settings
from estudos.ia.embeddings import obter_embeddings
from estudos.importacao.vinculo import Semantica
from types import SimpleNamespace
from estudos.db.conexao import conectar
from estudos.workspace import ARQUIVO_DB

APP_DIR = Path(__file__).resolve().parents[3]          # _app/
WORKSPACE = APP_DIR.parent
GABARITOS = Path(__file__).resolve().parent / "gabaritos"
SMALL, BASE = "intfloat/multilingual-e5-small", "intfloat/multilingual-e5-base"
CONFIGS_BUSCA = {
    "texto": Configuracao("texto", "texto", None),
    "vetor:small": Configuracao("vetor:small", "vetor", SMALL),
    "vetor:base": Configuracao("vetor:base", "vetor", BASE),
    "hibrida:small": Configuracao("hibrida:small", "hibrida", SMALL),
    "hibrida:base": Configuracao("hibrida:base", "hibrida", BASE),
}
MODELOS = {"small": SMALL, "base": BASE}


def _config_vinculo(nome: str) -> ConfigVinculo:
    """"regra" ou "sentido:<small|base>@<peso>" (ex.: sentido:small@0.5); o modelo só é carregado quando pedido."""
    if nome == "regra":
        return ConfigVinculo("regra")
    tipo, _, resto = nome.partition(":")
    modelo, _, peso = resto.partition("@")
    if tipo != "sentido" or modelo not in MODELOS:
        raise KeyError(nome)
    e = obter_embeddings(SimpleNamespace(embeddings=True, modelo=MODELOS[modelo], app_dir=APP_DIR))
    if e is None:
        raise KeyError(f"{nome} (modelo indisponível)")
    return ConfigVinculo(nome, Semantica(e), float(peso or 0.5))


def _arquivo_gabarito(materia: str, tipo: str) -> Path:
    return GABARITOS / f"{_slug(materia)}_{tipo}.toml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="estudos.avaliacao", description="Avalia a busca ou os vínculos de uma matéria contra o gabarito.")
    parser.add_argument("tipo", choices=["busca", "vinculos"])
    parser.add_argument("--materia", required=True, help="nome da pasta da matéria (ex.: \"Calculo 2\")")
    parser.add_argument("--gabarito", type=Path, help="arquivo TOML (padrão: gabaritos/<matéria>_<tipo>.toml)")
    parser.add_argument("--configs", default=None, help="separadas por vírgula (busca: texto…; vínculos: regra…)")
    parser.add_argument("--gravar", action="store_true", help="grava a tabela em docs/avaliacoes/")
    parser.add_argument("--geradas", action="store_true",
                        help="busca: acrescenta perguntas geradas dos enunciados das questões (resposta = seção da lista)")
    parser.add_argument("--limite-teoria", type=int, default=None,
                        help="busca: caracteres por trecho de teoria no índice temporário (padrão: o do código)")
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
    padrao = "texto" if args.tipo == "busca" else "regra"
    try:
        nomes = [n.strip() for n in (args.configs or padrao).split(",") if n.strip()]
        configs = [CONFIGS_BUSCA[n] for n in nomes] if args.tipo == "busca" else [_config_vinculo(n) for n in nomes]
    except KeyError as e:
        print(f"configuração desconhecida: {e}", file=sys.stderr)
        return 2
    if args.tipo == "vinculos":
        return _vinculos(args, pasta, arquivo, configs)
    perguntas = ler_busca(arquivo)
    relacionados = ler_relacionados(arquivo)
    with closing(conectar(pasta / ARQUIVO_DB)) as con, tempfile.TemporaryDirectory() as temp:
        if args.geradas:
            perguntas += perguntas_das_questoes(con)
        linhas = avaliar(con, pasta, perguntas, configs, Path(temp), relacionados=relacionados,
                         limite_teoria=args.limite_teoria)
    tabela = tabela_busca(linhas)
    print(f"{len(perguntas)} perguntas · {arquivo.name}\n\n{tabela}")
    if args.gravar:
        texto = f"# Avaliação da busca — {args.materia}\n\nGabarito: `{arquivo.name}` ({len(perguntas)} perguntas)\n\n{tabela}"
        print(f"gravado em {gravar(texto, WORKSPACE / 'docs' / 'avaliacoes', args.tipo, datetime.date.today(), materia=args.materia)}")
    return 0


def _vinculos(args, pasta: Path, arquivo: Path, configs) -> int:
    settings = carregar_settings(APP_DIR)
    gabarito = ler_vinculos(arquivo)
    with closing(conectar(pasta / ARQUIVO_DB)) as con:
        linhas = avaliar_vinculos(con, gabarito, configs, settings.limiar_vinculo, settings.limiar_confianca)
    tabela = tabela_vinculos(linhas)
    total = len(gabarito.topicos) + len(gabarito.listas) + len(gabarito.documentos)
    print(f"{total} itens · {arquivo.name} · limiares {settings.limiar_vinculo} / {settings.limiar_confianca}\n\n{tabela}")
    if args.gravar:
        texto = f"# Avaliação dos vínculos — {args.materia}\n\nGabarito: `{arquivo.name}` ({total} itens)\n\n{tabela}"
        print(f"gravado em {gravar(texto, WORKSPACE / 'docs' / 'avaliacoes', args.tipo, datetime.date.today(), materia=args.materia)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
