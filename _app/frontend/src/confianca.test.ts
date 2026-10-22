import { expect, test } from 'vitest'
import { corDoSelo, explicarUnidadeLista } from './confianca'
import type { PropostaListaItem } from './api/proposta'

test.each([
  [{ confianca: 0.82, revisar: false }, 'certo'],
  [{ confianca: 0.3, revisar: true }, 'revisar'],
  [{ numero: null, confianca: 0, revisar: true }, 'sem-palpite'],
  [{ fonte_id: null, confianca: 0, revisar: false }, 'sem-palpite'],
])('selo %j', (item, cor) => {
  expect(corDoSelo(item)).toBe(cor)
})

function itemLista(extra: Partial<PropostaListaItem>): PropostaListaItem {
  return {
    codigo: 'L1', titulo: 'Primeira Lista', secao_livro: null, questoes: [], revisar: false, secao_id: null,
    unidade: { numero: 1, confianca: 0.3, revisar: true }, topicos: [], existente: null, ...extra,
  }
}

test('por quê da unidade cita os tópicos', () => {
  const item = itemLista({
    topicos: [
      { topico_id: 1, titulo: 'Limite', unidade: 1, confianca: 0.5, aceito: true, revisar: true },
      { topico_id: 2, titulo: 'Continuidade', unidade: 1, confianca: 0.5, aceito: true, revisar: true },
    ],
  })
  const texto = explicarUnidadeLista(item)
  expect(texto).toMatch(/Unidade 1 com confiança 0,30/)
  expect(texto).toMatch(/Limite.*Continuidade/)
})

test('por quê de unidade escolhida à mão e de unidade sem palpite', () => {
  expect(explicarUnidadeLista(itemLista({ unidade: { numero: 3, confianca: 1, revisar: false, manual: true } }))).toMatch(/você escolheu/)
  expect(explicarUnidadeLista(itemLista({ unidade: { numero: null, confianca: 0, revisar: true } }))).toMatch(/escolha a unidade/i)
})
