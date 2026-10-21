import json
import shutil
from pathlib import Path

import pytest

from estudos.migracao.legado import LegadoInvalido, carregar

FIXTURE = Path(__file__).parent / "fixtures" / "legado_minimo"


def test_carregar_fixture():
    legado = carregar(FIXTURE)
    assert [s.sec for s in legado.secoes] == ["14.1", "15.4", "L5"]
    assert len(legado.marcacoes) == 4
    item = legado.secoes[0].itens[0]
    assert (item.numero, item.figura, item.linha) == ("22", "ex22", 1)
    assert [i.linha for i in legado.secoes[0].itens] == [1, 1, 2, 2]
    assert legado.secoes[1].locked is True and legado.secoes[2].pdf == "disciplina/listas/Lista5.pdf"
    assert [p.name for p in legado.resumos] == ["00-polares.md", "01-funcoes.md", "02-solto.md"]
    assert len(legado.resolucoes) == 2 and len(legado.figuras) == 1
    assert sorted(p.as_posix() for p in legado.pdfs) == [
        "disciplina/Programa.pdf", "disciplina/listas/Lista5.pdf",
        "livros/extra.pdf", "livros/guidorizzi.pdf", "livros/stewart.pdf",
    ]


def test_curso_sem_unidades(tmp_path):
    destino = tmp_path / "leg"
    shutil.copytree(FIXTURE, destino)
    caminho = destino / "_app/dados/curso.json"
    curso = json.loads(caminho.read_text(encoding="utf-8"))
    del curso["unidades"]
    caminho.write_text(json.dumps(curso), encoding="utf-8")
    with pytest.raises(LegadoInvalido, match="unidades"):
        carregar(destino)


def test_json_invalido(tmp_path):
    destino = tmp_path / "leg"
    shutil.copytree(FIXTURE, destino)
    (destino / "status.json").write_text("{ruim", encoding="utf-8")
    with pytest.raises(LegadoInvalido, match="status.json"):
        carregar(destino)
