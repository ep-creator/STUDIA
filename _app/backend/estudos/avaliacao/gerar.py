"""Perguntas geradas do próprio banco, sem escrever nada à mão: o caso de uso da IA ("o aluno está nesta questão; que
trecho do livro ajuda?"). A pergunta é o enunciado da questão (sem negrito/markdown) e a resposta aceita é a seção do
livro ligada à lista. Questões de listas sem seção ficam de fora (não há resposta conhecida para aceitar), assim como
enunciados curtos demais ("Esboce.") e repetidos.
"""

import re
import sqlite3

from estudos.avaliacao.gabarito import PerguntaBusca
from estudos.importacao.idioma import radicais_relevantes

_MIN_PALAVRAS = 3
_MARCAS = re.compile(r"[*_`#>]+")


def _limpar(enunciado: str) -> str:
    return re.sub(r"\s+", " ", _MARCAS.sub("", enunciado or "")).strip()


def perguntas_das_questoes(con: sqlite3.Connection) -> list[PerguntaBusca]:
    linhas = con.execute(
        """SELECT q.enunciado_md, group_concat(DISTINCT s.codigo) AS codigos
           FROM questao q JOIN lista l ON l.id = q.lista_id
           JOIN lista_secao ls ON ls.lista_id = l.id JOIN secao_livro s ON s.id = ls.secao_id
           GROUP BY q.id ORDER BY l.ordem, l.id, q.ordem"""
    ).fetchall()
    perguntas, vistas = [], set()
    for linha in linhas:
        texto = _limpar(linha["enunciado_md"])
        aceitas = tuple(f"secao:{c}" for c in sorted(linha["codigos"].split(",")))
        if len(radicais_relevantes(texto)) < _MIN_PALAVRAS or (texto.lower(), aceitas) in vistas:
            continue
        vistas.add((texto.lower(), aceitas))
        perguntas.append(PerguntaBusca(texto, "questao", aceitas, None, "gerada"))
    return perguntas
