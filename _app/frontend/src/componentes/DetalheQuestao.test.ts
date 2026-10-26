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
