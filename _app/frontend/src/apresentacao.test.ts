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

test('resumos seguem a ordem dos tópicos; sem tópico, ficam junto do vizinho de número; de unidades anteriores vêm antes', async () => {
  const { ordenarPeloAssunto } = await import('./apresentacao')
  const topicos = [
    { unidade_id: 1, ordem: 1, titulo: 'Funções de várias variáveis · gráficos' },
    { unidade_id: 1, ordem: 2, titulo: 'Coordenadas polares' },
    { unidade_id: 1, ordem: 3, titulo: 'Limite e continuidade' },
    { unidade_id: 1, ordem: 4, titulo: 'Multiplicadores de Lagrange' },
  ]
  const d = (titulo: string, unidade_id: number | null = 1) => ({ titulo, unidade_id })
  const ordem = (docs: ReturnType<typeof d>[], atual: number) => ordenarPeloAssunto(docs, topicos, atual).map((x) => x.titulo)
  expect(ordem([d('14.2 Limite e continuidade'), d('Coordenadas polares'), d('14.8 Multiplicadores de Lagrange'), d('14.7 Valores máximo e mínimo'), d('14.1 Funções de várias variáveis')], 1))
    .toEqual(['14.1 Funções de várias variáveis', 'Coordenadas polares', '14.2 Limite e continuidade', '14.7 Valores máximo e mínimo', '14.8 Multiplicadores de Lagrange'])
  // vendo a 3ª unidade: o resumo da 1ª (revisão) vem antes dos da unidade
  expect(ordem([d('15.5 Aplicações', 3), d('Coordenadas polares', 1), d('15.4 Integrais em polares', 3)], 3))
    .toEqual(['Coordenadas polares', '15.4 Integrais em polares', '15.5 Aplicações'])
  // sem tópico nenhum, vale a ordem dos números
  expect(ordenarPeloAssunto([d('Resolução 14.2-7'), d('Resolução 14.1-30'), d('Resolução 14.2-11')], [], 1).map((x) => x.titulo))
    .toEqual(['Resolução 14.1-30', 'Resolução 14.2-7', 'Resolução 14.2-11'])
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

test('resumo do tópico: o documento com mais palavras em comum', async () => {
  const { documentoDoTopico } = await import('./apresentacao')
  const docs = [{ id: 1, titulo: '14.2 Limite e continuidade' }, { id: 2, titulo: '14.3 Derivadas parciais' }]
  expect(documentoDoTopico('Derivadas parciais e de ordens superiores', docs)?.id).toBe(2)
  expect(documentoDoTopico('Aula extra', docs)).toBeNull()
})
