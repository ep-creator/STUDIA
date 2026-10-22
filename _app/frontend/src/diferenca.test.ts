import { expect, test } from 'vitest'
import { diferencaLinhas } from './diferenca'

test('diferença por linhas', () => {
  expect(diferencaLinhas('a\nb', 'a\nc')).toEqual([
    { tipo: 'igual', texto: 'a' }, { tipo: 'removida', texto: 'b' }, { tipo: 'adicionada', texto: 'c' },
  ])
})

test('arquivo criado ou apagado', () => {
  expect(diferencaLinhas(null, 'x\ny')).toEqual([{ tipo: 'adicionada', texto: 'x' }, { tipo: 'adicionada', texto: 'y' }])
  expect(diferencaLinhas('x', null)).toEqual([{ tipo: 'removida', texto: 'x' }])
})

test('linhas iguais no meio são preservadas', () => {
  const d = diferencaLinhas('1\n2\n3\n4', '1\n2b\n3\n4\n5')
  expect(d.filter((l) => l.tipo === 'igual').map((l) => l.texto)).toEqual(['1', '3', '4'])
  expect(d.filter((l) => l.tipo !== 'igual').map((l) => `${l.tipo}:${l.texto}`)).toEqual(['removida:2', 'adicionada:2b', 'adicionada:5'])
})
