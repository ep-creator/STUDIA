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

const COMANDO_LATEX = /\\[a-zA-Z]+/

function escaparHtml(texto: string): string {
  return texto.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/** Corpo de uma fórmula do Formulário. Com comandos LaTeX: uma equação por linha (o KaTeX ignora quebras soltas).
 *  Sem LaTeX (fórmulas diagramadas em Unicode, vindas do app antigo): texto pré-formatado, com " | " virando linha. */
export function renderizarFormula(corpo: string): string {
  if (COMANDO_LATEX.test(corpo)) {
    const linhas = corpo.split('\n').map((l) => l.trim()).filter(Boolean)
    return DOMPurify.sanitize(linhas.map((l) => renderizarLatex(l, true)).join(''))
  }
  const texto = corpo.replace(/\s+\|\s+/g, '\n').replace(/^\n+|\n+$/g, '')
  return DOMPurify.sanitize(`<pre class="formula-texto">${escaparHtml(texto)}</pre>`)
}
