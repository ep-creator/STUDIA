import { render, screen } from '@testing-library/svelte'
import { expect, test, vi } from 'vitest'
import CabecalhoProposta from './CabecalhoProposta.svelte'

test('cabeçalho enxuto: tipo e "tipo: lista ⌄", sem Tipo errado? nem o selo de confiança', () => {
  render(CabecalhoProposta, { tipo: 'lista', classificacao: { tipo: 'lista', confianca: 0.93, revisar: false }, ontrocar: vi.fn() })
  expect(screen.getByRole('heading', { name: 'Lista' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /^tipo/ })).toBeInTheDocument()
  expect(screen.queryByText(/Tipo errado/)).toBeNull()
  expect(screen.queryByText(/por quê/)).toBeNull()
  expect(screen.queryByText('conferir')).toBeNull()
})

test('tipo duvidoso mostra conferir em amarelo, com a confiança no title', () => {
  render(CabecalhoProposta, { tipo: 'lista', classificacao: { tipo: 'lista', confianca: 0.55, revisar: true }, ontrocar: vi.fn() })
  const conferir = screen.getByText('conferir')
  expect(conferir).toHaveClass('conferir')
  expect(conferir.getAttribute('title')).toMatch(/confiança 0,55/)
})
