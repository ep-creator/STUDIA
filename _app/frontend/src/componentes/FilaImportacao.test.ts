import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import type { ImportacaoSaida } from '../api/tipos'
import { avisos } from '../estado/avisos.svelte'
import FilaImportacao from './FilaImportacao.svelte'

function imp(id: number, fonte_id: number, pendencias: number, tipo = 'lista'): ImportacaoSaida {
  return { id, fonte_id, tipo, estado: 'proposta', proposta: {}, criada_em: '2026-10-22T10:00:00', confirmada_em: null, pendencias }
}

type Rota = (url: string, init: RequestInit) => [number, unknown] | undefined

function motor(...rotas: Rota[]) {
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit = {}) => {
    for (const r of rotas) {
      const resp = r(url, init)
      if (resp) return new Response(JSON.stringify(resp[1]), { status: resp[0], headers: { 'content-type': 'application/json' } })
    }
    throw new Error(`rota não simulada: ${init.method ?? 'GET'} ${url}`)
  }))
}

const fontes: Rota = (url) => (url.endsWith('/fontes') ? [200, [{ id: 1, tipo: 'lista', titulo: 'L1', caminho: 'fontes/listas/Lista1.pdf', paginas: 3 }]] : undefined)

beforeEach(() => {
  avisos.lista = []
})

test('arquivo recusado avisa e a fila continua usável', async () => {
  let envios = 0
  motor(
    fontes,
    (url, init) => (url.includes('/importacoes?') && (init.method ?? 'GET') === 'GET' ? [200, []] : undefined),
    (url, init) => {
      if (init.method !== 'POST' || !url.endsWith('/importacoes')) return undefined
      envios++
      return envios === 1 ? [422, { erro: 'Por enquanto só PDFs podem ser importados.' }] : [201, imp(9, 1, 0, 'programa')]
    },
  )
  const user = userEvent.setup({ applyAccept: false })
  render(FilaImportacao, { uid: 'ab', selecionada: null, onselecionar: vi.fn(), versao: 0 })
  const campo = screen.getByLabelText(/Escolher arquivos/)
  await user.upload(campo, new File(['texto'], 'nota.txt', { type: 'text/plain' }))
  await waitFor(() => expect(avisos.lista.map((a) => a.texto)).toContain('Por enquanto só PDFs podem ser importados.'))
  await user.upload(campo, new File(['%PDF-1.4'], 'Programa.pdf', { type: 'application/pdf' }))
  await waitFor(() => expect(envios).toBe(2))
})

test('confirmar todos só confirma os sem pendências', async () => {
  const confirmados: string[] = []
  motor(
    fontes,
    (url, init) => (url.includes('/importacoes?') && (init.method ?? 'GET') === 'GET' ? [200, [imp(1, 1, 0), imp(2, 1, 2), imp(3, 1, 0)]] : undefined),
    (url, init) => {
      if (init.method !== 'POST' || !url.endsWith('/confirmar')) return undefined
      confirmados.push(url.split('/').at(-2)!)
      return [200, { unidades: 0, topicos: 0, eventos: 0, secoes: 0, listas: 1, questoes: 8, vinculos: 0, criterios: 0, indexacao: 'em segundo plano' }]
    },
  )
  render(FilaImportacao, { uid: 'ab', selecionada: null, onselecionar: vi.fn(), versao: 0 })
  await userEvent.click(await screen.findByRole('button', { name: /Confirmar todos sem pendências \(2\)/ }))
  await waitFor(() => expect(confirmados).toEqual(['1', '3']))
})

test('fila mostra primeiro o que pede revisão, depois por tipo', async () => {
  const fontesVarias: Rota = (url) => (url.endsWith('/fontes') ? [200, [
    { id: 1, tipo: 'slides', titulo: '', caminho: 'fontes/slides/Aula 1.pdf', paginas: 3 },
    { id: 2, tipo: 'livro', titulo: '', caminho: 'fontes/livros/Boulos.pdf', paginas: 300 },
    { id: 3, tipo: 'programa', titulo: '', caminho: 'fontes/documentos/Programa.pdf', paginas: 2 },
    { id: 4, tipo: 'lista', titulo: '', caminho: 'fontes/listas/Lista 1.pdf', paginas: 2 },
  ]] : undefined)
  motor(fontesVarias, (url, init) => (url.includes('/importacoes?') && (init.method ?? 'GET') === 'GET'
    ? [200, [imp(10, 1, 0, 'slides'), imp(11, 2, 1, 'livro'), imp(12, 3, 0, 'programa'), imp(13, 4, 1, 'lista')]] : undefined))
  render(FilaImportacao, { uid: 'ab', selecionada: null, onselecionar: vi.fn(), versao: 0 })
  const lista = await screen.findByRole('list', { name: 'Arquivos esperando revisão' })
  await waitFor(() => expect(lista.querySelectorAll('button')).toHaveLength(4))
  expect([...lista.querySelectorAll('.nome')].map((n) => n.textContent)).toEqual(['Boulos.pdf', 'Lista 1.pdf', 'Programa.pdf', 'Aula 1.pdf'])
})
