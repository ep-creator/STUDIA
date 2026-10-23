// @vitest-environment node
import { mkdirSync, mkdtempSync, utimesSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { expect, test } from 'vitest'
import { precisaCompilar, precisaInstalar } from './compilacao.mjs'

function projeto() {
  const raiz = mkdtempSync(join(tmpdir(), 'compilacao-'))
  for (const p of ['src', 'dist', 'node_modules']) mkdirSync(join(raiz, p))
  writeFileSync(join(raiz, 'src', 'main.ts'), '')
  writeFileSync(join(raiz, 'package.json'), '{}')
  writeFileSync(join(raiz, 'package-lock.json'), '{}')
  return raiz
}

function idade(arquivo: string, segundos: number) {
  const t = new Date(Date.now() - segundos * 1000)
  utimesSync(arquivo, t, t)
}

test('compila sem build, ou quando qualquer fonte de configuração é mais nova', () => {
  const raiz = projeto()
  expect(precisaCompilar(raiz)).toBe(true)
  writeFileSync(join(raiz, 'dist', 'index.html'), '')
  idade(join(raiz, 'dist', 'index.html'), 50)
  for (const f of ['src/main.ts', 'package.json', 'package-lock.json']) idade(join(raiz, f), 100)
  expect(precisaCompilar(raiz)).toBe(false)
  writeFileSync(join(raiz, 'svelte.config.js'), '')   // configuração nova também conta
  expect(precisaCompilar(raiz)).toBe(true)
})

test('reinstala quando o lock muda depois da última instalação', () => {
  const raiz = projeto()
  expect(precisaInstalar(raiz)).toBe(true)   // node_modules sem registro de instalação
  writeFileSync(join(raiz, 'node_modules', '.package-lock.json'), '{}')
  idade(join(raiz, 'node_modules', '.package-lock.json'), 50)
  idade(join(raiz, 'package-lock.json'), 100)
  expect(precisaInstalar(raiz)).toBe(false)
  writeFileSync(join(raiz, 'package-lock.json'), '{"novo": true}')   // dependência nova chegou com a atualização
  expect(precisaInstalar(raiz)).toBe(true)
})
