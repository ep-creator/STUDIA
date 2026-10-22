// Criação de documentos: o nome do arquivo vem do título e nunca sobrescreve um documento existente.
import { ErroApi, requisitar } from './api/cliente'
import type { Criado } from './api/tipos'

const MAX_TENTATIVAS = 50

export function nomeArquivo(titulo: string, sufixo = 1): string {
  const base = titulo.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  return `${base || 'documento'}${sufixo > 1 ? `-${sufixo}` : ''}.md`
}

/** Cria um documento vazio. `versao_esperada: ""` faz o motor recusar (409) se o arquivo já existe; aí tenta "-2", "-3"… */
export async function criarDocumento(uid: string, dados: { tipo: string; titulo: string; unidade_id: number }): Promise<number> {
  for (let sufixo = 1; sufixo <= MAX_TENTATIVAS; sufixo++) {
    try {
      const { id } = await requisitar<Criado>('PUT', `/api/materias/${uid}/documentos`, {
        ...dados, titulo: dados.titulo.trim(), nome_arquivo: nomeArquivo(dados.titulo, sufixo), corpo: '', versao_esperada: '',
      })
      return id
    } catch (e) {
      if (!(e instanceof ErroApi && e.status === 409)) throw e
    }
  }
  throw new Error('Não encontrei um nome de arquivo livre para este documento.')
}
