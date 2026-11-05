import { expect, test } from 'vitest'
import { analisarRota, montarHash, precisaListaDeMaterias, type Rota } from './rota'

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

test('a lista de matérias recarrega na tela inicial, sem lista, ou quando a matéria aberta não está nela (uma vez por matéria)', () => {
  const lista = [{ uid: 'a' }]
  expect(precisaListaDeMaterias({ tela: 'materias' }, lista, null)).toBe(true)
  expect(precisaListaDeMaterias({ tela: 'importar', uid: 'a' }, [], null)).toBe(true)
  expect(precisaListaDeMaterias({ tela: 'importar', uid: 'a' }, lista, null)).toBe(false)
  // matéria recém-criada: ainda não está na lista
  expect(precisaListaDeMaterias({ tela: 'importar', uid: 'nova' }, lista, null)).toBe(true)
  // já pediu para essa matéria e ela continua fora (endereço errado): não pede de novo
  expect(precisaListaDeMaterias({ tela: 'importar', uid: 'nova' }, lista, 'nova')).toBe(false)
  // workspace sem matérias: a lista vazia também é pedida uma vez só por matéria
  expect(precisaListaDeMaterias({ tela: 'importar', uid: 'a' }, [], 'a')).toBe(false)
})

test('página de um tópico tem endereço próprio', () => {
  const rota = analisarRota('#/m/ab/u/3/topicos/14')
  expect(rota).toEqual({ tela: 'materia', uid: 'ab', unidade: 3, area: 'topicos', topico: 14 })
  expect(montarHash(rota)).toBe('#/m/ab/u/3/topicos/14')
  expect(analisarRota('#/m/ab/u/3/topicos/x')).toEqual({ tela: 'materias' })
  expect(montarHash({ tela: 'materia', uid: 'ab', unidade: 3, area: 'listas', topico: 14 })).toBe('#/m/ab/u/3/listas')
})
