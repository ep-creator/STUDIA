import { beforeEach, expect, test, vi } from 'vitest'

beforeEach(() => {
  vi.resetModules()
  localStorage.clear()
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() })))
})

test('tema padrão segue o sistema, no Editorial', async () => {
  const { tema, aplicarTema } = await import('./tema.svelte')
  expect(tema.modo).toBe('sistema')
  aplicarTema()
  expect(document.documentElement.dataset.tema).toBe('editorial-claro')
})

test('sistema escuro escolhe a versão escura', async () => {
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })))
  const { aplicarTema } = await import('./tema.svelte')
  aplicarTema()
  expect(document.documentElement.dataset.tema).toBe('editorial-escuro')
})

test('escolherModo salva só o modo e é relido', async () => {
  const primeiro = await import('./tema.svelte')
  primeiro.escolherModo('claro')
  expect(JSON.parse(localStorage.getItem('estudos.tema')!)).toEqual({ modo: 'claro' })
  expect(document.documentElement.dataset.tema).toBe('editorial-claro')
  vi.resetModules()
  const segundo = await import('./tema.svelte')
  expect(segundo.tema.modo).toBe('claro')
})

test('preferência antiga com identidade padrão vira editorial', async () => {
  localStorage.setItem('estudos.tema', JSON.stringify({ identidade: 'padrao', modo: 'escuro' }))
  const { tema, temaEfetivo } = await import('./tema.svelte')
  expect(tema.modo).toBe('escuro')
  expect(temaEfetivo()).toBe('editorial-escuro')
})

test('localStorage indisponível não quebra o tema', async () => {
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('bloqueado') })
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('bloqueado') })
  const { aplicarTema, escolherModo } = await import('./tema.svelte')
  expect(() => aplicarTema()).not.toThrow()
  expect(() => escolherModo('claro')).not.toThrow()
})
