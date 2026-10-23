import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import Seletor from './Seletor.svelte'

const opcoes = [{ valor: 'editorial', rotulo: 'Editorial' }, { valor: 'padrao', rotulo: 'Padrão' }]

test('abre, mostra as opções e escolhe com o mouse', async () => {
  const onmudar = vi.fn()
  render(Seletor, { rotulo: 'Identidade visual', opcoes, valor: 'editorial', onmudar })
  const botao = screen.getByRole('button', { name: /Identidade visual/ })
  expect(botao).toHaveTextContent('Editorial')
  await userEvent.click(botao)
  expect(screen.getByRole('option', { name: 'Editorial' })).toHaveAttribute('aria-selected', 'true')
  await userEvent.click(screen.getByRole('option', { name: 'Padrão' }))
  expect(onmudar).toHaveBeenCalledWith('padrao')
  expect(screen.queryByRole('listbox')).toBeNull()
})

test('teclado: seta abre e anda, Enter escolhe, Esc fecha sem mudar', async () => {
  const onmudar = vi.fn()
  const user = userEvent.setup()
  render(Seletor, { rotulo: 'Identidade visual', opcoes, valor: 'editorial', onmudar })
  screen.getByRole('button', { name: /Identidade visual/ }).focus()
  await user.keyboard('{ArrowDown}')
  expect(screen.getByRole('listbox')).toBeInTheDocument()
  await user.keyboard('{Escape}')
  expect(screen.queryByRole('listbox')).toBeNull()
  expect(onmudar).not.toHaveBeenCalled()
  await user.keyboard('{ArrowDown}{ArrowDown}{Enter}')
  expect(onmudar).toHaveBeenCalledWith('padrao')
})

test('clique fora fecha', async () => {
  render(Seletor, { rotulo: 'Tipo', opcoes, valor: 'editorial', onmudar: vi.fn() })
  await userEvent.click(screen.getByRole('button', { name: /Tipo/ }))
  await userEvent.click(document.body)
  expect(screen.queryByRole('listbox')).toBeNull()
})
