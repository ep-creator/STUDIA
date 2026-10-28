import { expect, test } from 'vitest'
import { analisarRota, montarHash, type Rota } from './rota'

test.each<[string, Rota]>([
  ['#/', { tela: 'materias' }],
  ['', { tela: 'materias' }],
  ['#/m/ab/u/2/listas', { tela: 'materia', uid: 'ab', unidade: 2, area: 'listas' }],
  ['#/m/ab', { tela: 'materia', uid: 'ab', unidade: null, area: 'painel' }],
  ['#/m/ab/importar', { tela: 'importar', uid: 'ab' }],
  ['#/m/ab/historico', { tela: 'historico', uid: 'ab' }],
  ['#/lixo', { tela: 'materias' }],
  ['#/m/ab/u/2/inexistente', { tela: 'materias' }],
])('analisarRota(%s)', (hash, rota) => {
  expect(analisarRota(hash)).toEqual(rota)
  expect(analisarRota(montarHash(rota))).toEqual(rota)
})

test('montarHash da área com unidade', () => {
  expect(montarHash({ tela: 'materia', uid: 'ab', unidade: 3, area: 'topicos' })).toBe('#/m/ab/u/3/topicos')
  expect(montarHash({ tela: 'materia', uid: 'ab', unidade: null, area: 'painel' })).toBe('#/m/ab')
})

test('hash malformado não derruba o app: volta para a tela inicial', () => {
  expect(analisarRota('#/m/%E0%A4%A')).toEqual({ tela: 'materias' })
})

test('rota do assistente', () => {
  expect(analisarRota('#/m/u1/assistente')).toEqual({ tela: 'assistente', uid: 'u1' })
  expect(montarHash({ tela: 'assistente', uid: 'u1' })).toBe('#/m/u1/assistente')
})
