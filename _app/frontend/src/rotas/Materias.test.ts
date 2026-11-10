import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'
import Materias from './Materias.svelte'

const M = { uid: 'u1', nome: 'Sistemas Digitais', periodo: null, unidades: 0, proxima_prova: null, importacoes_pendentes: 0 }
afterEach(() => vi.unstubAllGlobals())

test('apagar matéria pede confirmação, move para a lixeira e recarrega a lista', async () => {
  const chamadas: { url: string; metodo: string }[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit = {}) => {
    chamadas.push({ url, metodo: init.method ?? 'GET' })
    return new Response(JSON.stringify({ movida_para: '_lixeira/Sistemas Digitais (x)' }), { status: 200, headers: { 'content-type': 'application/json' } })
  }))
  const confirmar = vi.fn((_texto: string) => true)
  vi.stubGlobal('confirm', confirmar)
  const onmudou = vi.fn()
  render(Materias, { materias: [M], onmudou })
  await userEvent.click(screen.getByRole('button', { name: 'Mais ações de Sistemas Digitais' }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Apagar matéria' }))
  expect(confirmar.mock.calls[0][0]).toMatch(/Sistemas Digitais.*_lixeira/s)
  await waitFor(() => expect(chamadas).toContainEqual({ url: expect.stringMatching(/\/api\/materias\/u1$/), metodo: 'DELETE' }))
  await waitFor(() => expect(onmudou).toHaveBeenCalled())
})

test('cancelar a confirmação não apaga nada', async () => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  vi.stubGlobal('confirm', vi.fn(() => false))
  render(Materias, { materias: [M], onmudou: vi.fn() })
  await userEvent.click(screen.getByRole('button', { name: 'Mais ações de Sistemas Digitais' }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Apagar matéria' }))
  expect(fetch).not.toHaveBeenCalled()
})
