import { fireEvent, render, screen } from '@testing-library/svelte'
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

test('a resolução fica escondida até abrir a aba Resolução', async () => {
  const chamadas = motor()
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, resolucao, onmarcar: vi.fn() })
  expect(screen.queryByText(/isole a variável/)).toBeNull()
  await userEvent.click(screen.getByRole('tab', { name: 'Sua resolução' }))
  expect(await screen.findByText(/isole a variável/)).toBeInTheDocument()
  expect(chamadas.some((u) => u.endsWith('/api/materias/u1/documentos/16'))).toBe(true)
})

test('abrir a resolução não fecha a gaveta da IA', async () => {
  motor()
  const { ia } = await import('../estado/ia.svelte')
  ia.aberta = true
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, resolucao, onmarcar: vi.fn() })
  await userEvent.click(screen.getByRole('tab', { name: 'Sua resolução' }))
  expect(ia.aberta).toBe(true)
})

test('sem Limpar: clicar na marca ativa desmarca, clicar em outra troca', async () => {
  motor()
  const onmarcar = vi.fn()
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: 'ok', secao: null, onmarcar })
  expect(screen.queryByRole('button', { name: /Limpar/ })).toBeNull()
  await userEvent.click(screen.getByRole('button', { name: /Acertei/ }))
  expect(onmarcar).toHaveBeenLastCalledWith(q.id, null)
  await userEvent.click(screen.getByRole('button', { name: /Errei/ }))
  expect(onmarcar).toHaveBeenLastCalledWith(q.id, 'err')
})

test('sem resolução, não há a aba', () => {
  motor()
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, resolucao: null, onmarcar: vi.fn() })
  expect(screen.queryByRole('tab', { name: 'Sua resolução' })).toBeNull()
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

test('exercício do livro: a própria página do livro no lugar do texto extraído; a resposta numa aba', async () => {
  const chamadas = motorDoLivro(200, { exercicio: exercicio(), resposta: { ...exercicio(), parte: 'resposta', trecho: '29. o paraboloide', pagina: 980 } })
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  // o exercício recortado da página (o motor corta do "30." até o seguinte); a página inteira fica a um link
  const recorte = await screen.findByAltText('Exercício 30 do livro, recortado da página 312')
  expect(recorte.getAttribute('src')).toBe('/api/materias/u1/secoes/31/exercicios/30/recorte')
  expect(screen.getByRole('link', { name: /página inteira/ }).getAttribute('href')).toMatch(/stewart\.pdf#page=312/)
  expect(chamadas.some((u) => u.endsWith('/api/materias/u1/secoes/31/exercicios/30'))).toBe(true)
  expect(screen.queryByText(/x² \+ y²/)).toBeNull()          // o texto extraído (quebrado em livros de cálculo) não aparece
  await userEvent.click(screen.getByRole('tab', { name: 'Resposta do livro' }))
  expect(screen.getByAltText(/Resposta do exercício 30/).getAttribute('src')).toMatch(/exercicios\/30\/recorte\?parte=resposta$/)
})

test('sem recorte (rótulo não achado), a página inteira do livro no lugar', async () => {
  motorDoLivro(200, { exercicio: exercicio(), resposta: null })
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  const recorte = await screen.findByAltText(/Exercício 30 do livro/)
  await fireEvent.error(recorte)
  expect(screen.getByTitle('Página 312 do livro, com o exercício 30').getAttribute('src')).toMatch(/#page=312&toolbar=0/)
})

test('resposta do livro sem página: o trecho em texto', async () => {
  motorDoLivro(200, { exercicio: exercicio(), resposta: { ...exercicio(), parte: 'resposta', trecho: '29. o paraboloide', pagina: null } })
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  await userEvent.click(await screen.findByRole('tab', { name: 'Resposta do livro' }))
  expect(screen.getByText(/o paraboloide/)).toBeInTheDocument()
})

test('resolução da IA tem nome próprio; o prefixo "[Sessão …]" sai do enunciado', async () => {
  motor()
  const comPrefixo = { ...questao(2, '1'), enunciado_md: '[Sessão S4] Calcule a integral.' }
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: comPrefixo, marca: null, secao: null, onmarcar: vi.fn(),
    resolucao: { ...resolucao, origem: 'agente' } })
  expect(screen.getByText('Calcule a integral.')).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: 'Resolução da IA' })).toBeInTheDocument()
})

test('sem o exercício no índice, não há link solto para a página da seção', async () => {
  motorDoLivro(404)
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  expect(screen.queryByRole('link', { name: /Abrir o livro/ })).toBeNull()
})

test('sem exercício no índice, não aparece enunciado do livro nem a aba da resposta', async () => {
  const chamadas = motorDoLivro(404)
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  await vi.waitFor(() => expect(chamadas.filter((u) => u.includes('/exercicios/')).length).toBe(1))
  await vi.waitFor(() => expect(screen.queryByText(/Procurando/)).toBeNull())
  expect(screen.queryByRole('tab', { name: 'Resposta do livro' })).toBeNull()
})

test('rótulo que não é número, lista de outra seção ou sem seção: nem pergunta ao motor', () => {
  const chamadas = motorDoLivro(200)
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: questao(3, '22a'), marca: null, secao: SECAO, onmarcar: vi.fn() })
  render(DetalheQuestao, { uid: 'u1', lista: lista(2, 'L2', [q]), questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, onmarcar: vi.fn() })
  expect(chamadas.filter((u) => u.includes('/exercicios/'))).toEqual([])
})

test('o painel do tutor recebe a questão aberta e os atalhos N1–N4', async () => {
  const chamadas: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    chamadas.push(url)
    const json = (d: unknown) => new Response(JSON.stringify(d), { status: 200, headers: { 'content-type': 'application/json' } })
    if (url.includes('/agente/conversa')) return json({ id: 1, alvo: 'questao:2', papel: 'tutor', mensagens: [] })
    if (url.endsWith('/api/agente/estado')) return json({ chave_configurada: true, modelo: 'g', total_mes: 0, teto: 20 })
    throw new Error(`rota não simulada: ${url}`)
  }))
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, onmarcar: vi.fn() })
  for (const nome of ['N1 Dica', 'N2 Caminho', 'N3 Esboço', 'N4 Resolução']) {
    expect(await screen.findByRole('button', { name: nome })).toBeInTheDocument()
  }
  expect(chamadas.some((u) => u.includes('/agente/conversa?alvo=questao%3A2&papel=tutor'))).toBe(true)
})

test('enquanto procura no livro, uma linha já ocupa o lugar, para a tela não pular', async () => {
  let responder!: (r: Response) => void
  vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>((r) => { responder = r })))
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: SECAO, onmarcar: vi.fn() })
  expect(screen.getByText('Procurando o exercício no livro…')).toBeInTheDocument()
  responder(new Response(JSON.stringify({ exercicio: exercicio(), resposta: null }), { status: 200, headers: { 'content-type': 'application/json' } }))
  expect(await screen.findByAltText(/Exercício 30 do livro/)).toBeInTheDocument()
  expect(screen.queryByText(/Procurando/)).toBeNull()
})

test('o enunciado vem antes da marcação; anterior e próxima andam pela lista', async () => {
  motor()
  const onproxima = vi.fn()
  const onanterior = vi.fn()
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: questao(2, '30', { enunciado_md: 'Esboce o domínio de $f$.' }), marca: null, secao: null, onmarcar: vi.fn(), onproxima, onanterior })
  const enunciado = screen.getByText(/Esboce o domínio/)
  const marcas = screen.getByRole('group', { name: 'Marcar questão' })
  expect(enunciado.compareDocumentPosition(marcas) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  await userEvent.click(screen.getByRole('button', { name: 'Próxima ›' }))
  await userEvent.click(screen.getByRole('button', { name: '‹ Anterior' }))
  expect(onproxima).toHaveBeenCalledOnce()
  expect(onanterior).toHaveBeenCalledOnce()
})

test('fórmulas da seção numa aba própria', async () => {
  motor()
  const formula = { id: 7, unidade_id: 1, secao_id: 31, titulo: 'Área polar', corpo_tex: 'A = r', notas_md: '', ordem: 1, origem: 'manual' }
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, onmarcar: vi.fn(), formulas: [formula] })
  await userEvent.click(screen.getByRole('tab', { name: 'Fórmulas (1)' }))
  expect(screen.getByRole('tabpanel')).toHaveTextContent('Área polar')
})

test('questão de lista da turma: o recorte do PDF da lista é o enunciado; sem recorte, o texto e o link da lista', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    if (url.endsWith('/fontes')) return new Response(JSON.stringify([{ id: 7, tipo: 'lista', titulo: 'Lista 6', caminho: 'fontes/listas/Lista6.pdf', paginas: 3 }]), { status: 200, headers: { 'content-type': 'application/json' } })
    throw new Error(`rota não simulada: ${url}`)
  }))
  const l6 = lista(9, 'L6', [], { fonte_id: 7, titulo: 'Lista 6' })
  const q1 = { ...questao(250, '1'), enunciado_md: '**[Sessão S4]** Calcule a integral no paralelepípedo.' }
  render(DetalheQuestao, { uid: 'u1', lista: l6, questao: q1, marca: null, secao: null, onmarcar: vi.fn() })
  const recorte = screen.getByAltText(/Questão 1 da Lista 6, recortada do PDF da lista/)
  expect(recorte.getAttribute('src')).toBe('/api/materias/u1/questoes/250/recorte')
  expect(screen.queryByText('Calcule a integral no paralelepípedo.')).toBeNull()        // o recorte é o enunciado
  await fireEvent.error(recorte)
  expect(screen.getByText('Calcule a integral no paralelepípedo.')).toBeInTheDocument() // sem recorte, o texto guardado
  expect((await screen.findByRole('link', { name: /Ver na lista \(PDF\)/ })).getAttribute('href')).toMatch(/Lista6\.pdf$/)
})

test('com resolução gravada, o nível Resolução (pago) sai do seletor: a gravada está na aba', async () => {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const json = (d: unknown) => new Response(JSON.stringify(d), { status: 200, headers: { 'content-type': 'application/json' } })
    if (url.includes('/agente/conversa')) return json({ id: 1, alvo: 'questao:2', papel: 'tutor', mensagens: [] })
    if (url.endsWith('/api/agente/estado')) return json({ chave_configurada: true, modelo: 'g', total_mes: 0, teto: 20 })
    throw new Error(`rota não simulada: ${url}`)
  }))
  render(DetalheQuestao, { uid: 'u1', lista: l, questao: q, marca: null, secao: null, onmarcar: vi.fn(), resolucao })
  expect(await screen.findByRole('button', { name: 'N3 Esboço' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'N4 Resolução' })).toBeNull()
  expect(screen.getByRole('tab', { name: 'Sua resolução' })).toBeInTheDocument()
})
