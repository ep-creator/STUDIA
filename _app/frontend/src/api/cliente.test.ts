import { expect, test, vi } from 'vitest'
import { ErroApi, MotorDesligado, requisitar, urlArquivo } from './cliente'

function respostaFetch(status: number, corpo: unknown) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(corpo), {
    status, headers: { 'content-type': 'application/json' },
  })))
}

test('erro do motor vira ErroApi com a mensagem', async () => {
  respostaFetch(422, { erro: 'Dados inválidos — nome: obrigatório' })
  await expect(requisitar('POST', '/api/materias', {})).rejects.toMatchObject({
    status: 422, message: 'Dados inválidos — nome: obrigatório',
  })
  await expect(requisitar('POST', '/api/materias', {})).rejects.toBeInstanceOf(ErroApi)
})

test('falha de rede vira MotorDesligado', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('Failed to fetch') }))
  await expect(requisitar('GET', '/api/materias')).rejects.toBeInstanceOf(MotorDesligado)
})

test('resposta ok devolve o JSON e manda corpo como JSON', async () => {
  respostaFetch(200, [{ uid: 'ab' }])
  expect(await requisitar('GET', '/api/materias')).toEqual([{ uid: 'ab' }])
  respostaFetch(201, { uid: 'cd', nome: 'X' })
  await requisitar('POST', '/api/materias', { nome: 'X' })
  const [, init] = vi.mocked(fetch).mock.calls[0]
  expect(init?.body).toBe('{"nome":"X"}')
  expect(new Headers(init?.headers).get('content-type')).toBe('application/json')
})

test('FormData vai sem content-type manual', async () => {
  respostaFetch(201, { id: 1 })
  const dados = new FormData()
  dados.append('arquivo', new Blob(['%PDF']), 'a.pdf')
  await requisitar('POST', '/api/materias/ab/importacoes', dados)
  const [, init] = vi.mocked(fetch).mock.calls[0]
  expect(init?.body).toBe(dados)
  expect(new Headers(init?.headers).has('content-type')).toBe(false)
})

test('urlArquivo com página', () => {
  expect(urlArquivo('ab', 'fontes/livros/s t.pdf', 433)).toBe('/arquivos/ab/fontes/livros/s%20t.pdf#page=433')
  expect(urlArquivo('ab', 'fontes/a.pdf')).toBe('/arquivos/ab/fontes/a.pdf')
})
