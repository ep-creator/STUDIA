import { expect, test } from 'vitest'
import { diasAte, nomeUnidade, ordinal, rotuloStatus, textoContagem } from './apresentacao'

test('ordinal e unidade', () => {
  expect(ordinal(1)).toBe('1ª')
  expect(nomeUnidade(3)).toBe('3ª unidade')
})

test.each([
  ['2026-10-22', 'hoje'],
  ['2026-10-23', 'amanhã'],
  ['2026-11-03', '12 dias'],
])('contagem %s', (data, texto) => {
  expect(textoContagem({ data, hora_inicio: null }, new Date(2026, 9, 22, 15, 0))).toBe(texto)
})

test('prova que já passou e sem prova', () => {
  expect(textoContagem({ data: '2026-10-01', hora_inicio: null }, new Date(2026, 9, 22))).toBe('prova já passou')
  expect(textoContagem(null, new Date())).toBe('sem data de prova')
})

test('diasAte ignora a hora do dia', () => {
  expect(diasAte('2026-10-23', new Date(2026, 9, 22, 23, 59))).toBe(1)
})

test('rótulos dos status do banco', () => {
  expect(['pendente', 'proxima', 'visto'].map(rotuloStatus)).toEqual(['pendente', 'próxima', 'visto'])
})

test('texto da prova no topo', async () => {
  const { textoTopoProva } = await import('./apresentacao')
  const hoje = new Date(2026, 9, 22)
  expect(textoTopoProva({ data: '2026-11-03', hora_inicio: '14:30' }, hoje)).toBe('Prova em 12 dias')
  expect(textoTopoProva({ data: '2026-10-22', hora_inicio: null }, hoje)).toBe('Prova hoje')
  expect(textoTopoProva({ data: '2026-10-23', hora_inicio: null }, hoje)).toBe('Prova amanhã')
  expect(textoTopoProva({ data: '2026-09-14', hora_inicio: null }, hoje)).toBe('Prova já foi (seg 14/09)')
  expect(textoTopoProva(null, hoje)).toBe('Sem data de prova')
})

test('ordem natural de nomes', async () => {
  const { compararNomes } = await import('./apresentacao')
  expect(['Aula 10', 'Aula 2', 'Aula 1'].sort(compararNomes)).toEqual(['Aula 1', 'Aula 2', 'Aula 10'])
})
