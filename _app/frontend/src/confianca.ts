// Selos e explicações da confiança das propostas. O motor já decide o que pede revisão (`revisar`, a partir do
// limiar_confianca do config.toml); aqui só se traduz isso para cor e texto.
import type { PropostaListaItem } from './api/proposta'

export type CorSelo = 'certo' | 'revisar' | 'sem-palpite'

export function corDoSelo(item: { confianca?: number; revisar?: boolean; numero?: number | null; fonte_id?: number | null }): CorSelo {
  if (('numero' in item && item.numero == null) || ('fonte_id' in item && item.fonte_id == null)) return 'sem-palpite'
  return item.revisar ? 'revisar' : 'certo'
}

export function numeroPt(n: number): string {
  return n.toFixed(2).replace('.', ',')
}

function juntar(nomes: string[]): string {
  return nomes.length <= 1 ? (nomes[0] ?? '') : `${nomes.slice(0, -1).join(', ')} e ${nomes.at(-1)}`
}

/** O "por quê?" da unidade de uma lista: de onde veio o palpite e quanto ele vale. */
export function explicarUnidadeLista(item: PropostaListaItem): string {
  const { numero, confianca, manual } = item.unidade
  if (numero == null) return 'Nenhum conteúdo da lista se parece com os tópicos do programa: escolha a unidade.'
  if (manual) return `Unidade ${numero}: você escolheu na revisão.`
  const aqui = item.topicos.filter((t) => t.unidade === numero).map((t) => t.titulo)
  const base = `Unidade ${numero} com confiança ${numeroPt(confianca)}`
  if (aqui.length === 0) return `${base}: a unidade vem do título do arquivo ou da seção do livro.`
  const verbo = aqui.length === 1 ? 'aponta' : 'apontam'
  const aviso = item.unidade.revisar ? ' As evidências estão divididas ou fracas; confira.' : ''
  return `${base}: ${juntar(aqui)} ${verbo} para a unidade ${numero}.${aviso}`
}
