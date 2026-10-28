import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import LinhaDoTempo from './LinhaDoTempo.svelte'

const S = { id: 1, unidade_id: 1, codigo: 'S1', data: '2026-08-31', foco_md: '**Fechar o 14.1**\n\nExercícios: 68 + 20, 26, 36', feito: true, ordem: 1, origem: 'manual', questao_ids: [] }

test('foco da sessão em uma linha, feita como selo de texto e ações no hover', async () => {
  const onfeito = vi.fn()
  render(LinhaDoTempo, { itens: [{ data: S.data, hora: null, tipo: 'sessao', sessao: S }], hoje: new Date(2026, 9, 28), onfeito, oneditar: vi.fn() })
  expect(screen.getByText('Fechar o 14.1')).toBeInTheDocument()
  expect(screen.queryByText(/Exercícios: 68/)).toBeNull()
  expect(screen.getByText('feita')).toHaveClass('selo-feita')
  expect(screen.queryByRole('checkbox')).toBeNull()
  const desmarcar = screen.getByRole('button', { name: 'Sessão S1: desmarcar feita' })
  expect(desmarcar.closest('.acoes-linha')).not.toBeNull()
  await userEvent.click(desmarcar)
  expect(onfeito).toHaveBeenCalledWith(S)
})
