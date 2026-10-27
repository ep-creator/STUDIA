import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, test, vi } from 'vitest'
import type { Documento } from '../api/tipos'
import { lista, questao } from '../teste-dados'
import DetalheQuestao from './DetalheQuestao.svelte'

const q = questao(2, '30')
const l = lista(1, '14.1', [q])
const resolucao: Documento = {
  id: 16, tipo: 'resolucao', titulo: 'Resolução 14.1-30', caminho: 'conteudo/resolucoes/14-1-30.md', origem: 'migrado',
  unidade_id: 1, secao_id: null, questao_id: 2, atualizado_em: '2026-10-22', secao_decidida: false,
}

afterEach(() => vi.unstubAllGlobals())

function motor() {
  const chamadas: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    chamadas.push(url)
    if (url.endsWith('/documentos/16')) {
      return new Response(JSON.stringify({ ...resolucao, corpo: 'Passo 1: isole a variável.', versao: 'v1' }), { status: 200, headers: { 'content-type': 'application/json' } })
    }
    throw new Error(`rota não simulada: ${url}`)
  }))
  return chamadas
}

test('a resolução da questão fica escondida até pedir, e aparece no próprio menu', async () => {
  const chamadas = motor()
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, resolucao, onmarcar: vi.fn() })
  expect(screen.queryByText(/isole a variável/)).toBeNull()
  await userEvent.click(screen.getByRole('button', { name: /Ver resolução/ }))
  expect(await screen.findByText(/isole a variável/)).toBeInTheDocument()
  expect(chamadas.some((u) => u.endsWith('/api/materias/u1/documentos/16'))).toBe(true)
})

test('abrir a resolução recolhe a área de IA para dar espaço', async () => {
  motor()
  const { ia } = await import('../estado/ia.svelte')
  ia.aberta = true
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, resolucao, onmarcar: vi.fn() })
  await userEvent.click(screen.getByRole('button', { name: /Ver resolução/ }))
  expect(ia.aberta).toBe(false)
})

test('sem resolução, o menu não oferece o botão', () => {
  motor()
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, resolucao: null, onmarcar: vi.fn() })
  expect(screen.queryByRole('button', { name: /Ver resolução/ })).toBeNull()
})

const SECAO = { secao_id: 31, codigo: '14.1', titulo: 'Funções de várias variáveis', fonte_id: 4, caminho: 'fontes/livros/stewart.pdf', pagina_pdf_ini: 303 }
const exercicio = (extra = {}) => ({
  trecho_id: 9, origem: 'fonte:4', tipo: 'livro', titulo: '14.1 Funções de várias variáveis', trecho: '30. f(x, y) = x² + y²',
  pagina: 312, secao_id: 31, secao_codigo: '14.1', fonte_id: 4, documento_id: null, score: 0, por: 'texto', pagina_fim: 312,
  parte: 'exercicio', numero: 29, ...extra,
})

function motorDoLivro(status: number, corpo: unknown = null) {
  const chamadas: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    chamadas.push(url)
    if (url.includes('/exercicios/')) return new Response(JSON.stringify(corpo ?? { detail: 'não está' }), { status, headers: { 'content-type': 'application/json' } })
    throw new Error(`rota não simulada: ${url}`)
  }))
  return chamadas
}

test('questão que é exercício do livro mostra "Ver no livro" com o enunciado e a resposta', async () => {
  const chamadas = motorDoLivro(200, { exercicio: exercicio(), resposta: { ...exercicio(), parte: 'resposta', trecho: '29. o paraboloide' } })
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  await userEvent.click(await screen.findByRole('button', { name: /Ver no livro/ }))
  expect(chamadas.some((u) => u.endsWith('/api/materias/u1/secoes/31/exercicios/30'))).toBe(true)
  expect(screen.getByText(/x² \+ y²/)).toBeInTheDocument()
  expect(screen.getByText(/o paraboloide/)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /Abrir no livro na p\. 312/ })).toBeInTheDocument()
})

test('sem exercício no índice, "Ver no livro" não aparece', async () => {
  const chamadas = motorDoLivro(404)
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  await vi.waitFor(() => expect(chamadas.length).toBe(1))
  expect(screen.queryByRole('button', { name: /Ver no livro/ })).toBeNull()
})

test('rótulo que não é número, lista de outra seção ou sem seção: nem pergunta ao motor', () => {
  const chamadas = motorDoLivro(200)
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: questao(3, '22a'), marca: null, secao: SECAO, onmarcar: vi.fn() })
  render(DetalheQuestao, { uid: 'u1', lista: lista(2, 'L2', [q]), questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, onmarcar: vi.fn() })
  expect(chamadas).toEqual([])
})
