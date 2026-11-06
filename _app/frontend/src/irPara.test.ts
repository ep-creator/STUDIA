import { expect, test } from 'vitest'
import { destinos } from './irPara'
import { lista, painel, questao, topico, unidade } from './teste-dados'

const p = painel({
  unidades: [unidade(1), unidade(2), unidade(3)], unidade: 3,
  topicos: [topico(14, 'pendente', { titulo: 'Polares (fim) · aplicações' })],
  listas: [lista(1, '14.1', [questao(4, '46'), questao(5, '50')]), lista(19, 'L5', [questao(201, '8')])],
})

test('caixa vazia: as áreas, como um menu', () => {
  expect(destinos('', p).map((d) => d.rotulo)).toEqual(['Hoje', 'Tópicos', 'Praticar', 'Biblioteca', 'Plano completo', 'Folha de fórmulas', 'Adicionar material', 'Histórico'])
})

test('questão pelo código da lista e o número', () => {
  for (const consulta of ['14.1 46', '14.1 #46', '14.1#46']) {
    expect(destinos(consulta, p)[0]).toEqual({ rotulo: '14.1 #46', detalhe: 'Praticar · Lista 14.1', href: '#/m/ab/u/3/listas/4' })
  }
  expect(destinos('l5 8', p)[0].href).toBe('#/m/ab/u/3/listas/201')
})

test('unidade, área por nome (sem acento) e tópico por trecho do título', () => {
  expect(destinos('2ª unidade', p)[0]).toEqual({ rotulo: '2ª unidade', detalhe: 'Hoje desta unidade', href: '#/m/ab/u/2/painel' })
  expect(destinos('formulas', p)[0].rotulo).toBe('Folha de fórmulas')
  expect(destinos('pra', p)[0].href).toBe('#/m/ab/u/3/listas')
  expect(destinos('polares', p)).toContainEqual({ rotulo: 'Polares (fim) · aplicações', detalhe: 'Tópico', href: '#/m/ab/u/3/topicos/14' })
  expect(destinos('9ª unidade', p)).toEqual([])
})
