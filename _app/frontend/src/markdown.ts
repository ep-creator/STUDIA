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

const FUNCOES = /\b(sen|sin|cos|tg|tan|cotg|sec|cossec|csc|ln|log|exp|arcsen|arccos|arctg|senh|cosh|tgh)\b\s*/g

/** Linha em Unicode (app antigo) → TeX que o KaTeX diagrama com a mesma cara das fórmulas em LaTeX:
 *  palavras acentuadas viram texto, funções viram operadores e os espaços do texto viram espaços de verdade. */
function unicodeParaTex(linha: string): string {
  return linha
    .replace(/[%#&$]/g, (c) => `\\${c}`)
    .replace(/\s{2,}/g, '\\quad{}')
    .replace(/[\p{L}]*[À-ÖØ-öø-ÿ][\p{L}]*/gu, (p) => `\\text{${p}}`)
    .replace(FUNCOES, (_m, f: string) => `\\operatorname{${f}}`)
    .replace(/(?<=[\p{L}\p{N})\]}])\s(?!\\operatorname)(?=[\p{L}\p{N}(\\√∫∬∭∮])/gu, '\\,') // o operador já traz o próprio espaço
}

/** Corpo de uma fórmula do Formulário: uma equação por linha (o KaTeX ignora quebras soltas).
 *  As diagramadas em Unicode também passam pelo KaTeX ("  |  " separa linhas); se alguma não for TeX válido, sai como texto. */
export function renderizarFormula(corpo: string): string {
  const latex = COMANDO_LATEX.test(corpo)
  const linhas = (latex ? corpo : corpo.replace(/\s+\|\s+/g, '\n')).split('\n').map((l) => l.trim()).filter(Boolean)
  const html = linhas.map((l) => {
    if (latex) return renderizarLatex(l, true)
    const saida = katex.renderToString(unicodeParaTex(l), { displayMode: true, throwOnError: false, strict: 'ignore', output: 'html' })
    return saida.includes('katex-error') ? `<pre class="formula-texto">${escaparHtml(l)}</pre>` : saida
  })
  return DOMPurify.sanitize(html.join(''))
}
