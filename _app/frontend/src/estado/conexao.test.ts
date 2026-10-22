import { expect, test, vi } from 'vitest'
import { conexao, verificarMotor } from './conexao.svelte'

test('motor volta depois de desligado', async () => {
  vi.useFakeTimers()
  const fetchFalso = vi.fn()
    .mockRejectedValueOnce(new TypeError('Failed to fetch'))
    .mockResolvedValue(new Response('[]', { status: 200, headers: { 'content-type': 'application/json' } }))
  vi.stubGlobal('fetch', fetchFalso)

  const verificando = verificarMotor()
  await vi.advanceTimersByTimeAsync(0)
  expect(conexao.motorLigado).toBe(false)
  await vi.advanceTimersByTimeAsync(3000)
  await verificando
  expect(conexao.motorLigado).toBe(true)
  expect(fetchFalso).toHaveBeenCalledTimes(2)
  vi.useRealTimers()
})
