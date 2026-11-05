import { render, screen, waitFor, within } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import type { Hoje as DadosHoje } from '../api/tipos'
import { pedido } from '../estado/pedido.svelte'
import { painel, painelVazio } from '../teste-dados'
import Hoje from './Hoje.svelte'

const secao = { secao_id: 5, codigo: '15.5', titulo: 'Aplicações', fonte_id: 2, caminho: 'fontes/livros/s.pdf', pagina_pdf_ini: 1012 }

function dados(extra: Partial<DadosHoje> = {}): DadosHoje {
  return {
    data: '2026-11-05', unidade: 3, reta_final: false,
    prova: { data: '2026-11-30', hora_inicio: null, unidade: 3, dias: 25 },
    sessao: {
      id: 1, codigo: 'S3', data: '2026-11-05', unidade: 3, titulo: '15.5 Aplicações', detalhe: 'massa, centro de massa',
      estado: 'hoje', secoes: [secao],
      resumos: [{ id: 40, titulo: '15.5 Aplicações de Integrais Duplas' }],
      formulas: [{ id: 7, titulo: 'Massa de uma lâmina (15.5)' }, { id: 8, titulo: 'Momentos (15.5)' }],
      questoes: [
        { id: 159, rotulo: '11', lista_id: 12, lista_codigo: '15.5', unidade: 3, estado: null, resolucao_id: 52 },
        { id: 160, rotulo: '18', lista_id: 12, lista_codigo: '15.5', unidade: 3, estado: null, resolucao_id: null },
        { id: 201, rotulo: '8', lista_id: 19, lista_codigo: 'L5', unidade: 3, estado: 'err', resolucao_id: null },
      ],
    },
    proximos: [
      { tipo: 'sessao', data: '2026-11-05', hora_inicio: null, codigo: 'S3', titulo: '15.5 Aplicações', estado: 'hoje', unidade: 3 },
      { tipo: 'sessao', data: '2026-11-07', hora_inicio: null, codigo: 'S4', titulo: 'Triplas', estado: 'futura', unidade: 3 },
      { tipo: 'prova', data: '2026-11-12', hora_inicio: '14:00', codigo: null, titulo: '', estado: null, unidade: 3 },
    ],
    revisar: [
      { lista_id: 1, lista_codigo: '14.1', lista_titulo: 'Funções', unidade: 1, questoes: [{ id: 4, rotulo: '46', estado: 'err' }] },
    ],
    topicos: [
      { id: 13, titulo: 'Integrais em polares', estado: 'visto', secoes: ['15.4'], total: 13, trabalhadas: 4, ok: 0, err: 1, dub: 0 },
      { id: 14, titulo: 'Aplicações', estado: 'hoje', secoes: ['15.5'], total: 4, trabalhadas: 0, ok: 0, err: 0, dub: 0 },
      { id: 19, titulo: 'Aula extra', estado: 'a seguir', secoes: [], total: 0, trabalhadas: 0, ok: 0, err: 0, dub: 0 },
    ],
    ...extra,
  }
}

let resposta: DadosHoje
beforeEach(() => {
  resposta = dados()
  pedido.questao = null
  pedido.documento = null
  pedido.fonte = null
  location.hash = '#/m/ab/u/3/painel'
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(resposta), { headers: { 'content-type': 'application/json' } })))
})
afterEach(() => vi.unstubAllGlobals())

const p3 = painel({ unidade: 3, unidade_atual: 3 })

test('a sessão de hoje é o foco, com o material a um clique', async () => {
  render(Hoje, { painel: p3 })
  const sessao = await screen.findByRole('region', { name: /Sessão de hoje/ })
  expect(within(sessao).getByRole('heading', { name: '15.5 Aplicações' })).toBeInTheDocument()
  expect(sessao).toHaveTextContent('massa, centro de massa')
  await userEvent.click(within(sessao).getByRole('button', { name: /15\.5 no livro/ }))
  expect(pedido.fonte).toEqual({ id: 2, pagina: 1012 })
  expect(location.hash).toBe('#/m/ab/u/3/documentos')
  await userEvent.click(within(sessao).getByRole('button', { name: /Resumo/ }))
  expect(pedido.documento).toBe(40)
  expect(within(sessao).getByRole('link', { name: /2 fórmulas/ })).toHaveAttribute('href', '#/m/ab/u/3/formulario')
})

test('questões da sessão por lista; clicar abre em Praticar', async () => {
  render(Hoje, { painel: p3 })
  const sessao = await screen.findByRole('region', { name: /Sessão de hoje/ })
  const q18 = within(sessao).getByRole('button', { name: '15.5 #18' })
  await userEvent.click(q18)
  expect(pedido.questao).toBe(160)
  expect(location.hash).toBe('#/m/ab/u/3/listas')
  expect(within(sessao).getByRole('button', { name: /L5 #8, errei/ })).toBeInTheDocument()
  expect(within(sessao).getByRole('button', { name: /15\.5 #11, resolução gravada/ })).toBeInTheDocument()
})

test('Começar pelas questões abre a primeira ainda não trabalhada', async () => {
  render(Hoje, { painel: p3 })
  await userEvent.click(await screen.findByRole('button', { name: 'Começar pelas questões' }))
  expect(pedido.questao).toBe(160)
})

test('para revisar junta todas as unidades e abre na unidade certa', async () => {
  render(Hoje, { painel: p3 })
  const revisar = await screen.findByRole('region', { name: 'Para revisar' })
  expect(revisar).toHaveTextContent('1ª unidade')
  await userEvent.click(within(revisar).getByRole('button', { name: '14.1 #46, errei' }))
  expect(pedido.questao).toBe(4)
  expect(location.hash).toBe('#/m/ab/u/1/listas')
})

test('próximos 7 dias e tópicos com estado derivado', async () => {
  render(Hoje, { painel: p3 })
  const proximos = await screen.findByRole('region', { name: 'Próximos 7 dias' })
  expect(proximos).toHaveTextContent('S4')
  expect(proximos).toHaveTextContent('Prova')
  expect(within(proximos).getByRole('link', { name: /Plano completo/ })).toHaveAttribute('href', '#/m/ab/u/3/cronograma')
  const topicos = screen.getByRole('region', { name: /Tópicos da 3ª unidade/ })
  expect(topicos).toHaveTextContent('Integrais em polares')
  expect(topicos).toHaveTextContent('4/13')
  expect(within(topicos).getByText('hoje')).toBeInTheDocument()
})

test('prova da unidade no cabeçalho; reta final só com 7 dias ou menos', async () => {
  render(Hoje, { painel: p3 })
  expect(await screen.findByText(/Prova da 3ª unidade em 25 dias/)).toBeInTheDocument()
  expect(screen.queryByRole('region', { name: /Reta final/ })).toBeNull()
})

test('reta final: dias, o que revisar e a folha de fórmulas', async () => {
  resposta = dados({ reta_final: true, prova: { data: '2026-11-08', hora_inicio: null, unidade: 3, dias: 3 } })
  render(Hoje, { painel: p3 })
  const reta = await screen.findByRole('region', { name: /Reta final/ })
  expect(reta).toHaveTextContent('3 dias')
  expect(reta).toHaveTextContent('1 questão para revisar')
  expect(within(reta).getByRole('link', { name: /Folha de fórmulas/ })).toBeInTheDocument()
})

test('sem sessão no plano: frase curta e o caminho para o plano', async () => {
  resposta = dados({ sessao: null, proximos: [] })
  render(Hoje, { painel: p3 })
  expect(await screen.findByText(/Nenhuma sessão marcada/)).toBeInTheDocument()
})

test('matéria vazia leva a adicionar material', async () => {
  resposta = dados({ unidade: null, prova: null, sessao: null, proximos: [], revisar: [], topicos: [] })
  render(Hoje, { painel: painelVazio })
  await waitFor(() => expect(screen.getByRole('link', { name: /Adicionar material/ })).toHaveAttribute('href', '#/m/ab/importar'))
})
