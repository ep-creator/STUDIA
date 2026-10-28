import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import MenuMais from './MenuMais.svelte'

test('o menu fecha quando o foco sai dele (Tab adiante), para não ficar aberto invisível', async () => {
  const fora = document.createElement('button')
  fora.textContent = 'depois'
  render(MenuMais, { rotulo: 'Mais ações de X', itens: [{ rotulo: 'Apagar', acao: vi.fn() }] })
  document.body.appendChild(fora)
  await userEvent.click(screen.getByRole('button', { name: 'Mais ações de X' }))
  expect(screen.getByRole('menu')).toBeInTheDocument()
  fora.focus()
  await new Promise((r) => setTimeout(r, 0))
  expect(screen.queryByRole('menu')).toBeNull()
})
