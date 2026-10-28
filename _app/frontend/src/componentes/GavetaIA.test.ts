import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { ia } from '../estado/ia.svelte'
import GavetaIA from './GavetaIA.svelte'

const json = (d: unknown) => new Response(JSON.stringify(d), { status: 200, headers: { 'content-type': 'application/json' } })

beforeEach(() => {
  ia.alvo = 'geral'
  ia.papel = 'estrategista'
  ia.aberta = true
  location.hash = '#/m/u1/u/3/painel'
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.includes('/agente/conversa?')) return json({ id: 1, alvo: 'geral', papel: 'estrategista', mensagens: [] })
    if (url.endsWith('/api/agente/estado')) return json({ chave_configurada: true, modelo: 'g', total_mes: 0, teto: 20 })
    throw new Error(`rota não simulada: ${url}`)
  }))
})
afterEach(() => vi.unstubAllGlobals())

function abrirDe() {
  const botao = document.createElement('button')
  botao.textContent = 'IA ›'
  document.body.appendChild(botao)
  botao.focus()
  return botao
}

test('ao abrir, o foco vai para o campo de mensagem', async () => {
  abrirDe()
  render(GavetaIA, { uid: 'u1', onfechar: vi.fn() })
  await waitFor(() => expect(screen.getByRole('textbox', { name: 'Mensagem para o assistente' })).toHaveFocus())
  expect(screen.getByRole('dialog', { name: 'Assistente' })).toHaveAttribute('aria-modal', 'true')
})

test('Esc fecha e o foco volta para quem abriu', async () => {
  const botao = abrirDe()
  const { unmount } = render(GavetaIA, { uid: 'u1', onfechar: () => unmount() })
  await waitFor(() => expect(screen.getByRole('textbox', { name: 'Mensagem para o assistente' })).toHaveFocus())
  await userEvent.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(botao).toHaveFocus()
})

test('clicar no véu fecha', async () => {
  const onfechar = vi.fn()
  render(GavetaIA, { uid: 'u1', onfechar })
  await userEvent.click(screen.getByRole('button', { name: 'Fechar o assistente' }))
  expect(onfechar).toHaveBeenCalled()
})

test('Tab fica preso dentro da gaveta', async () => {
  abrirDe()
  render(GavetaIA, { uid: 'u1', onfechar: vi.fn() })
  const gaveta = screen.getByRole('dialog', { name: 'Assistente' })
  await waitFor(() => expect(screen.getByRole('textbox', { name: 'Mensagem para o assistente' })).toHaveFocus())
  for (let i = 0; i < 12; i++) {
    await userEvent.tab()
    expect(gaveta.contains(document.activeElement)).toBe(true)
  }
})

test('abrir em página leva para a página do Assistente com a mesma conversa', async () => {
  render(GavetaIA, { uid: 'u1', onfechar: vi.fn() })
  await userEvent.click(screen.getByRole('link', { name: /abrir em página/ }))
  expect(location.hash).toBe('#/m/u1/assistente')
  expect(ia.alvo).toBe('geral')
  expect(ia.aberta).toBe(false)
})
