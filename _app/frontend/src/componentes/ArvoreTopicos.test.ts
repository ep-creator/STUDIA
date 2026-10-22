import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import { topico } from '../teste-dados'
import ArvoreTopicos from './ArvoreTopicos.svelte'

function okFetch() {
  vi.stubGlobal('fetch', vi.fn(async () => new Response('{"ok":true}', { status: 200, headers: { 'content-type': 'application/json' } })))
}

test('clique no status avança pendente → próxima → visto → pendente', async () => {
  okFetch()
  const onmudou = vi.fn()
  render(ArvoreTopicos, { uid: 'ab', unidadeId: 1, topicos: [topico(1, 'pendente')], vinculos: {}, listasDoTopico: {}, onmudou })
  await userEvent.click(screen.getByRole('button', { name: 'pendente' }))
  const [url, init] = vi.mocked(fetch).mock.calls[0]
  expect(url).toMatch(/\/api\/materias\/ab\/topicos\/1$/)
  expect(init?.method).toBe('PATCH')
  expect(JSON.parse(init?.body as string)).toEqual({ status: 'proxima' })
  expect(onmudou).toHaveBeenCalled()
})

test('subtópicos aparecem dentro do pai e mostram a seção do livro', () => {
  render(ArvoreTopicos, {
    uid: 'ab', unidadeId: 1, listasDoTopico: {}, onmudou: vi.fn(),
    topicos: [topico(1, 'visto', { titulo: 'Integração dupla' }), topico(2, 'pendente', { titulo: 'Polares', pai_id: 1 })],
    vinculos: { '2': [{ secao_id: 9, codigo: '15.4', titulo: 'Polares', fonte_id: 1, caminho: 'fontes/livros/s.pdf', pagina_pdf_ini: 431 }] },
  })
  const pai = screen.getByText('Integração dupla').closest('li')!
  expect(pai).toContainElement(screen.getByText('Polares'))
  expect(screen.getByRole('link', { name: /15\.4/ })).toHaveAttribute('href', '/arquivos/ab/fontes/livros/s.pdf#page=431')
})
