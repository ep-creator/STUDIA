import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { ia } from '../estado/ia.svelte'
import Assistente from './Assistente.svelte'

const json = (d: unknown) => new Response(JSON.stringify(d), { status: 200, headers: { 'content-type': 'application/json' } })
let urls: string[] = []

function motor(conversas: unknown[]) {
  urls = []
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    urls.push(url)
    if (url.endsWith('/agente/conversas')) return json(conversas)
    if (url.includes('/agente/conversa?')) return json({ id: 1, alvo: 'x', papel: 'y', mensagens: [] })
    if (url.endsWith('/api/agente/estado')) return json({ chave_configurada: true, modelo: 'g', total_mes: 0, teto: 20 })
    throw new Error(`rota não simulada: ${url}`)
  }))
}

const CONVERSAS = [
  { id: 3, alvo: 'questao:5', papel: 'tutor', rotulo: '14.1 #22', atualizada_em: '2026-10-28T09:00:00' },
  { id: 2, alvo: 'geral', papel: 'estrategista', rotulo: 'Geral', atualizada_em: '2026-10-27T09:00:00' },
  { id: 4, alvo: 'secao:3', papel: 'resumidor', rotulo: '15.4 Integrais duplas', atualizada_em: '2026-09-12T09:00:00' },
]

beforeEach(() => { ia.alvo = null; ia.papel = null; ia.paraPagina = null })
afterEach(() => vi.unstubAllGlobals())

test('lista as conversas agrupadas e abre a escolhida', async () => {
  motor(CONVERSAS)
  render(Assistente, { uid: 'u1', hoje: new Date(2026, 9, 28) })
  expect(await screen.findByText('Questões')).toBeInTheDocument()
  expect(screen.getByText('Seções')).toBeInTheDocument()
  const questao = screen.getByRole('button', { name: /14\.1 #22/ })
  expect(questao).toHaveTextContent('hoje')
  expect(screen.getByRole('button', { name: /Geral/ })).toHaveTextContent('ontem')
  expect(screen.getByRole('button', { name: /15\.4 Integrais duplas/ })).toHaveTextContent('12/09')
  await userEvent.click(questao)
  expect(questao).toHaveAttribute('aria-current', 'true')
  await waitFor(() => expect(urls.some((u) => u.includes('/agente/conversa?alvo=questao%3A5&papel=tutor'))).toBe(true))
  expect(screen.getByRole('group', { name: 'Nível de ajuda' })).toBeInTheDocument()
})

test('sem conversas, abre a geral do estrategista', async () => {
  motor([])
  render(Assistente, { uid: 'u1', hoje: new Date(2026, 9, 28) })
  await waitFor(() => expect(urls.some((u) => u.includes('/agente/conversa?alvo=geral&papel=estrategista'))).toBe(true))
  expect(screen.getByRole('button', { name: 'Plano de revisão' })).toBeInTheDocument()
})

test('chegando pela gaveta, abre a conversa que estava aberta', async () => {
  motor(CONVERSAS)
  ia.paraPagina = { uid: 'u1', alvo: 'secao:3', papel: 'resumidor' }
  render(Assistente, { uid: 'u1', hoje: new Date(2026, 9, 28) })
  await waitFor(() => expect(urls.some((u) => u.includes('/agente/conversa?alvo=secao%3A3&papel=resumidor'))).toBe(true))
  expect(await screen.findByRole('button', { name: /15\.4 Integrais duplas/ })).toHaveAttribute('aria-current', 'true')
})

test('não há + nova conversa', async () => {
  motor(CONVERSAS)
  render(Assistente, { uid: 'u1', hoje: new Date(2026, 9, 28) })
  await screen.findByText('Questões')
  expect(screen.queryByText(/nova conversa/i)).toBeNull()
})

test('o pedido da gaveta vale uma vez só: a visita seguinte abre a conversa mais recente', async () => {
  motor(CONVERSAS)
  ia.paraPagina = { uid: 'u1', alvo: 'secao:3', papel: 'resumidor' }
  const primeira = render(Assistente, { uid: 'u1', hoje: new Date(2026, 9, 28) })
  await screen.findByText('Questões')
  primeira.unmount()
  expect(ia.paraPagina).toBeNull()
  render(Assistente, { uid: 'u1', hoje: new Date(2026, 9, 28) })
  expect(await screen.findByRole('button', { name: /14.1 #22/ })).toHaveAttribute('aria-current', 'true')
})

test('um pedido feito em outra matéria é ignorado', async () => {
  motor(CONVERSAS)
  ia.alvo = 'secao:7'
  ia.papel = 'resumidor'
  ia.paraPagina = { uid: 'outra', alvo: 'secao:7', papel: 'resumidor' }
  render(Assistente, { uid: 'u1', hoje: new Date(2026, 9, 28) })
  expect(await screen.findByRole('button', { name: /14.1 #22/ })).toHaveAttribute('aria-current', 'true')
})
