import { expect, test, vi } from 'vitest'
import { EdicaoProposta } from './revisao'

type P = { a: boolean; b: boolean }

test('edições rápidas não se perdem: cada envio leva todas as mudanças, um de cada vez', async () => {
  const enviados: P[] = []
  let emVoo = 0
  let maxEmVoo = 0
  const enviar = vi.fn(async (p: P) => {
    emVoo++
    maxEmVoo = Math.max(maxEmVoo, emVoo)
    enviados.push(structuredClone(p))
    await new Promise((r) => setTimeout(r, 10))
    emVoo--
    return p
  })
  const edicao = new EdicaoProposta<P>({ a: true, b: true }, enviar)
  void edicao.alterar((p) => (p.a = false))
  expect(edicao.proposta).toEqual({ a: false, b: true })   // a tela muda na hora
  await edicao.alterar((p) => (p.b = false))
  expect(maxEmVoo).toBe(1)
  expect(enviados.at(-1)).toEqual({ a: false, b: false })
})

test('falha no envio avisa para reler a proposta do motor', async () => {
  const aoFalhar = vi.fn()
  const edicao = new EdicaoProposta<P>({ a: true, b: true }, async () => { throw new Error('motor recusou') }, aoFalhar)
  await edicao.alterar((p) => (p.a = false))
  expect(aoFalhar).toHaveBeenCalledWith(expect.objectContaining({ message: 'motor recusou' }))
})

test('esperar() só termina depois dos envios pendentes', async () => {
  const feitos: string[] = []
  const edicao = new EdicaoProposta<P>({ a: true, b: true }, async () => {
    await new Promise((r) => setTimeout(r, 10))
    feitos.push('put')
  })
  void edicao.alterar((p) => (p.a = false))
  await edicao.esperar()
  expect(feitos).toEqual(['put'])
})
