// @vitest-environment node
// Regras do estilo presas por teste: sem botão com contorno (.botao), sem o tema Padrão e sem condicionais de
// identidade; no máximo uma ação forte por tela.
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { expect, test } from 'vitest'

const SRC = fileURLToPath(new URL('../src', import.meta.url))

function fontes(pasta = SRC): [string, string][] {
  return readdirSync(pasta).flatMap((nome) => {
    const caminho = join(pasta, nome)
    if (statSync(caminho).isDirectory()) return fontes(caminho)
    return /\.(svelte|css)$/.test(nome) ? [[caminho, readFileSync(caminho, 'utf8')] as [string, string]] : []
  })
}

test('nenhum .botao, nenhum tema Padrão, nenhum condicional de identidade', () => {
  for (const [arquivo, texto] of fontes()) {
    expect(texto, arquivo).not.toMatch(/class="[^"]*\bbotao\b/)
    expect(texto, arquivo).not.toMatch(/\.botao\b/)
    expect(texto, arquivo).not.toMatch(/data-tema\^='(padrao|editorial)'/)
    expect(texto, arquivo).not.toMatch(/padrao-(claro|escuro)/)
  }
})

test('no máximo uma acao-forte por arquivo de tela', () => {
  for (const [arquivo, texto] of fontes(join(SRC, 'rotas'))) {
    expect((texto.match(/class="acao-forte/g) ?? []).length, arquivo).toBeLessThanOrEqual(1)
  }
})
