import pytest

from estudos.db.conexao import conectar
from estudos.historico import operacao
from estudos.rag.indexador import sincronizar
from estudos.rag.indice import abrir_indice
from estudos.repos import documentos, fontes, listas, livros, topicos, unidades
from estudos.workspace import criar_materia
from pdfs_sinteticos import criar_pdf
from test_rag_indexador import PAGINAS_LIVRO


@pytest.fixture
def materia(tmp_path):
    return criar_materia(tmp_path, "Matéria Teste")


@pytest.fixture
def con(materia):
    conexao = conectar(materia.db)
    yield conexao
    conexao.close()


# Matéria com um livro (seções 1.1 polares e 1.2 triplas), uma lista e dois documentos, já indexada.
# Usada pelos testes da busca e da avaliação.
@pytest.fixture
def cenario_busca(con, materia):
    criar_pdf(materia.pasta / "fontes/livros/livro.pdf", PAGINAS_LIVRO)
    criar_pdf(materia.pasta / "fontes/listas/lista.pdf", ["Lista 5\n1. Calcule a integral dupla em polares.", "2. Área da cardioide."])
    with operacao(con, "base", materia.pasta) as op:
        u1, u3 = unidades.criar(op, 1), unidades.criar(op, 3)
        livro = fontes.registrar(op, "livro", "fontes/livros/livro.pdf")
        livros.criar(op, livro, "principal", gabarito_pdf_ini=7, gabarito_pdf_fim=8)
        s11 = livros.criar_secao(op, livro, "1.1", "Coordenadas polares", 2, 3)
        s12 = livros.criar_secao(op, livro, "1.2", "Integrais triplas", 4, 6)
        t3 = topicos.criar(op, u3, "Integrais triplas em coordenadas cilíndricas")
        livros.vincular_topico(op, t3, s12, confianca=1.0, confirmado=True)
        fl = fontes.registrar(op, "lista", "fontes/listas/lista.pdf")
        listas.criar(op, "L5", "Lista 5", u3, fonte_id=fl)
        documentos.salvar(op, "resumo", "polares", "Polares", "# Polares\n\nCoordenadas polares e cardioides.", unidade_id=u1)
        documentos.salvar(op, "anotacao", "geral", "Geral", "Integrais em geral.")
    sincronizar(con, materia.pasta)
    indice = abrir_indice(materia.pasta)
    yield {"indice": indice, "s11": s11, "s12": s12, "t3": t3, "u1": u1}
    indice.close()
