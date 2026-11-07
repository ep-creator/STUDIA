import { render, screen, within } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import type { TopicoPagina as Dados } from '../api/tipos'
import { pedido } from '../estado/pedido.svelte'
import TopicoPagina from './TopicoPagina.svelte'

const secao = { secao_id: 4, codigo: '15.4', titulo: 'Polares', fonte_id: 2, caminho: 'fontes/livros/s.pdf', pagina_pdf_ini: 412 }

function dados(extra: Partial<Dados> = {}): Dados {
  return {
    topico: { id: 13, titulo: 'Integrais em polares', estado: 'em dia', secoes: ['15.4'], total: 3, trabalhadas: 2, ok: 1, err: 1, dub: 0, ultima_aula: '2026-10-31' },
    unidade: 3, secoes: [secao],
    resumos: [{ id: 40, titulo: '15.4 Integrais em polares' }],
    formulas: [{ id: 7, unidade_id: 3, secao_id: 4, titulo: 'Área polar', corpo_tex: 'A = \\int r', notas_md: 'ARMADILHA: r dr', ordem: 1, origem: 'manual' }],
    listas: [{ id: 11, codigo: '15.4', titulo: 'Integrais em polares', unidade: 3, questoes: [
      { id: 1, rotulo: '7', estado: 'err', resolucao_id: null, trabalhada: true },
      { id: 2, rotulo: '8', estado: null, resolucao_id: 52, trabalhada: true },
      { id: 3, rotulo: '9', estado: null, resolucao_id: null, trabalhada: false },
    ] }],
    resolucoes: [{ id: 52, questao_id: 2, rotulo: '15.4 #8' }],
    ...extra,
  }
}

let resposta: Dados
beforeEach(() => {
  resposta = dados()
  pedido.questao = null
  pedido.documento = null
  pedido.fonte = null
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const corpo = url.includes('/documentos/') ? { id: 40, titulo: 'r', corpo: 'Em polares, **dA = r dr dθ**.' } : resposta
    return new Response(JSON.stringify(corpo), { headers: { 'content-type': 'application/json' } })
  }))
})
afterEach(() => vi.unstubAllGlobals())

test('o resumo no centro; seção, estado e o que revisar no cabeçalho', async () => {
  render(TopicoPagina, { uid: 'ab', topico: 13, versao: 1 })
  expect(await screen.findByRole('heading', { level: 1, name: 'Integrais em polares' })).toBeInTheDocument()
  expect(await screen.findByText('dA = r dr dθ')).toBeInTheDocument()
  expect(screen.getByText('2 de 3 questões feitas')).toBeInTheDocument()
  expect(screen.getByText('1 para revisar')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: '15.4 no livro, página 412' }))
  expect(pedido.fonte).toEqual({ id: 2, pagina: 412 })
  expect(location.hash).toBe('#/m/ab/u/3/documentos')
})

test('fórmulas com as notas, questões com as marcações e resoluções', async () => {
  render(TopicoPagina, { uid: 'ab', topico: 13, versao: 1 })
  const formulas = await screen.findByRole('region', { name: 'Fórmulas' })
  expect(formulas).toHaveTextContent('Área polar')
  expect(formulas).toHaveTextContent('ARMADILHA')
  const questoes = screen.getByRole('region', { name: 'Questões' })
  await userEvent.click(within(questoes).getByRole('button', { name: '15.4 #7, errei' }))
  expect(location.hash).toBe('#/m/ab/u/3/listas/1')
  await userEvent.click(within(screen.getByRole('region', { name: 'Resoluções gravadas' })).getByRole('button', { name: '15.4 #8' }))
  expect(pedido.documento).toBe(52)
})

test('sem resumo: diz e aponta para a Biblioteca', async () => {
  resposta = dados({ resumos: [] })
  render(TopicoPagina, { uid: 'ab', topico: 13, versao: 1 })
  expect(await screen.findByText('Este tópico ainda não tem resumo.')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Abrir a Biblioteca' })).toHaveAttribute('href', '#/m/ab/u/3/documentos')
})

test('mais de um resumo vira abas', async () => {
  resposta = dados({ resumos: [{ id: 40, titulo: '15.4 Polares' }, { id: 41, titulo: '15.5 Aplicações' }] })
  render(TopicoPagina, { uid: 'ab', topico: 13, versao: 1 })
  const abas = await screen.findByRole('tablist', { name: 'Resumos do tópico' })
  expect(within(abas).getByRole('tab', { name: '15.4 Polares' })).toHaveAttribute('aria-selected', 'true')
})

test('praticar o tópico começa pela primeira questão ainda não trabalhada', async () => {
  render(TopicoPagina, { uid: 'ab', topico: 13, versao: 1 })
  await userEvent.click(await screen.findByRole('button', { name: 'Praticar: começar pela 15.4 #9' }))
  expect(location.hash).toBe('#/m/ab/u/3/listas/3')
})
