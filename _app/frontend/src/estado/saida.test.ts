import { afterEach, expect, test, vi } from 'vitest'
import { haAlteracoes, marcarAlteracoes, podeSair } from './saida'

afterEach(() => marcarAlteracoes('editor', false))

test('sem alterações pendentes pode sair sem perguntar', () => {
  const pergunta = vi.spyOn(window, 'confirm')
  expect(podeSair()).toBe(true)
  expect(pergunta).not.toHaveBeenCalled()
})

test('com alterações pendentes pergunta antes de sair', () => {
  marcarAlteracoes('editor', true)
  expect(haAlteracoes()).toBe(true)
  vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true)
  expect(podeSair()).toBe(false)
  expect(podeSair()).toBe(true)
  expect(haAlteracoes()).toBe(false)   // quem confirmou a saída descartou o texto
})
