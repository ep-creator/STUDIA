import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import Historico from './Historico.svelte'

const agora = new Date()
const momento = (min: number) => new Date(agora.getTime() - min * 60_000).toISOString().slice(0, 19)
const grupo = (id: number, descricao: string, min: number) => ({ id, momento: momento(min), descricao, desfaz_grupo: null, desfeito_em: null })

beforeEach(() => {
  const grupos = [
    grupo(9, 'Marcar questão 14.2 #18 como ok', 1),
    grupo(8, 'Marcar questão 14.2 #18 como err', 2),
    grupo(7, 'Marcar questão 14.2 #18 como dub', 3),
    grupo(6, 'Marcar questão 14.2 #17 como ok', 4),
  ]
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(grupos), { headers: { 'content-type': 'application/json' } })))
})
afterEach(() => vi.unstubAllGlobals())

test('remarcar a mesma questão em sequência vira uma linha, com as anteriores a um clique', async () => {
  render(Historico, { uid: 'ab' })
  expect(await screen.findByText(/14\.2 #18 como ok/)).toBeInTheDocument()
  expect(screen.queryByText(/14\.2 #18 como err/)).toBeNull()
  expect(screen.getByText(/14\.2 #17 como ok/)).toBeInTheDocument()       // outra questão: linha própria
  await userEvent.click(screen.getByRole('button', { name: '+2 marcações anteriores da mesma questão' }))
  expect(screen.getByText(/14\.2 #18 como err/)).toBeInTheDocument()
})
