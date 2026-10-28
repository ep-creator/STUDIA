import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import CartaoFormula from './CartaoFormula.svelte'

const F = { id: 1, unidade_id: 1, secao_id: null, titulo: 'Clairaut', corpo_tex: 'f_xy = f_yx', notas_md: '', ordem: 1, origem: 'manual' }

test('editar fica nas ações da linha e apagar dentro do ···', async () => {
  const onapagar = vi.fn()
  render(CartaoFormula, { formula: F, oneditar: vi.fn(), onapagar })
  expect(screen.getByRole('button', { name: 'Editar Clairaut' }).closest('.acoes-linha')).not.toBeNull()
  expect(screen.queryByRole('button', { name: 'Apagar Clairaut' })).toBeNull()
  await userEvent.click(screen.getByRole('button', { name: 'Mais ações de Clairaut' }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Apagar' }))
  expect(onapagar).toHaveBeenCalled()
})
