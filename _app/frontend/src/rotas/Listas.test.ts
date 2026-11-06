import { render, screen, within } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import type { Documento, Sessao } from '../api/tipos'
import { lista, painel, questao } from '../teste-dados'
import Listas from './Listas.svelte'

// Praticar dentro de uma sessão do plano: a faixa, a ordem da sessão e o fechamento
const l155 = lista(12, '15.5', [questao(1, '11'), questao(2, '12'), questao(3, '18')])
const l5 = lista(19, 'L5', [questao(4, '8', { lista_id: 19 }), questao(5, '9', { lista_id: 19 })])
const sessao = (id: number, codigo: string, data: string, questao_ids: number[], foco = `**${codigo} foco**`): Sessao => ({
  id, unidade_id: 1, codigo, data, foco_md: foco, feito: false, ordem: id, origem: 'manual', questao_ids,
})
const S3 = sessao(1, 'S3', '2026-11-05', [3, 5], '**15.5 Aplicações** — massa')
const S4 = sessao(2, 'S4', '2026-11-07', [2], '**Triplas**')
const daIA: Documento = {
  id: 70, tipo: 'resolucao', titulo: 'Resolução 15.5-18', caminho: 'conteudo/resolucoes/15-5-18.md', origem: 'agente',
  unidade_id: 1, secao_id: null, questao_id: 3, atualizado_em: '2026-11-04', secao_decidida: false,
}

beforeEach(() => {
  location.hash = '#/m/ab/u/1/listas'
  // o detalhe da questão pergunta à IA e ao livro: aqui só interessa a navegação
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ detail: 'x' }), { status: 404, headers: { 'content-type': 'application/json' } })))
})
afterEach(() => vi.unstubAllGlobals())

test('vindo da sessão: faixa com as questões dela, abre a primeira ainda por fazer', async () => {
  render(Listas, { painel: painel({ listas: [l155, l5], sessoes: [S3, S4], marcacoes: {} }), sessao: 1 })
  const faixa = screen.getByRole('region', { name: 'Sessão S3' })
  expect(faixa).toHaveTextContent('15.5 Aplicações')
  expect(within(faixa).getAllByRole('button').map((b) => b.getAttribute('aria-label'))).toEqual(['15.5 #18', 'L5 #9'])
  expect(faixa).toHaveTextContent('0 de 2')
  expect(await screen.findByRole('heading', { level: 2, name: '15.5 #18' })).toBeInTheDocument()
})

test('próxima anda pela sessão, não pela grade', async () => {
  render(Listas, { painel: painel({ listas: [l155, l5], sessoes: [S3, S4] }), sessao: 1, questao: 3 })
  await userEvent.click(await screen.findByRole('button', { name: 'Próxima ›' }))
  expect(screen.getByRole('heading', { level: 2, name: 'L5 #9' })).toBeInTheDocument()   // na grade viria a L5 #8, que não é da sessão
  expect(screen.queryByRole('button', { name: 'Próxima ›' })).toBeNull()                 // a última da sessão
})

test('N vai para a que falta da sessão; a resolução da IA não conta como feita', async () => {
  render(Listas, { painel: painel({ listas: [l155, l5], sessoes: [S3, S4], marcacoes: { '5': 'ok' }, documentos: [daIA] }), sessao: 1, questao: 5 })
  const faixa = screen.getByRole('region', { name: 'Sessão S3' })
  expect(faixa).toHaveTextContent('1 de 2')                       // a 18 tem só a resolução da IA: falta
  await userEvent.keyboard('n')
  expect(screen.getByRole('heading', { level: 2, name: '15.5 #18' })).toBeInTheDocument()
})

test('sessão feita: diz qual é a próxima do plano e leva de volta para Hoje', () => {
  render(Listas, { painel: painel({ listas: [l155, l5], sessoes: [S3, S4], marcacoes: { '3': 'ok', '5': 'err' } }), sessao: 1, questao: 5 })
  const faixa = screen.getByRole('region', { name: 'Sessão S3' })
  expect(faixa).toHaveTextContent('Sessão feita')
  expect(faixa).toHaveTextContent('Próxima: S4 Triplas')
  expect(within(faixa).getByRole('link', { name: 'Voltar para Hoje' })).toHaveAttribute('href', '#/m/ab/u/1/painel')
  expect(within(faixa).getByRole('link', { name: 'sair da sessão' })).toHaveAttribute('href', '#/m/ab/u/1/listas/5')
})

test('sem sessão no endereço: nenhuma faixa', () => {
  render(Listas, { painel: painel({ listas: [l155, l5], sessoes: [S3] }), questao: 1 })
  expect(screen.queryByRole('region', { name: /Sessão/ })).toBeNull()
})
