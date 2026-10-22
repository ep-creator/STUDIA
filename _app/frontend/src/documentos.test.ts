import { expect, test, vi } from 'vitest'
import { criarDocumento, nomeArquivo } from './documentos'

test('nome do arquivo vem do título, sem acento', () => {
  expect(nomeArquivo('Regra da Cadeia — 14.5')).toBe('regra-da-cadeia-14-5.md')
  expect(nomeArquivo('???')).toBe('documento.md')
})

test('criar nunca sobrescreve: tenta com sufixo até achar um nome livre', async () => {
  const corpos: Record<string, unknown>[] = []
  vi.stubGlobal('fetch', vi.fn(async (_url: string, init: RequestInit) => {
    const corpo = JSON.parse(init.body as string)
    corpos.push(corpo)
    const ocupado = corpo.nome_arquivo === 'resumo.md' || corpo.nome_arquivo === 'resumo-2.md'
    return ocupado
      ? new Response('{"erro":"Já existe um documento em conteudo/resumos/resumo.md; escolha outro nome."}', { status: 409, headers: { 'content-type': 'application/json' } })
      : new Response('{"id":9}', { status: 200, headers: { 'content-type': 'application/json' } })
  }))
  const id = await criarDocumento('ab', { tipo: 'resumo', titulo: 'Resumo', unidade_id: 2 })
  expect(id).toBe(9)
  expect(corpos.map((c) => c.nome_arquivo)).toEqual(['resumo.md', 'resumo-2.md', 'resumo-3.md'])
  expect(corpos.every((c) => c.versao_esperada === '')).toBe(true)
})
