from estudos.avaliacao.gerar import perguntas_das_questoes
from estudos.historico import operacao
from estudos.modelos import QuestaoEntrada
from estudos.repos import listas, unidades


def test_questoes_viram_perguntas_com_a_secao_da_lista(con, materia, cenario_busca):
    with operacao(con, "lista", materia.pasta) as op:
        u = unidades.criar(op, 2)
        lista = listas.criar(op, "1.2", "Integrais triplas", u)
        listas.vincular_secao(op, lista, cenario_busca["s12"])
        listas.sincronizar_questoes(op, lista, [
            QuestaoEntrada("1", enunciado_md="Calcule a **integral tripla** sobre o sólido limitado pelos planos."),
            QuestaoEntrada("2", enunciado_md="Calcule a integral tripla sobre o sólido limitado pelos planos."),  # repetida
            QuestaoEntrada("3", enunciado_md="Esboce."),                                                          # curta demais
            QuestaoEntrada("4", enunciado_md=""),
        ])
        sem_secao = listas.criar(op, "X", "Lista sem seção", u)
        listas.sincronizar_questoes(op, sem_secao, [QuestaoEntrada("1", enunciado_md="Determine a equação do plano tangente.")])
    perguntas = perguntas_das_questoes(con)
    assert [(p.texto, p.aceitas, p.estilo, p.origem) for p in perguntas] == [
        ("Calcule a integral tripla sobre o sólido limitado pelos planos.", ("secao:1.2",), "questao", "gerada"),
    ]
