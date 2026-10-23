// Markdown com fórmulas ($…$ e $$…$$ via KaTeX). Toda saída passa pelo DOMPurify antes de ir para a tela.
import DOMPurify from 'dompurify'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: true, linkify: true, breaks: true })

// $$…$$ em bloco; $…$ em linha só quando colado ao conteúdo ("R$ 10 e R$ 20" não é fórmula)
const FORMULA = /\$\$([\s\S]+?)\$\$|(?<![\\\w])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\d)/g
const CODIGO = /```[\s\S]*?```|`[^`\n]+`/g

export function renderizarLatex(tex: string, bloco = false): string {
  return katex.renderToString(tex, { displayMode: bloco, throwOnError: false, output: 'html' })
}

export function renderizarMarkdown(texto: string): string {
  // As fórmulas saem do texto antes do markdown (que estragaria _ e * dentro delas) e voltam já renderizadas.
  // Código fica de fora (pode ter $ de verdade) e volta intacto antes do markdown
  const codigos: string[] = []
  const semCodigo = (texto ?? '').replace(CODIGO, (m) => `@@CODIGO${codigos.push(m) - 1}@@`)
  const formulas: string[] = []
  const semFormulas = semCodigo.replace(FORMULA, (_m, bloco: string | undefined, linha: string | undefined) => {
    formulas.push(bloco !== undefined ? renderizarLatex(bloco, true) : renderizarLatex(linha!, false))
    return `@@FORMULA${formulas.length - 1}@@`
  })
  const html = md.render(semFormulas.replace(/@@CODIGO(\d+)@@/g, (_m, i: string) => codigos[Number(i)])).replace(/@@FORMULA(\d+)@@/g, (_m, i: string) => formulas[Number(i)])
  return DOMPurify.sanitize(html)
}
