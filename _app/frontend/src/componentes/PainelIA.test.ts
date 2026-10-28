import { render, screen, waitFor, within } from '@testing-library/svelte'
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

test('sem chave: só a caixa da API key, que salva com Enter', async () => {
  motor({ chave: false })
  abrir()
  await userEvent.type(await screen.findByPlaceholderText('API key'), 'AIza-teste{Enter}')
  await waitFor(() => expect(pedidos.find((p) => p.metodo === 'PUT')?.corpo).toEqual({ chave: 'AIza-teste' }))
  expect(screen.queryByText(/Google AI Studio/)).toBeNull()
})

test('atalhos aparecem curtos (N1…N4) e não há Copiar o contexto', async () => {
  motor()
  abrir()
  const n2 = await screen.findByRole('button', { name: 'N2 Caminho' })
  expect(n2).toHaveTextContent(/^N2$/)
  expect(screen.queryByRole('button', { name: /Copiar o contexto/ })).toBeNull()
})

test('erro do Gemini mostra o motivo e Tentar de novo', async () => {
  motor({ respostas: [[{ tipo: 'texto', dados: { texto: 'Começ' } }, { tipo: 'erro', dados: { motivo: 'indisponivel', detalhe: '503' } }], RESPOSTA] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N3 Esboço/ }))
  expect(await screen.findByText(/não consegui falar com o Gemini/i)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))
  expect(await screen.findByText(/Use polares/)).toBeInTheDocument()
})

test('trocar de questão no meio da resposta corta a antiga e não mistura as conversas', async () => {
  motor()
  let fluxo!: ReadableStreamDefaultController<Uint8Array>
  let sinal: AbortSignal | null | undefined
  let iniciado = false
  const base = vi.mocked(fetch).getMockImplementation()!
  vi.mocked(fetch).mockImplementation(async (url, init = {}) => {
    if (String(url).includes('/agente/mensagem') && !iniciado) {
      iniciado = true
      sinal = init.signal
      return new Response(new ReadableStream<Uint8Array>({ start: (c) => { fluxo = c } }), { status: 200 })
    }
    return base(url as string, init)
  })
  const linha = (e: unknown) => new TextEncoder().encode(JSON.stringify(e) + '\n')
  const { rerender } = abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N2 Caminho/ }))
  await waitFor(() => expect(iniciado).toBe(true))
  fluxo.enqueue(linha({ tipo: 'texto', dados: { texto: 'Da questão cinco' } }))
  expect(await screen.findByText(/Da questão cinco/)).toBeInTheDocument()

  await rerender({ uid: 'u1', alvo: 'questao:6', papel: 'tutor', atalhos: ['N1', 'N2', 'N3', 'N4'] })
  expect(sinal?.aborted).toBe(true)
  fluxo.enqueue(linha({ tipo: 'texto', dados: { texto: 'VAZOU' } }))
  await new Promise((r) => setTimeout(r, 20))
  expect(screen.queryByText(/VAZOU/)).not.toBeInTheDocument()
  expect(screen.queryByText(/Da questão cinco/)).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: /N1 Dica/ })).toBeEnabled()
})

test('pedido recusado pelo Gemini não manda trocar a chave e mostra o detalhe', async () => {
  motor({ respostas: [[{ tipo: 'erro', dados: { motivo: 'pedido_invalido', detalhe: 'Invalid JSON payload received.' } }]] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N3 Esboço/ }))
  expect(await screen.findByText(/recusou o pedido.*Invalid JSON payload received/i)).toBeInTheDocument()
  expect(screen.queryByText(/chave/i)).not.toBeInTheDocument()
})

test('erro interno do app mostra o detalhe em vez de "fora do ar"', async () => {
  motor({ respostas: [[{ tipo: 'erro', dados: { motivo: 'interno', detalhe: 'PermissionError: arquivo travado' } }]] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: /N3 Esboço/ }))
  expect(await screen.findByText(/PermissionError: arquivo travado/)).toBeInTheDocument()
  expect(screen.queryByText(/fora do ar/)).not.toBeInTheDocument()
})

test('N1–N4 num grupo só e Recomeçar dentro do ···', async () => {
  motor({ respostas: [RESPOSTA] })
  abrir()
  const grupo = await screen.findByRole('group', { name: 'Nível de ajuda' })
  expect(within(grupo).getAllByRole('button')).toHaveLength(4)
  expect(screen.queryByRole('button', { name: 'Recomeçar' })).toBeNull()
  await userEvent.click(screen.getByRole('button', { name: 'Mais ações' }))
  expect(screen.getByRole('menuitem', { name: 'Recomeçar' })).toBeInTheDocument()
})

test('menu ··· fecha com Esc e devolve o foco ao botão', async () => {
  motor()
  abrir()
  const mais = await screen.findByRole('button', { name: 'Mais ações' })
  await userEvent.click(mais)
  expect(screen.getByRole('menu')).toBeInTheDocument()
  await userEvent.keyboard('{Escape}')
  expect(screen.queryByRole('menu')).toBeNull()
  expect(mais).toHaveFocus()
})

test('pedido que falhou não empilha: o próximo atalho substitui a bolha e o aviso', async () => {
  const SEM_CHAVE = [{ tipo: 'erro', dados: { motivo: 'sem_chave', detalhe: '' } }]
  motor({ respostas: [SEM_CHAVE, SEM_CHAVE] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: 'N1 Dica' }))
  expect(await screen.findByText(/Falta configurar a chave/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'N2 Caminho' }))
  await waitFor(() => expect(pedidos.filter((p) => p.url.includes('/agente/mensagem'))).toHaveLength(2))
  await waitFor(() => expect(screen.getAllByText(/Falta configurar a chave/)).toHaveLength(1))
  expect(screen.queryByText('N1 Dica')).toBeNull()
  expect(screen.getByText('N2 Caminho')).toBeInTheDocument()
})

test('chave recusada oferece o atalho para trocar a chave', async () => {
  motor({ respostas: [[{ tipo: 'erro', dados: { motivo: 'chave_invalida', detalhe: 'API key not valid' } }]] })
  abrir()
  await userEvent.click(await screen.findByRole('button', { name: 'N1 Dica' }))
  expect(await screen.findByRole('link', { name: 'trocar a chave' })).toHaveAttribute('href', '#/m/u1/assistente')
})
