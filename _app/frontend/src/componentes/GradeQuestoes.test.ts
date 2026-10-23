import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import { lista, questao } from '../teste-dados'
import GradeQuestoes from './GradeQuestoes.svelte'

const lista154 = lista(1, '15.4', [questao(11, '7'), questao(12, '8'), questao(13, '9', { linha: 2 })])

test('teclado: setas navegam e 1/2/3 marcam', async () => {
  const onmarcar = vi.fn()
  const user = userEvent.setup()
  render(GradeQuestoes, { listas: [lista154], marcacoes: {}, selecionada: null, onmarcar, onselecionar: vi.fn() })
  await user.click(screen.getByRole('button', { name: /Questão 15\.4 #7/ }))
  onmarcar.mockClear()
  await user.keyboard('{ArrowRight}2')
  expect(onmarcar).toHaveBeenCalledWith(12, 'err')
  await user.keyboard('3')
  expect(onmarcar).toHaveBeenLastCalledWith(12, 'dub')
})

test('clique alterna a marca e seleciona a questão', async () => {
  const onmarcar = vi.fn()
  const onselecionar = vi.fn()
  render(GradeQuestoes, { listas: [lista154], marcacoes: { '11': 'ok' }, selecionada: null, onmarcar, onselecionar })
  await userEvent.click(screen.getByRole('button', { name: /Questão 15\.4 #7/ }))
  expect(onmarcar).toHaveBeenCalledWith(11, 'err')
  expect(onselecionar).toHaveBeenCalledWith(11)
})

test('lista por seção separa linha 1 e linha 2, com placar', () => {
  render(GradeQuestoes, { listas: [lista154], marcacoes: { '11': 'ok', '12': 'err' }, selecionada: null, onmarcar: vi.fn(), onselecionar: vi.fn() })
  expect(screen.getByText('Linha 1')).toBeInTheDocument()
  expect(screen.getByText('Linha 2')).toBeInTheDocument()
  expect(screen.getByText(/1 ✓ · 1 ✗ · 0 \? · 1 por fazer/)).toBeInTheDocument()
})
