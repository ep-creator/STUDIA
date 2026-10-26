import { render, screen } from '@testing-library/svelte'
import { expect, test } from 'vitest'
import SeloConfianca from './SeloConfianca.svelte'

test('mostra o motivo do vínculo quando o sentido contou', () => {
  const { rerender } = render(SeloConfianca, { item: { confianca: 0.8, revisar: false, por: 'sentido' } })
  expect(screen.getByText('pelo sentido')).toBeInTheDocument()
  rerender({ item: { confianca: 0.8, revisar: false, por: 'ambos' } })
  expect(screen.getByText('pelos dois')).toBeInTheDocument()
  rerender({ item: { confianca: 0.8, revisar: false, por: 'palavras' } })
  expect(screen.queryByText(/pelo sentido|pelos dois/)).toBeNull()
})
