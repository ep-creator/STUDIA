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
