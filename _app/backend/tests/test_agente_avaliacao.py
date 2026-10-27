import pytest

from estudos.avaliacao.contexto import cobertura_do_contexto
from estudos.avaliacao.gabarito import PerguntaBusca
from test_agente_contexto import questao_do_livro  # noqa: F401 (fixture)


def test_cobertura_do_contexto(con, materia, questao_do_livro):
    perguntas = [
        PerguntaBusca("Calcule a integral tripla em casa.", "questao", ("secao:1.2",), None),          # no contexto
        PerguntaBusca("Calcule a integral tripla em casa. | por que muda a ordem?", "duvida", ("secao:9.9",), None),
        PerguntaBusca("Enunciado que não está em nenhuma lista", "questao", ("secao:1.2",), None),     # fora da conta
        PerguntaBusca("coordenadas polares", "exata", ("secao:1.1",), None),                           # não é de questão
    ]
    linha = cobertura_do_contexto(con, materia.pasta, perguntas)
    assert (linha.total, linha.achadas) == (2, 1)
    assert linha.por_estilo == {"questao": 1.0, "duvida": 0.0}


def test_contexto_marca_de_onde_veio_cada_pedaco(con, materia, questao_do_livro):
    from estudos.agente.contexto import montar_contexto
    pedacos = montar_contexto(con, materia.pasta, f"questao:{questao_do_livro}", "tutor")
    do_livro = [p for p in pedacos if p.fonte_id is not None]
    assert do_livro and all(p.pagina for p in do_livro) and any(p.secao_codigo == "1.2" for p in do_livro)
    assert any(p.documento_id is not None for p in pedacos)   # o resumo ligado à seção


@pytest.mark.gemini
def test_gemini_real():
    from pathlib import Path

    from estudos.agente.modelo import Gemini, Texto, Turno, Uso
    from estudos.agente.segredos import ler_chave
    from estudos.config import carregar_settings

    app_dir = Path(__file__).resolve().parents[2]
    chave = ler_chave(app_dir)
    if not chave:
        pytest.skip("sem chave do Gemini em _app/.segredos.toml")
    settings = carregar_settings(app_dir)
    eventos = list(Gemini(chave, settings.agente_modelo, 60).responder("Responda com uma palavra.", [Turno("usuario", "Diga oi.")], []))
    assert any(isinstance(e, Texto) and e.texto.strip() for e in eventos) and any(isinstance(e, Uso) for e in eventos)
