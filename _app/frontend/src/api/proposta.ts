// Tipos das propostas de importação, por tipo de arquivo. O motor guarda a proposta como JSON livre
// (estudos/importacao/pipeline.py); estes tipos descrevem o que ele monta hoje.

export type Classificacao = { tipo: string; confianca: number; sinais: Record<string, number>; revisar: boolean }

/** Vínculo que o usuário pode aceitar ou recusar; `manual` marca o que ele incluiu ou escolheu na revisão. */
type Vinculavel = { confianca: number; aceito: boolean; revisar: boolean; manual?: boolean }

export type SecaoProposta = Vinculavel & { secao_id: number; codigo: string; livro: string }
export type TopicoProposto = { titulo: string; existente_id: number | null; secoes: SecaoProposta[]; filhos: TopicoProposto[] }
export type PropostaPrograma = {
  classificacao: Classificacao
  unidades: { numero: number; titulo: string; existente_id: number | null; topicos: TopicoProposto[] }[]
  revisar: boolean
}

export type EventoProposto = {
  tipo: string; data: string; hora_inicio: string | null; hora_fim: string | null; descricao: string; revisar: boolean
}
export type PropostaCalendario = {
  classificacao: Classificacao
  ano: number | null
  unidades: { numero: number; aulas: EventoProposto[]; prova: EventoProposto | null }[]
  eventos: EventoProposto[]
  revisar: boolean
}

export type ReferenciaProposta = { texto: string; papel: string; fonte_id: number | null; confianca: number; revisar: boolean; manual?: boolean }
export type PropostaTurma = {
  classificacao: Classificacao
  professor: string | null
  email: string | null
  horarios: [number, string, string][]
  referencias: ReferenciaProposta[]
  criterios: string[]
  revisar: boolean
}

export type SecaoLivroProposta = {
  codigo: string; titulo: string; nivel: number; pagina_pdf_ini: number; pagina_pdf_fim: number; confianca: number; revisar: boolean
}
export type PropostaLivro = {
  classificacao: Classificacao
  titulo_obra: string
  offset_pagina: number | null
  gabarito: [number, number] | null
  origem: string
  sem_texto: boolean
  avisos: string[]
  secoes: SecaoLivroProposta[]
  papel: 'principal' | 'complementar'
  papel_manual?: boolean
  equivalencias: (Vinculavel & { codigo: string; equivalente_id: number; equivalente_codigo: string })[]
  topicos: (Vinculavel & { topico_id: number; titulo: string; unidade: number; codigo: string })[]
  revisar: boolean
}

export type TopicoDaLista = Vinculavel & { topico_id: number; titulo: string; unidade: number }
export type PropostaListaItem = {
  codigo: string
  titulo: string
  secao_livro: string | null
  questoes: { rotulo: string; linha: number; enunciado_md: string; pagina_pdf: number | null }[]
  revisar: boolean
  secao_id: number | null
  secao_manual?: boolean
  unidade: { numero: number | null; confianca: number; revisar: boolean; manual?: boolean }
  topicos: TopicoDaLista[]
  existente: { lista_id: number; novas: string[]; mantidas: string[]; ausentes: string[] } | null
}
export type PropostaLista = {
  classificacao: Classificacao
  formato: 'numerada' | 'por_secao'
  modo: 'mesclar' | 'substituir'
  titulo: string
  unidade: { numero: number | null; confianca: number }
  referencia_livro: string | null
  conteudos: string[]
  avisos: string[]
  listas: PropostaListaItem[]
  revisar: boolean
}

export type PropostaOutro = { classificacao: Classificacao; observacao: string }

export const TIPOS_ARQUIVO = ['programa', 'calendario', 'turma', 'livro', 'lista', 'slides', 'prova', 'anotacao', 'outro'] as const
export const NOME_TIPO: Record<string, string> = {
  programa: 'Programa', calendario: 'Calendário', turma: 'Informações da turma', livro: 'Livro', lista: 'Lista',
  slides: 'Slides', prova: 'Prova', anotacao: 'Anotação', outro: 'Outro',
}

/**
 * A leitura não achou nada do que o tipo promete (ex.: calendário sem nenhuma data)? Devolve a frase que diz isso, para
 * a tela não oferecer "Confirmar" como se tivesse dado certo; null quando há o que gravar.
 */
export function propostaVazia(tipo: string, proposta: unknown): string | null {
  const p = proposta as Record<string, unknown>
  if (tipo === 'calendario') {
    const c = p as unknown as PropostaCalendario
    const temData = c.eventos?.length || c.unidades?.some((u) => u.aulas.length || u.prova)
    return temData ? null : 'Não achei datas de aula nem de prova neste calendário.'
  }
  if (tipo === 'programa') {
    const pr = p as unknown as PropostaPrograma
    return pr.unidades?.some((u) => u.topicos.length) ? null : 'Não achei unidades nem tópicos neste programa.'
  }
  if (tipo === 'lista') {
    const l = p as unknown as PropostaLista
    return l.listas?.some((x) => x.questoes.length) ? null : 'Não achei questões nesta lista.'
  }
  if (tipo === 'livro') {
    const lv = p as unknown as PropostaLivro
    if (lv.secoes?.length) return null
    return lv.sem_texto ? 'Este PDF não tem texto (parece ser imagem), então não deu para ler o sumário.' : 'Não achei o sumário deste livro.'
  }
  if (tipo === 'turma') {
    const t = p as unknown as PropostaTurma
    const algo = t.professor || t.email || t.horarios?.length || t.referencias?.length || t.criterios?.length
    return algo ? null : 'Não achei informações da turma neste arquivo.'
  }
  return null
}
