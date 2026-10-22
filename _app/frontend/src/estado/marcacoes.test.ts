import { beforeEach, expect, test, vi } from 'vitest'
import { painel, placarVazio } from '../teste-dados'
import { estadoMateria } from './materia.svelte'
import { marcaDe, marcar, proximaMarca, type Marca } from './marcacoes.svelte'

beforeEach(() => {
  Object.assign(estadoMateria, { uid: 'ab', unidade: 1, painel: painel({ marcacoes: {} }), carregando: false })
})

function json(status: number, corpo: unknown) {
  return new Response(JSON.stringify(corpo), { status, headers: { 'content-type': 'application/json' } })
}

test('ciclo da marca', () => {
  expect(([null, 'ok', 'err', 'dub'] as Marca[]).map(proximaMarca)).toEqual(['ok', 'err', 'dub', null])
})

test('marcar atualiza a tela e o placar', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json(200, { placar: { ...placarVazio, ok: 1, total: 1 } })))
  await marcar(7, 'ok')
  expect(marcaDe(7)).toBe('ok')
  expect(estadoMateria.painel?.placar?.ok).toBe(1)
  const [url, init] = vi.mocked(fetch).mock.calls[0]
  expect(url).toBe('/api/materias/ab/marcacoes/7')
  expect(init?.body).toBe('{"estado":"ok"}')
})

test('falha do motor reverte a marca', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json(422, { erro: 'Questão 7 não encontrada' })))
  await marcar(7, 'ok')
  expect(marcaDe(7)).toBe(null)
})

test('cliques rápidos terminam na última marca e na ordem', async () => {
  const ordem: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (_url: string, init: RequestInit) => {
    const estado = JSON.parse(init.body as string).estado
    await new Promise((r) => setTimeout(r, estado === 'ok' ? 30 : 5))   // a 1ª demora mais que as outras
    ordem.push(estado)
    return json(200, { placar: placarVazio })
  }))
  void marcar(7, 'ok')
  void marcar(7, 'err')
  await marcar(7, 'dub')
  expect(ordem).toEqual(['ok', 'err', 'dub'])
  expect(marcaDe(7)).toBe('dub')
})
