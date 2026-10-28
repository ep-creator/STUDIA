import { render, screen, within } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import SeletorTema from './SeletorTema.svelte'

beforeEach(() => {
  localStorage.clear()
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() })))
})

test('três opções em texto, a ativa marcada, e clicar troca o modo', async () => {
  render(SeletorTema)
  const grupo = screen.getByRole('group', { name: 'Tema' })
  expect(within(grupo).getAllByRole('button').map((b) => b.textContent?.trim())).toEqual(['Claro', 'Escuro', 'Sistema'])
  await userEvent.click(within(grupo).getByRole('button', { name: 'Escuro' }))
  expect(within(grupo).getByRole('button', { name: 'Escuro' })).toHaveAttribute('aria-pressed', 'true')
  expect(within(grupo).getByRole('button', { name: 'Sistema' })).toHaveAttribute('aria-pressed', 'false')
  expect(document.documentElement.dataset.tema).toBe('editorial-escuro')
})
