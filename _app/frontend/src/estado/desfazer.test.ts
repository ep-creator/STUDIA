import { beforeEach, expect, test, vi } from 'vitest'
import { avisos } from './avisos.svelte'
import { atalhoDesfazer, desfazer } from './desfazer'
import { estadoMateria } from './materia.svelte'

function tecla(key: string, mods: KeyboardEventInit, alvo: EventTarget): KeyboardEvent {
  const e = new KeyboardEvent('keydown', { key, ...mods })
  Object.defineProperty(e, 'target', { value: alvo })
  return e
}

beforeEach(() => {
  avisos.lista = []
  Object.assign(estadoMateria, { uid: 'ab', unidade: 1, painel: null, carregando: false })
})

test('ctrl+z não age dentro do editor', () => {
  expect(atalhoDesfazer(tecla('z', { ctrlKey: true }, document.body))).toBe(true)
  expect(atalhoDesfazer(tecla('z', { metaKey: true }, document.body))).toBe(true)
  expect(atalhoDesfazer(tecla('z', { ctrlKey: true }, document.createElement('textarea')))).toBe(false)
  expect(atalhoDesfazer(tecla('z', { ctrlKey: true }, document.createElement('input')))).toBe(false)
  expect(atalhoDesfazer(tecla('z', {}, document.body))).toBe(false)
  expect(atalhoDesfazer(tecla('z', { ctrlKey: true, shiftKey: true }, document.body))).toBe(false)
})

function json(corpo: unknown) {
  return new Response(JSON.stringify(corpo), { status: 200, headers: { 'content-type': 'application/json' } })
}

test('desfazer avisa o que foi desfeito e recarrega', async () => {
  const chamadas: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit = {}) => {
    chamadas.push(`${init.method ?? 'GET'} ${url}`)
    if (url.endsWith('/historico/desfazer')) return json({ desfeito: { id: 7, momento: '', descricao: 'Importar Stewart vol. 2', desfaz_grupo: null, desfeito_em: '' } })
    return json({ materia: { uid: 'ab' }, unidade: 1, unidades: [] })
  }))
  await desfazer()
  expect(avisos.lista.map((a) => a.texto)).toContain('Desfeito: Importar Stewart vol. 2')
  expect(chamadas).toEqual([
    'GET /api/materias/ab/historico?limite=30', 'POST /api/materias/ab/historico/desfazer', 'GET /api/materias/ab/painel?unidade=1',
  ])
})

test('a última ação é antiga: diz qual é e só desfaz se confirmar', async () => {
  const chamadas: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit = {}) => {
    chamadas.push(`${init.method ?? 'GET'} ${url}`)
    if (url.includes('/historico?')) {
      return json([{ id: 9, momento: '2020-01-02T10:00:00', descricao: 'IA: resolução 15.7-33', desfaz_grupo: null, desfeito_em: null }])
    }
    return json({ desfeito: null })
  }))
  await desfazer()
  const aviso = avisos.lista.at(-1)!
  expect(aviso.texto).toMatch(/^A última ação é de .*: IA: resolução 15\.7-33$/)
  expect(chamadas).toEqual(['GET /api/materias/ab/historico?limite=30'])   // nada desfeito ainda
  expect(aviso.acao?.rotulo).toBe('Desfazer mesmo')
})

test('nada para desfazer', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => json({ desfeito: null })))
  await desfazer()
  expect(avisos.lista.map((a) => a.texto)).toContain('Nada para desfazer')
})
