import { expect, test } from 'vitest'
import { propostaVazia } from './proposta'

const classificacao = { tipo: 'calendario', confianca: 0.9, sinais: {}, revisar: false }

test('calendário sem nenhuma data é uma leitura vazia', () => {
  expect(propostaVazia('calendario', { classificacao, ano: null, unidades: [{ numero: 1, aulas: [], prova: null }], eventos: [], revisar: true }))
    .toBe('Não achei datas de aula nem de prova neste calendário.')
  const aula = { tipo: 'aula', data: '2026-08-31', hora_inicio: null, hora_fim: null, descricao: '', revisar: false }
  expect(propostaVazia('calendario', { classificacao, ano: 2026, unidades: [{ numero: 1, aulas: [aula], prova: null }], eventos: [], revisar: false })).toBeNull()
})

test('lista sem questões, programa sem tópicos, livro sem sumário', () => {
  expect(propostaVazia('lista', { listas: [{ questoes: [] }] })).toBe('Não achei questões nesta lista.')
  expect(propostaVazia('lista', { listas: [{ questoes: [{ rotulo: '1' }] }] })).toBeNull()
  expect(propostaVazia('programa', { unidades: [{ topicos: [] }] })).toBe('Não achei unidades nem tópicos neste programa.')
  expect(propostaVazia('livro', { secoes: [], sem_texto: true })).toMatch(/não tem texto/)
  expect(propostaVazia('livro', { secoes: [], sem_texto: false })).toBe('Não achei o sumário deste livro.')
})

test('turma sem nada e tipos que não prometem conteúdo', () => {
  expect(propostaVazia('turma', { professor: null, email: null, horarios: [], referencias: [], criterios: [] })).toMatch(/turma/)
  expect(propostaVazia('turma', { professor: 'Ana', email: null, horarios: [], referencias: [], criterios: [] })).toBeNull()
  expect(propostaVazia('slides', { observacao: 'x' })).toBeNull()
})
