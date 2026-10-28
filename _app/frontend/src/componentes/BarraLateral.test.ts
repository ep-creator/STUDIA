import { render, screen } from '@testing-library/svelte'
import { expect, test } from 'vitest'
import BarraLateral from './BarraLateral.svelte'

test('Assistente fica num grupo próprio e marca a página atual', () => {
  render(BarraLateral, { rota: { tela: 'assistente', uid: 'u1' }, materias: [], unidade: 1, pendencias: 0 })
  const link = screen.getByRole('link', { name: 'Assistente' })
  expect(link).toHaveAttribute('href', '#/m/u1/assistente')
  expect(link).toHaveAttribute('aria-current', 'page')
  const grupo = link.closest('ul')!
  expect(grupo.querySelectorAll('a')).toHaveLength(1)
})
