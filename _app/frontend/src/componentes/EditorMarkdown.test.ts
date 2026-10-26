import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import type { DocumentoComCorpo } from '../api/tipos'
import EditorMarkdown from './EditorMarkdown.svelte'

const doc: DocumentoComCorpo = {
  id: 3, tipo: 'resumo', caminho: 'conteudo/resumos/14-3.md', titulo: 'Derivadas parciais', unidade_id: 1, secao_id: null,
  questao_id: null, origem: 'manual', atualizado_em: '2026-09-01T10:00:00', secao_decidida: false, secao_codigo: null, secao_posicao: null, corpo: 'Texto', versao: 'abc',
}

function respostas(...lista: [number, unknown][]) {
  const fila = [...lista]
  vi.stubGlobal('fetch', vi.fn(async () => {
    const [status, corpo] = fila.shift()!
    return new Response(JSON.stringify(corpo), { status, headers: { 'content-type': 'application/json' } })
  }))
}

test('salvar manda a versão aberta e o nome do arquivo', async () => {
  respostas([200, { id: 3 }])
  const onsalvo = vi.fn()
  render(EditorMarkdown, { uid: 'ab', documento: doc, onsalvo, oncancelar: vi.fn() })
  await userEvent.type(screen.getByRole('textbox', { name: 'Texto do documento' }), ' editado')
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }))
  const [url, init] = vi.mocked(fetch).mock.calls[0]
  expect(url).toBe('/api/materias/ab/documentos')
  expect(JSON.parse(init?.body as string)).toMatchObject({
    tipo: 'resumo', nome_arquivo: '14-3.md', titulo: 'Derivadas parciais', corpo: 'Texto editado', versao_esperada: 'abc', unidade_id: 1,
  })
  expect(onsalvo).toHaveBeenCalled()
})

test('conflito ao salvar oferece ver a versão atual sem perder o texto', async () => {
  respostas(
    [409, { erro: 'O documento mudou desde que foi aberto; recarregue para ver a versão atual.' }],
    [200, { ...doc, corpo: 'Mudado por fora', versao: 'def' }],
  )
  render(EditorMarkdown, { uid: 'ab', documento: doc, onsalvo: vi.fn(), oncancelar: vi.fn() })
  await userEvent.type(screen.getByRole('textbox', { name: 'Texto do documento' }), ' editado')
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }))
  expect(await screen.findByRole('button', { name: 'Ver versão atual' })).toBeInTheDocument()
  expect(screen.getByRole('textbox', { name: 'Texto do documento' })).toHaveValue('Texto editado')
  await userEvent.click(screen.getByRole('button', { name: 'Ver versão atual' }))
  expect(await screen.findByText('Mudado por fora')).toBeInTheDocument()
})

test('digitar marca alterações não salvas e salvar limpa', async () => {
  const { haAlteracoes } = await import('../estado/saida')
  respostas([200, { id: 3 }])
  render(EditorMarkdown, { uid: 'ab', documento: doc, onsalvo: vi.fn(), oncancelar: vi.fn() })
  expect(haAlteracoes()).toBe(false)
  await userEvent.type(screen.getByRole('textbox', { name: 'Texto do documento' }), ' novo')
  expect(haAlteracoes()).toBe(true)
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }))
  expect(haAlteracoes()).toBe(false)
})
