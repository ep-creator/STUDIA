import { beforeEach, expect, test, vi } from 'vitest'
import { carregarPainel, estadoMateria, painelACarregar } from './materia.svelte'

beforeEach(() => {
  Object.assign(estadoMateria, { uid: null, unidade: null, painel: null, carregando: false })
})

test('outra matéria nunca herda a unidade da anterior', () => {
  const atual = { uid: 'A', unidade: 1 }
  expect(painelACarregar({ tela: 'importar', uid: 'B' }, atual)).toEqual({ uid: 'B', unidade: null })
  expect(painelACarregar({ tela: 'historico', uid: 'B' }, atual)).toEqual({ uid: 'B', unidade: null })
  expect(painelACarregar({ tela: 'materia', uid: 'B', unidade: null, area: 'painel' }, atual)).toEqual({ uid: 'B', unidade: null })
  expect(painelACarregar({ tela: 'materia', uid: 'B', unidade: 2, area: 'listas' }, atual)).toEqual({ uid: 'B', unidade: 2 })
})

test('mesma matéria só recarrega ao pedir outra unidade', () => {
  const atual = { uid: 'A', unidade: 1 }
  expect(painelACarregar({ tela: 'importar', uid: 'A' }, atual)).toBeNull()
  expect(painelACarregar({ tela: 'materia', uid: 'A', unidade: 1, area: 'listas' }, atual)).toBeNull()
  expect(painelACarregar({ tela: 'materia', uid: 'A', unidade: null, area: 'painel' }, atual)).toBeNull()
  expect(painelACarregar({ tela: 'materia', uid: 'A', unidade: 3, area: 'listas' }, atual)).toEqual({ uid: 'A', unidade: 3 })
  expect(painelACarregar({ tela: 'materias' }, atual)).toBeNull()
})

test('unidade que não existe cai para a unidade atual da matéria', async () => {
  const urls: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    urls.push(url)
    if (url.includes('unidade=')) {
      return new Response('{"erro":"Unidade 1 não existe nesta matéria"}', { status: 404, headers: { 'content-type': 'application/json' } })
    }
    return new Response(JSON.stringify({ materia: { uid: 'B' }, unidade: null, unidades: [] }), { status: 200, headers: { 'content-type': 'application/json' } })
  }))
  await carregarPainel('B', 1)
  expect(urls).toEqual(['/api/materias/B/painel?unidade=1', '/api/materias/B/painel'])
  expect(estadoMateria.uid).toBe('B')
  expect(estadoMateria.painel).not.toBeNull()
})
