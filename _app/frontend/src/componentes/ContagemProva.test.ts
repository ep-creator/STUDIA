import { render, screen } from '@testing-library/svelte'
import { expect, test } from 'vitest'
import ContagemProva from './ContagemProva.svelte'

const hoje = new Date(2026, 9, 22, 21, 0)
const prova = (data: string) => ({ data, hora_inicio: null })

test('longe da prova: contagem neutra, sem frase do dia', () => {
  render(ContagemProva, { prova: prova('2026-11-16'), hoje })
  expect(screen.getByText('25 dias')).not.toHaveClass('perto')
  expect(screen.queryByText('Boa prova.')).toBeNull()
})

test('com 7 dias ou menos a contagem fica perto', () => {
  render(ContagemProva, { prova: prova('2026-10-29'), hoje })
  expect(screen.getByText('7 dias')).toHaveClass('perto')
})

test('no dia da prova: "hoje" e uma frase curta', () => {
  render(ContagemProva, { prova: prova('2026-10-22'), hoje })
  expect(screen.getByText('hoje')).toHaveClass('perto')
  expect(screen.getByText('Boa prova.')).toBeInTheDocument()
})
