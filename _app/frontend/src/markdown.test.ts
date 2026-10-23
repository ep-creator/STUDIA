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

test('cifrão de dinheiro e código não viram fórmula', () => {
  expect(renderizarMarkdown('Custa R$ 10 e R$ 20 por mês')).not.toContain('katex')
  expect(renderizarMarkdown('Use `$x$` no código')).not.toContain('katex')
  expect(renderizarMarkdown('```\n$a$ e $b$\n```')).not.toContain('katex')
  expect(renderizarMarkdown('E a fórmula $x^2$ continua')).toContain('katex')
})

test('fórmula em LaTeX: uma equação por linha', async () => {
  const { renderizarFormula } = await import('./markdown')
  const html = renderizarFormula(String.raw`x = r\cos\theta` + '\n' + String.raw`y = r\sin\theta`)
  expect(html.match(/katex-display/g)).toHaveLength(2)
})

test('fórmula em texto Unicode do app antigo vira KaTeX, uma linha por vez (" | " também quebra)', async () => {
  const { renderizarFormula } = await import('./markdown')
  const html = renderizarFormula('x = r cos θ,  y = r sen θ\n\nD<0 → sela  |  dA = r dr dθ')
  expect(html.match(/katex-display/g)).toHaveLength(3)
  expect(html).not.toContain('katex-error')
  expect(html).toContain('sen')
})

test('fórmula Unicode com % ou chaves quebradas não some nem mostra erro', async () => {
  const { renderizarFormula } = await import('./markdown')
  const porcento = renderizarFormula('juros = 5% ao mês')
  expect(porcento).not.toContain('katex-error')
  expect(porcento.replace(/<[^>]+>/g, '')).toContain('5%ao') // o % não vira comentário e engole o resto
  const quebrada = renderizarFormula('f(x} = 1')
  expect(quebrada).not.toContain('katex-error')
  expect(quebrada).toContain('f(x} = 1')
})
