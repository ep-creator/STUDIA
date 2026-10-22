// Markdown com fórmulas ($…$ e $$…$$ via KaTeX). Toda saída passa pelo DOMPurify antes de ir para a tela.
import DOMPurify from 'dompurify'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: true, linkify: true, breaks: true })

const FORMULA = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g

export function renderizarLatex(tex: string, bloco = false): string {
  return katex.renderToString(tex, { displayMode: bloco, throwOnError: false, output: 'html' })
}

export function renderizarMarkdown(texto: string): string {
  // As fórmulas saem do texto antes do markdown (que estragaria _ e * dentro delas) e voltam já renderizadas.
  const formulas: string[] = []
  const semFormulas = (texto ?? '').replace(FORMULA, (_m, bloco: string | undefined, linha: string | undefined) => {
    formulas.push(bloco !== undefined ? renderizarLatex(bloco, true) : renderizarLatex(linha!, false))
    return `@@FORMULA${formulas.length - 1}@@`
  })
  const html = md.render(semFormulas).replace(/@@FORMULA(\d+)@@/g, (_m, i: string) => formulas[Number(i)])
  return DOMPurify.sanitize(html)
}
