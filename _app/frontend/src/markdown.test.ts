import { expect, test } from 'vitest'
import { renderizarLatex, renderizarMarkdown } from './markdown'

test('fórmula vira KaTeX', () => {
  expect(renderizarMarkdown('Seja $x^2$ uma função')).toContain('katex')
  expect(renderizarMarkdown('$$\\int_0^1 x\\,dx$$')).toContain('katex-display')
})

test('markdown comum continua', () => {
  expect(renderizarMarkdown('**forte** e _leve_')).toMatch(/<strong>forte<\/strong>.*<em>leve<\/em>/)
})

test('script e handlers são removidos', () => {
  const html = renderizarMarkdown('<img src=x onerror="alert(1)"><script>alert(2)</script>ok')
  expect(html).not.toMatch(/onerror|<script/)
  expect(html).toContain('ok')
})

test('LaTeX inválido não derruba o texto', () => {
  const html = renderizarMarkdown('antes $\\frac{1}{$ depois')
  expect(html).toContain('antes')
  expect(html).toContain('depois')
})

test('renderizarLatex em bloco e em linha', () => {
  expect(renderizarLatex('a^2', true)).toContain('katex-display')
  expect(renderizarLatex('a^2')).not.toContain('katex-display')
})
