import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test } from 'vitest'
import type { Documento, FonteResumo } from '../api/tipos'
import ListaDocumentos from './ListaDocumentos.svelte'

const doc = (id: number, tipo: string, titulo: string, origem = 'migrado'): Documento => ({
  id, tipo, titulo, origem, caminho: `${id}.md`, unidade_id: 1, secao_id: null, questao_id: null, atualizado_em: '2026-10-22', secao_decidida: false,
})
const fonte = (id: number, tipo: string, titulo: string): FonteResumo => ({ id, tipo, titulo, caminho: `${id}.pdf`, paginas: 10 })

const props = () => ({
  documentos: [doc(1, 'resumo', '14.2 Limite'), doc(2, 'resumo', '14.1 Funções'), doc(3, 'anotacao', 'Calendário'), doc(4, 'resumo', '14.3 Derivadas', 'agente')],
  fontes: [fonte(9, 'livro', 'Stewart'), fonte(8, 'programa', 'Programa da disciplina')],
  selecao: null,
  onselecionar: () => {},
})

beforeEach(() => localStorage.clear())

test('separa os materiais de estudo dos arquivos da disciplina', () => {
  render(ListaDocumentos, props())
  const estudo = screen.getByRole('region', { name: 'Materiais de estudo' })
  const disciplina = screen.getByRole('region', { name: 'Da disciplina' })
  expect(estudo.textContent).toContain('14.1 Funções')
  expect(estudo.textContent).not.toContain('Stewart')
  expect(disciplina.textContent).toContain('Stewart')
  expect(disciplina.textContent).toContain('Programa da disciplina')
})

test('cada grupo abre e fecha pela setinha, e lembra a escolha', async () => {
  const { unmount } = render(ListaDocumentos, props())
  const resumos = screen.getByRole('button', { name: /Resumos/ })
  expect(resumos).toHaveAttribute('aria-expanded', 'true')
  await userEvent.click(resumos)
  expect(resumos).toHaveAttribute('aria-expanded', 'false')
  expect(screen.queryByText('14.1 Funções')).toBeNull()
  expect(screen.getByText('Calendário')).toBeInTheDocument()
  unmount()
  render(ListaDocumentos, props())
  expect(screen.getByRole('button', { name: /Resumos/ })).toHaveAttribute('aria-expanded', 'false')
})

test('documento criado pela IA ganha o selo IA', () => {
  render(ListaDocumentos, props())
  expect(screen.getByRole('button', { name: /14.3 Derivadas/ }).textContent).toContain('IA')
  expect(screen.getByRole('button', { name: /14.1 Funções/ }).textContent).not.toContain('IA')
})

test('resumos na ordem do livro; sem seção no fim, por nome', () => {
  const comPosicao = (id: number, titulo: string, secao_posicao: number | null): Documento => ({ ...doc(id, 'resumo', titulo), secao_posicao })
  render(ListaDocumentos, {
    ...props(),
    documentos: [comPosicao(1, 'Z primeiro no livro', 3), comPosicao(2, 'B sem seção', null), comPosicao(3, 'Y', 1), comPosicao(4, 'A sem seção', null), comPosicao(5, 'X', 2)],
  })
  const titulos = [...document.querySelectorAll('section[aria-label="Materiais de estudo"] .item')].map((b) => b.textContent?.trim())
  expect(titulos).toEqual(['Y', 'X', 'Z primeiro no livro', 'A sem seção', 'B sem seção'])
})
