import { render, screen } from '@testing-library/svelte'
import { expect, test, vi } from 'vitest'
import ItemHistorico from './ItemHistorico.svelte'

const G = { id: 5, momento: '2026-10-28T14:32:00', descricao: 'Agente: plano — 3ª unidade', desfaz_grupo: null, desfeito_em: null }

test('desfazer só na mais recente; detalhes como ação de linha', () => {
  render(ItemHistorico, { uid: 'ab', grupo: G, ultimo: false, ondesfazer: vi.fn() })
  expect(screen.queryByRole('button', { name: /desfazer/i })).toBeNull()
  expect(screen.getByRole('button', { name: 'detalhes' }).closest('.acoes-linha')).not.toBeNull()
})

test('a mais recente oferece desfazer como ação de texto sempre visível', () => {
  render(ItemHistorico, { uid: 'ab', grupo: G, ultimo: true, ondesfazer: vi.fn() })
  const desfazer = screen.getByRole('button', { name: /desfazer/i })
  expect(desfazer).toHaveClass('acao-texto')
  expect(desfazer.closest('.acoes-linha')).toBeNull()
})
