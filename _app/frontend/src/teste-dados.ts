// Fábricas de dados para os testes de componentes (formato igual ao do motor).
import type { ListaComQuestoes, Painel, Placar, Questao, Topico, Unidade } from './api/tipos'

export const placarVazio: Placar = {
  ok: 0, err: 0, dub: 0, total: 0, feitos_linha1: 0, total_linha1: 0, feitos_linha2: 0, total_linha2: 0,
  taxa_acerto: null,
}

export function unidade(numero: number, extra: Partial<Unidade> = {}): Unidade {
  return { id: numero, numero, titulo: `${numero}ª Unidade`, origem: 'importado', confianca: null, data_prova: null, ...extra }
}

export function topico(id: number, status: string, extra: Partial<Topico> = {}): Topico {
  return { id, unidade_id: 1, pai_id: null, ordem: id, titulo: `Tópico ${id}`, status, origem: 'importado', detalhe_md: '', ...extra }
}

export function questao(id: number, rotulo: string, extra: Partial<Questao> = {}): Questao {
  return { id, lista_id: 1, rotulo, ordem: id, linha: 1, enunciado_md: '', expressao: null, pagina_pdf: null, figura: null, ...extra }
}

export function lista(id: number, codigo: string, questoes: Questao[], extra: Partial<ListaComQuestoes> = {}): ListaComQuestoes {
  return {
    id, codigo, titulo: `Lista ${codigo}`, unidade_id: 1, fonte_id: null, liberacao: 'auto', ordem: id, origem: 'importado',
    aberta: true, questoes, ...extra,
  }
}

export function painel(extra: Partial<Painel> = {}): Painel {
  return {
    materia: { id: 1, uid: 'ab', nome: 'Cálculo 2', periodo: '2026.2', instituicao: null, professor: null, email_professor: null },
    unidades: [unidade(1), unidade(2)], unidade_atual: 1, unidade: 1,
    topicos: [], listas: [], marcacoes: {}, sessoes: [], formulas: [], documentos: [], placar: placarVazio,
    eventos: [], vinculos: { topicos: {}, listas: {} }, importacoes_pendentes: 0,
    ...extra,
  }
}

export const painelVazio: Painel = painel({ unidades: [], unidade_atual: null, unidade: null, placar: null })
