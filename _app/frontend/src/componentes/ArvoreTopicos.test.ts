import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'
import type { TopicoProgresso } from '../api/tipos'
import { topico } from '../teste-dados'
import ArvoreTopicos from './ArvoreTopicos.svelte'

const progresso = (id: number, estado: string, extra: Partial<TopicoProgresso> = {}): TopicoProgresso => ({
  id, titulo: '', estado, secoes: [], total: 0, trabalhadas: 0, ok: 0, err: 0, dub: 0, ...extra,
})

function motor(lista: TopicoProgresso[] = []) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const corpo = url.includes('/progresso') ? lista : { ok: true }
    return new Response(JSON.stringify(corpo), { status: 200, headers: { 'content-type': 'application/json' } })
  }))
}
const escritas = () => vi.mocked(fetch).mock.calls.filter(([, init]) => init?.method && init.method !== 'GET')
afterEach(() => vi.unstubAllGlobals())

const props = { uid: 'ab', unidade: 3, unidadeId: 1, onmudou: vi.fn() }

test('o título abre a página do tópico; estado e placar vêm derivados', async () => {
  motor([progresso(1, 'hoje', { secoes: ['15.4', '15.5'], total: 13, trabalhadas: 4 })])
  render(ArvoreTopicos, { ...props, topicos: [topico(1, 'pendente', { titulo: 'Polares' })] })
  expect(screen.getByRole('link', { name: 'Polares' })).toHaveAttribute('href', '#/m/ab/u/3/topicos/1')
  expect(await screen.findByText('hoje')).toBeInTheDocument()
  expect(screen.getByText('4/13')).toBeInTheDocument()
  expect(screen.getByText('15.4 · 15.5')).toBeInTheDocument()
  expect(vi.mocked(fetch).mock.calls[0][0]).toMatch(/\/api\/materias\/ab\/progresso\?unidade=3$/)
})

test('o visto à mão fica no menu ··· (o estado já se deriva sozinho)', async () => {
  motor()
  const onmudou = vi.fn()
  render(ArvoreTopicos, { ...props, onmudou, topicos: [topico(1, 'pendente', { titulo: 'Polares' })] })
  await userEvent.click(screen.getByRole('button', { name: 'Mais ações de Polares' }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Marcar como visto' }))
  await waitFor(() => expect(escritas()).toHaveLength(1))
  const [url, init] = escritas()[0]
  expect(url).toMatch(/\/topicos\/1$/)
  expect(JSON.parse(init?.body as string)).toEqual({ status: 'visto' })
  expect(onmudou).toHaveBeenCalled()
})

test('subtópicos aparecem dentro do pai', () => {
  motor()
  render(ArvoreTopicos, {
    ...props,
    topicos: [topico(1, 'visto', { titulo: 'Integração dupla' }), topico(2, 'pendente', { titulo: 'Polares', pai_id: 1 })],
  })
  const pai = screen.getByRole('link', { name: 'Integração dupla' }).closest('li')!
  expect(pai).toContainElement(screen.getByRole('link', { name: 'Polares' }))
})

test('apagar fica no menu ··· da linha, alcançável por teclado', async () => {
  motor()
  vi.stubGlobal('confirm', vi.fn(() => true))
  render(ArvoreTopicos, { ...props, topicos: [topico(1, 'pendente', { titulo: 'Polares' })] })
  expect(screen.queryByRole('button', { name: /^Apagar / })).toBeNull()
  const mais = screen.getByRole('button', { name: 'Mais ações de Polares' })
  expect(mais.closest('.acoes-linha')).not.toBeNull()
  mais.focus()
  await userEvent.keyboard('{Enter}')
  await userEvent.click(screen.getByRole('menuitem', { name: 'Apagar' }))
  await waitFor(() => expect(escritas()).toHaveLength(1))
  const [url, init] = escritas()[0]
  expect(url).toMatch(/\/topicos\/1$/)
  expect(init?.method).toBe('DELETE')
})

test('novo tópico: Enter adiciona, sem botão Adicionar', async () => {
  motor()
  render(ArvoreTopicos, { ...props, topicos: [] })
  expect(screen.queryByRole('button', { name: /Adicionar/ })).toBeNull()
  await userEvent.type(screen.getByRole('textbox', { name: 'Novo tópico' }), 'Revisão{Enter}')
  await waitFor(() => expect(escritas()).toHaveLength(1))
  const [, init] = escritas()[0]
  expect(init?.method).toBe('POST')
  expect(JSON.parse(init?.body as string)).toEqual({ unidade_id: 1, titulo: 'Revisão' })
})
