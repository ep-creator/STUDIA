import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { pedido } from '../estado/pedido.svelte'
import { estadoMateria } from '../estado/materia.svelte'
import PainelIA from './PainelIA.svelte'

type Pedido = { metodo: string; url: string; corpo: unknown }
let pedidos: Pedido[] = []

const json = (dados: unknown, status = 200) =>
  new Response(JSON.stringify(dados), { status, headers: { 'content-type': 'application/json' } })
const ndjson = (eventos: unknown[]) =>
  new Response(eventos.map((e) => JSON.stringify(e)).join('\n') + '\n', { status: 200, headers: { 'content-type': 'application/x-ndjson' } })

function motor(opcoes: { chave?: boolean; respostas?: unknown[][]; historicoTopo?: number } = {}) {
  pedidos = []
  const respostas = [...(opcoes.respostas ?? [])]
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit = {}) => {
    const metodo = init.method ?? 'GET'
    pedidos.push({ metodo, url, corpo: init.body ? JSON.parse(String(init.body)) : null })
    if (url.includes('/agente/conversa/recomecar')) return json({ id: 2, alvo: 'questao:5', papel: 'tutor', mensagens: [] })
    if (url.includes('/agente/conversa')) return json({ id: 1, alvo: 'questao:5', papel: 'tutor', mensagens: [] })
    if (url.endsWith('/api/agente/estado')) return json({ chave_configurada: opcoes.chave ?? true, modelo: 'gemini', total_mes: 1.5, teto: 20 })
    if (url.endsWith('/api/agente/chave')) return json({ ok: true })
    if (url.includes('/agente/contexto')) return json({ texto: 'PACOTE DE CONTEXTO' })
    if (url.includes('/agente/mensagem')) return ndjson(respostas.shift() ?? [])
    if (url.endsWith('/fontes')) return json([{ id: 1, tipo: 'livro', titulo: 'Stewart', caminho: 'fontes/livros/s.pdf', paginas: 600 }])
    if (url.includes('/historico/desfazer')) return json({ desfeito: { id: 77, descricao: 'Agente: resolução l1-3' } })
    if (url.includes('/historico')) return json([{ id: opcoes.historicoTopo ?? 77, momento: 'x', descricao: 'y', desfaz_grupo: null, desfeito_em: null }])
    throw new Error(`rota não simulada: ${metodo} ${url}`)
  }))
}

const RESPOSTA = [
  { tipo: 'texto', dados: { texto: 'Use polares ' } },
  { tipo: 'texto', dados: { texto: '[Stewart p. 312].' } },
  { tipo: 'fim', dados: { custo_brl: 0.04, total_mes: 1.54, tokens_entrada: 10, tokens_saida: 5 } },
]

beforeEach(() => {
  estadoMateria.uid = 'u1'
  estadoMateria.unidade = 3
  pedido.fonte = null
  pedido.documento = null
  location.hash = '#/m/u1/u/3/listas'
})
afterEach(() => vi.unstubAllGlobals())

const abrir = () => render(PainelIA, { uid: 'u1', alvo: 'questao:5', papel: 'tutor', atalhos: ['N1', 'N2', 'N3', 'N4'] })

test('atalho manda o pedido e a resposta chega aos pedaços, com o custo', async () => {
  motor({ respostas: [RESPOSTA] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N2 Caminho/ }))
  expect(await screen.findByText(/Use polares/)).toBeInTheDocument()
  const enviado = pedidos.find((p) => p.url.includes('/agente/mensagem'))!
  expect(enviado.corpo).toEqual({ alvo: 'questao:5', papel: 'tutor', atalho: 'N2', confirmado: false })
  expect(screen.getByText(/R\$ 0,04/)).toBeInTheDocument()
  expect(screen.getByText(/mês: R\$ 1,54 de R\$ 20,00/)).toBeInTheDocument()
})

test('citação vira link que abre o livro na página', async () => {
  motor({ respostas: [RESPOSTA] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N2 Caminho/ }))
  await userEvent.click(await screen.findByRole('link', { name: 'Stewart p. 312' }))
  await waitFor(() => expect(pedido.fonte).toEqual({ id: 1, pagina: 312 }))
  expect(location.hash).toContain('documentos')
})

test('o que foi gravado aparece com Abrir e Desfazer', async () => {
  motor({ respostas: [[{ tipo: 'gravado', dados: { tipo: 'documento', id: 9, titulo: 'Resolução L1-3', grupo_id: 77 } },
    { tipo: 'texto', dados: { texto: 'Gravei.' } }, { tipo: 'fim', dados: { custo_brl: 0.01, total_mes: 1.51 } }]] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N4 Resolução/ }))
  expect(await screen.findByText(/Resolução L1-3 salva/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Desfazer' }))
  await waitFor(() => expect(pedidos.some((p) => p.metodo === 'POST' && p.url.includes('/historico/desfazer'))).toBe(true))
})

test('com outra ação depois, Desfazer vira Abrir o Histórico', async () => {
  motor({ historicoTopo: 80, respostas: [[{ tipo: 'gravado', dados: { tipo: 'documento', id: 9, titulo: 'Resolução L1-3', grupo_id: 77 } },
    { tipo: 'fim', dados: { custo_brl: 0, total_mes: 1.5 } }]] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N4 Resolução/ }))
  await userEvent.click(await screen.findByRole('button', { name: 'Desfazer' }))
  expect(await screen.findByRole('link', { name: /Abrir o Histórico/ })).toBeInTheDocument()
  expect(pedidos.some((p) => p.url.includes('/historico/desfazer'))).toBe(false)
})

test('teto do mês pede confirmação e reenvia confirmado', async () => {
  motor({ respostas: [[{ tipo: 'confirmar', dados: { total_mes: 19.98, teto: 20 } }], RESPOSTA] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N1 Dica/ }))
  expect(await screen.findByText(/teto de R\$ 20,00/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Continuar' }))
  await waitFor(() => expect(pedidos.filter((p) => p.url.includes('/agente/mensagem')).at(-1)?.corpo)
    .toMatchObject({ atalho: 'N1', confirmado: true }))
})

test('sem chave: campo para colar a chave e Copiar o contexto', async () => {
  motor({ chave: false })
  const copiar = vi.fn(async () => {})
  Object.assign(navigator, { clipboard: { writeText: copiar } })
  abrir()
  await userEvent.type(await screen.findByLabelText(/Chave do Gemini/), 'AIza-teste')
  await userEvent.click(screen.getByRole('button', { name: 'Salvar a chave' }))
  await waitFor(() => expect(pedidos.find((p) => p.metodo === 'PUT')?.corpo).toEqual({ chave: 'AIza-teste' }))
  await userEvent.click(screen.getByRole('button', { name: /Copiar o contexto/ }))
  await waitFor(() => expect(copiar).toHaveBeenCalledWith('PACOTE DE CONTEXTO'))
})

test('erro do Gemini mostra o motivo e Tentar de novo', async () => {
  motor({ respostas: [[{ tipo: 'texto', dados: { texto: 'Começ' } }, { tipo: 'erro', dados: { motivo: 'indisponivel', detalhe: '503' } }], RESPOSTA] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N3 Esboço/ }))
  expect(await screen.findByText(/não consegui falar com o Gemini/i)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))
  expect(await screen.findByText(/Use polares/)).toBeInTheDocument()
})
