import { expect, test } from 'vitest'
import { diasAte, nomeUnidade, ordinal, rotuloStatus, textoContagem } from './apresentacao'

test('ordinal e unidade', () => {
  expect(ordinal(1)).toBe('1ª')
  expect(nomeUnidade(3)).toBe('3ª unidade')
})

test.each([
  ['2026-10-22', 'hoje'],
  ['2026-10-23', 'amanhã'],
  ['2026-11-03', '12 dias'],
])('contagem %s', (data, texto) => {
  expect(textoContagem({ data, hora_inicio: null }, new Date(2026, 9, 22, 15, 0))).toBe(texto)
})

test('prova que já passou e sem prova', () => {
  expect(textoContagem({ data: '2026-10-01', hora_inicio: null }, new Date(2026, 9, 22))).toBe('prova já passou')
  expect(textoContagem(null, new Date())).toBe('sem data de prova')
})

test('diasAte ignora a hora do dia', () => {
  expect(diasAte('2026-10-23', new Date(2026, 9, 22, 23, 59))).toBe(1)
})

test('rótulos dos status do banco', () => {
  expect(['pendente', 'proxima', 'visto'].map(rotuloStatus)).toEqual(['pendente', 'próxima', 'visto'])
})

test('texto da prova no topo', async () => {
  const { textoTopoProva } = await import('./apresentacao')
  const hoje = new Date(2026, 9, 22)
  expect(textoTopoProva({ data: '2026-11-03', hora_inicio: '14:30' }, hoje)).toBe('Prova em 12 dias')
  expect(textoTopoProva({ data: '2026-10-22', hora_inicio: null }, hoje)).toBe('Prova hoje')
  expect(textoTopoProva({ data: '2026-10-23', hora_inicio: null }, hoje)).toBe('Prova amanhã')
  expect(textoTopoProva({ data: '2026-09-14', hora_inicio: null }, hoje)).toBe('Prova já foi (seg 14/09)')
  expect(textoTopoProva(null, hoje)).toBe('Sem data de prova')
})

test('prova perto: de hoje até 7 dias, nunca depois de passar', async () => {
  const { provaPerto } = await import('./apresentacao')
  const hoje = new Date(2026, 9, 22, 21, 0)
  const em = (data: string) => provaPerto({ data, hora_inicio: null }, hoje)
  expect(em('2026-10-22')).toBe(true)    // hoje
  expect(em('2026-10-29')).toBe(true)    // 7 dias
  expect(em('2026-10-30')).toBe(false)   // 8 dias
  expect(em('2026-10-21')).toBe(false)   // já passou
  expect(provaPerto(null, hoje)).toBe(false)
})

test('nome legível de um PDF', async () => {
  const { nomeLegivel } = await import('./apresentacao')
  expect(nomeLegivel({ titulo: '', caminho: 'fontes/listas/Lista1_2026-1.pdf' })).toBe('Lista1 2026-1')
  expect(nomeLegivel({ titulo: 'Stewart_1_ptbr', caminho: 'x.pdf' })).toBe('Stewart 1 ptbr')
  expect(nomeLegivel({ titulo: 'Programa da disciplina', caminho: 'x.pdf' })).toBe('Programa da disciplina')
})

test('título que cita a seção pelo código', async () => {
  const { citaSecao } = await import('./apresentacao')
  expect(citaSecao('Massa de uma lâmina (15.5)', '15.5')).toBe(true)
  expect(citaSecao('Coordenadas (15.50)', '15.5')).toBe(false)
  expect(citaSecao('Seção 115.5', '15.5')).toBe(false)
  expect(citaSecao('Polares 1525', '15.5')).toBe(false)
})

test('foco da sessão: título em negrito e o detalhe sem o travessão', async () => {
  const { focoDaSessao } = await import('./apresentacao')
  expect(focoDaSessao('**15.5 Aplicações** — massa, centro de massa\n\nExercícios: 15.5: 11')).toEqual({ titulo: '15.5 Aplicações', detalhe: 'massa, centro de massa' })
  expect(focoDaSessao('**Integrais em polares**\n\nExercícios')).toEqual({ titulo: 'Integrais em polares', detalhe: '' })
  expect(focoDaSessao('Revisão geral')).toEqual({ titulo: 'Revisão geral', detalhe: '' })
})

test('ordem natural de nomes', async () => {
  const { compararNomes } = await import('./apresentacao')
  expect(['Aula 10', 'Aula 2', 'Aula 1'].sort(compararNomes)).toEqual(['Aula 1', 'Aula 2', 'Aula 10'])
})

test.each([
  [6, 'Bom dia'],
  [12, 'Boa tarde'],
  [19, 'Boa noite'],
  [2, 'Boa noite'],
])('saudação às %ih: %s', async (hora, esperado) => {
  const { saudacao } = await import('./apresentacao')
  expect(saudacao(new Date(2026, 9, 23, hora))).toBe(esperado)
})

test('data por extenso, em português', async () => {
  const { dataPorExtenso } = await import('./apresentacao')
  expect(dataPorExtenso(new Date(2026, 9, 23, 10))).toBe('sexta-feira, 23 de outubro')
})

test('próxima prova entre todas as matérias ignora as que já passaram', async () => {
  const { proximaProvaGeral } = await import('./apresentacao')
  const m = (nome: string, data: string | null) => ({ nome, proxima_prova: data ? { data, hora_inicio: null, unidade: 1 } : null })
  const hoje = new Date(2026, 9, 23, 10)
  expect(proximaProvaGeral([m('A', '2026-11-30'), m('B', '2026-10-20'), m('C', '2026-11-05'), m('D', null)], hoje)?.nome).toBe('C')
  expect(proximaProvaGeral([m('B', '2026-10-20')], hoje)).toBeNull()
})

test('para revisar: questões ✗ e ?, agrupadas por lista, na ordem das listas', async () => {
  const { paraRevisar } = await import('./apresentacao')
  const listas = [
    { id: 1, codigo: '14.1', titulo: 'Funções', questoes: [{ id: 10, rotulo: '22' }, { id: 11, rotulo: '46' }, { id: 12, rotulo: '50' }] },
    { id: 2, codigo: '14.2', titulo: 'Limites', questoes: [{ id: 20, rotulo: '12' }] },
    { id: 3, codigo: '14.3', titulo: 'Derivadas', questoes: [{ id: 30, rotulo: '1' }] },
  ]
  const grupos = paraRevisar(listas, { '10': 'ok', '11': 'err', '12': 'dub', '20': 'err' })
  expect(grupos.map((g) => [g.lista.codigo, g.questoes.map((x) => `${x.questao.rotulo}${x.marca}`)])).toEqual([
    ['14.1', ['46err', '50dub']],
    ['14.2', ['12err']],
  ])
})

test('desempenho de uma lista conta acertos, erros, dúvidas e o que falta', async () => {
  const { desempenho } = await import('./apresentacao')
  expect(desempenho({ questoes: [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }] }, { '1': 'ok', '2': 'ok', '3': 'err' }))
    .toEqual({ ok: 2, err: 1, dub: 0, falta: 1, total: 4 })
})

test('do trecho do livro, só o exercício pedido (e o enunciado do bloco, se houver)', async () => {
  const { trechoDoExercicio } = await import('./apresentacao')
  const trecho = '45–50 Faça o mapa de contorno.\n46. f (x, y) = ln(x²+ 4y²)\n47. f (x, y) = yex\n51–52 Faça o esboço.\n51. f (x, y) = x²+ 9y²'
  expect(trechoDoExercicio(trecho, '46')).toBe('45–50 Faça o mapa de contorno.\n46. f (x, y) = ln(x²+ 4y²)')
  expect(trechoDoExercicio(trecho, '51')).toBe('51–52 Faça o esboço.\n51. f (x, y) = x²+ 9y²')
  expect(trechoDoExercicio('46. f (x, y)\ncontinua aqui\n47. outra', '46')).toBe('46. f (x, y)\ncontinua aqui')
  expect(trechoDoExercicio('texto sem numeração', '46')).toBe('texto sem numeração')
})
