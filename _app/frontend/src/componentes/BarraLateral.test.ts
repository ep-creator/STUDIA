import { render, screen, within } from '@testing-library/svelte'
import { expect, test } from 'vitest'
import BarraLateral from './BarraLateral.svelte'

test('quatro áreas de estudo em cima, o apoio embaixo; a atual marcada', () => {
  render(BarraLateral, { rota: { tela: 'materia', uid: 'u1', unidade: 3, area: 'listas' }, materias: [], unidade: 3, pendencias: 0 })
  const nav = screen.getByRole('navigation', { name: 'Áreas da matéria' })
  const [principais, apoio] = within(nav).getAllByRole('list')
  expect(within(principais).getAllByRole('link').map((a) => a.textContent)).toEqual(['Hoje', 'Tópicos', 'Praticar', 'Biblioteca'])
  expect(within(apoio).getAllByRole('link').map((a) => a.textContent?.trim())).toEqual(['Plano', 'Folha de fórmulas', '＋ Adicionar material', 'Histórico'])
  expect(screen.getByRole('link', { name: 'Praticar' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('link', { name: 'Hoje' })).toHaveAttribute('href', '#/m/u1/u/3/painel')
  expect(screen.queryByRole('link', { name: 'Assistente' })).toBeNull()
})

test('material para conferir aparece como número no ＋ Adicionar material', () => {
  render(BarraLateral, { rota: { tela: 'importar', uid: 'u1' }, materias: [], unidade: null, pendencias: 2 })
  const link = screen.getByRole('link', { name: /Adicionar material, 2 para conferir/ })
  expect(link).toHaveAttribute('href', '#/m/u1/importar')
  expect(link).toHaveAttribute('aria-current', 'page')
})
