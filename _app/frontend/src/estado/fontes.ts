// Os arquivos da matéria (PDFs), lidos uma vez por matéria: quem precisa só do caminho de um deles (o link para a lista
// da turma numa questão, por exemplo) não pede a lista de novo a cada questão aberta.
import { requisitar } from '../api/cliente'
import type { FonteResumo } from '../api/tipos'

const porMateria = new Map<string, Promise<FonteResumo[]>>()

export function fontesDaMateria(uid: string): Promise<FonteResumo[]> {
  let lista = porMateria.get(uid)
  if (!lista) {
    lista = requisitar<FonteResumo[]>('GET', `/api/materias/${encodeURIComponent(uid)}/fontes`)
    porMateria.set(uid, lista)
    lista.catch(() => porMateria.delete(uid))   // falhou: a próxima tentativa pede de novo
  }
  return lista
}

/** Caminho do arquivo da fonte (para abrir o PDF), ou null se a fonte não existe mais ou a leitura falhou. */
export async function caminhoDaFonte(uid: string, fonteId: number): Promise<string | null> {
  try {
    return (await fontesDaMateria(uid)).find((f) => f.id === fonteId)?.caminho ?? null
  } catch {
    return null
  }
}

/** Depois de importar ou apagar arquivos, a lista guardada não vale mais. */
export function esquecerFontes(uid?: string): void {
  if (uid) porMateria.delete(uid)
  else porMateria.clear()
}
