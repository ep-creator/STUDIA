"""`python -m estudos.avaliacao.amostras <pdf> <página> <saída.json> [--imagem saída.png]` — salva os pedaços de texto
de uma página (fonte, tamanho, caixa, texto) e as tabelas de tradução dela para os testes da leitura limpa rodarem sem o PDF.

O PDF só é lido. A imagem opcional serve para conferir à mão o texto esperado da amostra.
"""

import argparse
import json
from pathlib import Path

import pymupdf

from estudos.importacao.pdf import traducoes_da_pagina


def spans_da_pagina(pagina: pymupdf.Page) -> list[dict]:
    return [
        {"font": s["font"], "size": round(s["size"], 2), "bbox": [round(v, 2) for v in s["bbox"]], "text": s["text"]}
        for bloco in pagina.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"] for linha in bloco.get("lines", []) for s in linha["spans"]
        if s["text"].strip()
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="estudos.avaliacao.amostras")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("pagina", type=int, help="número da página no PDF (1 = primeira)")
    parser.add_argument("saida", type=Path)
    parser.add_argument("--imagem", type=Path, help="grava também a página renderizada (PNG)")
    args = parser.parse_args(argv)
    with pymupdf.open(stream=args.pdf.read_bytes(), filetype="pdf") as doc:
        pagina = doc[args.pagina - 1]
        dados = {"largura": round(pagina.rect.width, 2), "altura": round(pagina.rect.height, 2), "spans": spans_da_pagina(pagina),
                 "tabelas": traducoes_da_pagina(doc, pagina)}  # inclui as que saem dos nomes dos glifos desta página
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(json.dumps(dados, ensure_ascii=False, indent=0), encoding="utf-8")
        if args.imagem:
            pagina.get_pixmap(dpi=110).save(args.imagem)
    print(f"{args.saida}: {len(dados['spans'])} pedaços")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
