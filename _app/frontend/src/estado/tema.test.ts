import { beforeEach, expect, test, vi } from 'vitest'

beforeEach(() => {
  vi.resetModules()
  localStorage.clear()
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() })))
})

test('tema padrão é editorial seguindo o sistema', async () => {
  const { tema, aplicarTema } = await import('./tema.svelte')
  expect([tema.identidade, tema.modo]).toEqual(['editorial', 'sistema'])
  aplicarTema()
  expect(document.documentElement.dataset.tema).toBe('editorial-claro')
})

test('sistema escuro escolhe a versão escura da identidade', async () => {
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })))
  const { aplicarTema } = await import('./tema.svelte')
  aplicarTema()
  expect(document.documentElement.dataset.tema).toBe('editorial-escuro')
})

test('escolha é salva e relida', async () => {
  const primeiro = await import('./tema.svelte')
  primeiro.escolherTema('padrao', 'escuro')
  expect(document.documentElement.dataset.tema).toBe('padrao-escuro')
  vi.resetModules()
  const segundo = await import('./tema.svelte')
  expect([segundo.tema.identidade, segundo.tema.modo]).toEqual(['padrao', 'escuro'])
})

test('localStorage indisponível não quebra o tema', async () => {
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('bloqueado') })
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('bloqueado') })
  const { aplicarTema, escolherTema } = await import('./tema.svelte')
  expect(() => aplicarTema()).not.toThrow()
  expect(() => escolherTema('padrao', 'claro')).not.toThrow()
})
