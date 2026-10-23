import { render, screen } from '@testing-library/svelte'
import { expect, test } from 'vitest'
import { painel, painelVazio, topico } from '../teste-dados'
import Painel from './Painel.svelte'

const hoje = new Date(2026, 8, 2)

test('painel de matéria vazia leva à importação', () => {
  render(Painel, { painel: painelVazio, hoje })
  expect(screen.getByText(/Envie o programa/)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /Importar/ })).toHaveAttribute('href', '#/m/ab/importar')
})

test('contagem, progresso e pendências da unidade', () => {
  render(Painel, {
    hoje,
    painel: painel({
      topicos: [topico(1, 'visto'), topico(2, 'proxima', { titulo: 'Derivadas parciais' }), topico(3, 'pendente')],
      eventos: [{ id: 9, tipo: 'prova', data: '2026-09-14', hora_inicio: '14:30', hora_fim: null, unidade_id: 1, descricao: '', origem: 'importado' }],
      importacoes_pendentes: 2,
    }),
  })
  expect(screen.getByText('12 dias')).toBeInTheDocument()
  expect(screen.getByText(/14:30/)).toBeInTheDocument()
  expect(screen.getByText('1/3')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /Derivadas parciais/ })).toHaveAttribute('href', '#/m/ab/u/1/topicos')
  expect(screen.getByRole('link', { name: /2 importações esperando revisão/ })).toHaveAttribute('href', '#/m/ab/importar')
})

test('para revisar lista as questões ✗ e ? e abre cada uma direto nas listas', async () => {
  const { pedido } = await import('../estado/pedido.svelte')
  const { lista, questao } = await import('../teste-dados')
  render(Painel, {
    hoje,
    painel: painel({
      listas: [lista(1, '14.1', [questao(10, '22'), questao(11, '46'), questao(12, '50')])],
      marcacoes: { '10': 'ok', '11': 'err', '12': 'dub' },
    }),
  })
  const link = screen.getByRole('link', { name: /14\.1 #46/ })
  expect(link).toHaveAttribute('href', '#/m/ab/u/1/listas')
  expect(screen.getByRole('link', { name: /14\.1 #50/ })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: /14\.1 #22/ })).toBeNull()
  link.click()
  expect(pedido.questao).toBe(11)
  // desempenho da lista: 3 de 3 feitas, 1 acerto
  expect(screen.getByText(/3\/3 feitas/)).toBeInTheDocument()
})

test('semana mostra os próximos sete dias, com a prova em destaque', () => {
  render(Painel, {
    hoje,
    painel: painel({ eventos: [{ id: 9, tipo: 'prova', data: '2026-09-04', hora_inicio: '14:30', hora_fim: null, unidade_id: 1, descricao: '', origem: 'importado' }] }),
  })
  const semana = screen.getByRole('region', { name: 'Semana' })
  expect(semana.querySelectorAll('[data-dia]')).toHaveLength(7)
  expect(semana.querySelector('.prova')?.textContent).toMatch(/Prova/)
})
