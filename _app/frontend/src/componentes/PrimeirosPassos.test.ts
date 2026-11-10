import { render, screen, within } from '@testing-library/svelte'
import { expect, test } from 'vitest'
import PrimeirosPassos from './PrimeirosPassos.svelte'

test('matéria vazia: três passos (o que soltar e o que vira) e um botão para começar', () => {
  render(PrimeirosPassos, { hrefImportar: '#/m/ab/importar' })
  const passos = screen.getByRole('region', { name: 'Primeiros passos' })
  const itens = within(passos).getAllByRole('listitem')
  expect(itens).toHaveLength(3)
  expect(itens[0]).toHaveTextContent('O programa da disciplina vira as unidades e os tópicos')
  expect(itens[1]).toHaveTextContent('calendário')
  expect(within(passos).getByRole('link', { name: '＋ Adicionar material' })).toHaveAttribute('href', '#/m/ab/importar')
})
