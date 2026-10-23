// Único ponto de acesso ao motor. Se um dia houver login ou servidor remoto, é aqui que entram o endereço,
// o token e o tratamento de sessão expirada; nenhuma tela chama fetch direto.

export const API_BASE: string = import.meta.env.VITE_API_BASE ?? ''

export class ErroApi extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = 'ErroApi'
  }
}

export class MotorDesligado extends Error {
  constructor() {
    super('Motor desligado: abra o abrir-novo.bat')
    this.name = 'MotorDesligado'
  }
}

type Metodo = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export async function requisitar<T>(metodo: Metodo, caminho: string, corpo?: unknown): Promise<T> {
  const init: RequestInit = { method: metodo }
  if (corpo instanceof FormData) {
    init.body = corpo
  } else if (corpo !== undefined) {
    init.body = JSON.stringify(corpo)
    init.headers = { 'content-type': 'application/json' }
  }
  let resposta: Response
  try {
    resposta = await fetch(API_BASE + caminho, init)
  } catch {
    throw new MotorDesligado()
  }
  let texto: string
  try {
    texto = await resposta.text()
  } catch {
    throw new MotorDesligado() // a conexão caiu no meio da resposta
  }
  let dados: { erro?: unknown } | null = null
  try {
    dados = texto ? JSON.parse(texto) : null
  } catch {
    dados = null // erro que não veio do motor em JSON (ex.: 500 em texto puro)
  }
  if (!resposta.ok) {
    const erro = typeof dados?.erro === 'string' ? dados.erro : null
    throw new ErroApi(erro ?? `Erro no motor (${resposta.status}): ${resposta.statusText || texto.slice(0, 80)}`, resposta.status)
  }
  return dados as T
}

/** Endereço de um arquivo da matéria; `pagina` abre o PDF já na página (leitor do próprio navegador). */
export function urlArquivo(uid: string, caminho: string, pagina?: number): string {
  const rel = caminho.split('/').map(encodeURIComponent).join('/')
  return `${API_BASE}/arquivos/${encodeURIComponent(uid)}/${rel}${pagina ? `#page=${pagina}` : ''}`
}
