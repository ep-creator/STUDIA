import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'
import { painel } from '../teste-dados'
import Documentos from './Documentos.svelte'

const resumo = {
  id: 7, tipo: 'resumo', titulo: 'Extremos', caminho: 'conteudo/resumos/extremos.md', unidade_id: 1, secao_id: null,
  questao_id: null, origem: 'manual', atualizado_em: '2026-10-26', secao_decidida: false, secao_codigo: null, secao_posicao: null,
}
const SECAO = { id: 42, livro_id: 1, codigo: '14.7', titulo: 'Valores Máximo e Mínimo', nivel: 2, pagina_pdf_ini: 361, pagina_pdf_fim: 370, origem: 'importado', confianca: 1 }

let pedidos: { metodo: string; url: string; corpo: unknown }[] = []
function motor() {
  pedidos = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init: RequestInit = {}) => {
    const metodo = init.method ?? 'GET'
    pedidos.push({ metodo, url, corpo: init.body ? JSON.parse(String(init.body)) : null })
    const json = (dados: unknown) => new Response(JSON.stringify(dados), { status: 200, headers: { 'content-type': 'application/json' } })
    if (url.endsWith('/fontes')) return json([{ id: 1, tipo: 'livro', titulo: 'Stewart', caminho: 'fontes/livros/s.pdf', paginas: 500 }])
    if (url.endsWith('/fontes/1/secoes')) return json([SECAO])
    if (url.endsWith('/documentos/ligar-secoes')) return json({ ligados: 0 })
    if (url.endsWith('/documentos/7/sugestao-secao')) return json({ secao_id: 42, codigo: '14.7', titulo: 'Valores Máximo e Mínimo', confianca: 0.6, por: 'palavras' })
    if (url.endsWith('/documentos/7/secao')) return json({ ok: true })
    if (url.endsWith('/documentos/7')) return json({ ...resumo, corpo: '# Extremos', versao: 'v1' })
    if (url.includes('/painel')) return json(painel({ documentos: [resumo] }))
    throw new Error(`rota não simulada: ${metodo} ${url}`)
  }))
}
afterEach(() => vi.unstubAllGlobals())

test('ao abrir, liga as seções que faltam uma vez', async () => {
  motor()
  render(Documentos, { painel: painel({ documentos: [resumo] }) })
  await waitFor(() => expect(pedidos.some((p) => p.metodo === 'POST' && p.url.endsWith('/ligar-secoes'))).toBe(true))
})

test('documento sem seção mostra a sugestão e "Sim" liga', async () => {
  motor()
  render(Documentos, { painel: painel({ documentos: [resumo] }) })
  await userEvent.click(await screen.findByRole('button', { name: 'Extremos' }))
  expect(await screen.findByText(/Ligar à seção 14\.7 — Valores Máximo e Mínimo\?/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Sim' }))
  await waitFor(() => expect(pedidos.find((p) => p.metodo === 'PUT' && p.url.endsWith('/documentos/7/secao'))?.corpo).toEqual({ secao_id: 42 }))
})

test('o seletor de seção do cabeçalho troca e remove a seção', async () => {
  motor()
  render(Documentos, { painel: painel({ documentos: [resumo] }) })
  await userEvent.click(await screen.findByRole('button', { name: 'Extremos' }))
  await userEvent.click(await screen.findByRole('button', { name: /^Seção do livro/ }))
  await userEvent.click(screen.getByRole('option', { name: /Sem seção/ }))
  // já estava sem seção: escolher "Sem seção" registra a decisão (a ligação automática passa a respeitar)
  await waitFor(() => expect(pedidos.find((p) => p.metodo === 'PUT' && p.url.endsWith('/documentos/7/secao'))?.corpo).toEqual({ secao_id: null }))
})

test('editando, a seção não pode ser trocada (trocar regravaria o .md e perderia o rascunho)', async () => {
  motor()
  render(Documentos, { painel: painel({ documentos: [resumo] }) })
  await userEvent.click(await screen.findByRole('button', { name: 'Extremos' }))
  expect(await screen.findByText(/Ligar à seção 14\.7/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: /Editar/ }))
  expect(screen.queryByText(/Ligar à seção 14\.7/)).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /^Seção do livro/ })).not.toBeInTheDocument()
})

test('"Resumir a seção" abre o resumidor da seção no painel', async () => {
  const { ia } = await import('../estado/ia.svelte')
  motor()
  const comSecao = { ...resumo, secao_id: 42, secao_codigo: '14.7' }
  render(Documentos, { painel: painel({ documentos: [comSecao] }) })
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const json = (dados: unknown) => new Response(JSON.stringify(dados), { status: 200, headers: { 'content-type': 'application/json' } })
    if (url.endsWith('/documentos/7')) return json({ ...comSecao, corpo: '# Extremos', versao: 'v1' })
    if (url.endsWith('/fontes') || url.endsWith('/secoes')) return json([])
    return json({ ligados: 0 })
  }))
  await userEvent.click(await screen.findByRole('button', { name: 'Extremos' }))
  await userEvent.click(await screen.findByRole('button', { name: /Resumir a seção/ }))
  expect({ aberta: ia.aberta, alvo: ia.alvo, papel: ia.papel, pendente: ia.pendente })
    .toEqual({ aberta: true, alvo: 'secao:42', papel: 'resumidor', pendente: 'resumir' })
})
