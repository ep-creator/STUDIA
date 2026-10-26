import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { pedido } from '../estado/pedido.svelte'
import BuscaMateria from './BuscaMateria.svelte'

type Resultado = Record<string, unknown>
const livro = (extra: Resultado = {}): Resultado => ({
  trecho_id: 1, origem: 'fonte:1', tipo: 'livro', titulo: '15.4 Integrais Duplas em Coordenadas Polares',
  trecho: 'Em [polares], dA = r dr dθ', pagina: 406, secao_id: 7, secao_codigo: '15.4', fonte_id: 1, documento_id: null,
  score: -3, ...extra,
})
const resumo: Resultado = {
  trecho_id: 2, origem: 'documento:9', tipo: 'resumo', titulo: '15.4 Integrais — Mudança para polares',
  trecho: 'Use [polares] quando a região for um disco', pagina: null, secao_id: null, secao_codigo: null, fonte_id: null,
  documento_id: 9, score: -2,
}

let urls: string[] = []
function motor(resultados: Resultado[], avisos: string[] = []) {
  urls = []
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    urls.push(url)
    return new Response(JSON.stringify({ resultados, sincronizacao: { indexadas: 0, removidas: 0, trechos: 10, avisos, tempo_ms: 1 } }),
      { status: 200, headers: { 'content-type': 'application/json' } })
  }))
}

beforeEach(() => {
  pedido.fonte = null
  pedido.documento = null
  pedido.ancora = null
  location.hash = '#/m/ab/u/3/painel'
})
afterEach(() => vi.unstubAllGlobals())

const abrir = (extra = {}) => render(BuscaMateria, { uid: 'ab', unidade: 3, aberta: true, onfechar: vi.fn(), ...extra })

test('digita, mostra resultados agrupados e Enter abre o PDF na página', async () => {
  motor([livro(), resumo])
  abrir()
  await userEvent.type(screen.getByRole('combobox', { name: /Buscar na matéria/ }), 'polares')
  expect(await screen.findByText('Livros', { selector: '.grupo' })).toBeInTheDocument()
  expect(screen.getByText('Textos', { selector: '.grupo' })).toBeInTheDocument()
  expect(screen.getByText(/p\. 406/)).toBeInTheDocument()
  expect(document.querySelector('mark')?.textContent).toBe('polares')
  expect(urls.at(-1)).toContain('q=polares')
  expect(urls.at(-1)).toContain('unidade=3')
  await userEvent.keyboard('{Enter}')
  expect(pedido.fonte).toEqual({ id: 1, pagina: 406 })
  expect(location.hash).toBe('#/m/ab/u/3/documentos')
})

test('abrir um texto pede o documento e a âncora do bloco', async () => {
  motor([resumo])
  abrir()
  await userEvent.type(screen.getByRole('combobox', { name: /Buscar na matéria/ }), 'polares')
  await userEvent.click(await screen.findByRole('option', { name: /Mudança para polares/ }))
  expect(pedido.documento).toBe(9)
  expect(pedido.ancora).toBe('mudanca-para-polares')
})

test('menos de 2 letras ou só palavras vazias não chamam o motor', async () => {
  motor([livro()])
  abrir()
  const campo = screen.getByRole('combobox', { name: /Buscar na matéria/ })
  await userEvent.type(campo, 'a')
  await userEvent.clear(campo)
  await userEvent.type(campo, 'de a o')
  await new Promise((r) => setTimeout(r, 300))
  expect(urls).toHaveLength(0)
})

test('filtro Toda a matéria tira a unidade; filtro Textos manda os tipos de texto', async () => {
  motor([resumo])
  abrir()
  await userEvent.type(screen.getByRole('combobox', { name: /Buscar na matéria/ }), 'polares')
  await screen.findByText('Textos', { selector: '.grupo' })
  await userEvent.click(screen.getByRole('radio', { name: 'Toda a matéria' }))
  await waitFor(() => expect(urls.at(-1)).not.toContain('unidade='))
  await userEvent.click(screen.getByRole('radio', { name: 'Textos' }))
  await waitFor(() => expect(urls.at(-1)).toContain('tipo=resumo'))
  expect(urls.at(-1)).toContain('tipo=resolucao')
  expect(urls.at(-1)).not.toContain('tipo=livro')
})

test('nada encontrado na unidade oferece buscar na matéria toda', async () => {
  motor([])
  abrir()
  await userEvent.type(screen.getByRole('combobox', { name: /Buscar na matéria/ }), 'jacobiano')
  await userEvent.click(await screen.findByRole('button', { name: 'Buscar na matéria toda' }))
  await waitFor(() => expect(urls.at(-1)).not.toContain('unidade='))
})

test('índice sendo montado avisa', async () => {
  motor([], ['sincronização em andamento; resultados podem ainda não incluir tudo'])
  abrir()
  await userEvent.type(screen.getByRole('combobox', { name: /Buscar na matéria/ }), 'polares')
  expect(await screen.findByText(/Montando o índice/)).toBeInTheDocument()
})

test('Esc fecha', async () => {
  motor([])
  const onfechar = vi.fn()
  abrir({ onfechar })
  await userEvent.keyboard('{Escape}')
  expect(onfechar).toHaveBeenCalled()
})
