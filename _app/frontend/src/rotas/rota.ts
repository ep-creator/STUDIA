// Rotas por hash: atualizar a página ou usar um favorito volta à mesma matéria, unidade e área.

export const AREAS = ['painel', 'topicos', 'listas', 'cronograma', 'documentos', 'formulario'] as const
export type Area = (typeof AREAS)[number]

export type Rota =
  | { tela: 'materias' }
  | { tela: 'materia'; uid: string; unidade: number | null; area: Area }
  | { tela: 'importar' | 'historico' | 'assistente'; uid: string }

const INICIO: Rota = { tela: 'materias' }

export function analisarRota(hash: string): Rota {
  let partes: string[]
  try {
    partes = hash.replace(/^#\/?/, '').split('/').filter(Boolean).map(decodeURIComponent)
  } catch {
    return INICIO   // endereço com escape inválido (favorito estragado): tela inicial em vez de quebrar
  }
  if (partes[0] !== 'm' || !partes[1]) return INICIO
  const uid = partes[1]
  if (partes.length === 2) return { tela: 'materia', uid, unidade: null, area: 'painel' }
  if (partes.length === 3 && (partes[2] === 'importar' || partes[2] === 'historico' || partes[2] === 'assistente')) {
    return { tela: partes[2], uid }
  }
  if (partes.length === 5 && partes[2] === 'u') {
    const unidade = Number(partes[3])
    const area = partes[4] as Area
    if (Number.isInteger(unidade) && unidade >= 1 && AREAS.includes(area)) return { tela: 'materia', uid, unidade, area }
  }
  return INICIO
}

export function montarHash(rota: Rota): string {
  if (rota.tela === 'materias') return '#/'
  const base = `#/m/${encodeURIComponent(rota.uid)}`
  if (rota.tela !== 'materia') return `${base}/${rota.tela}`
  if (rota.unidade === null) return base
  return `${base}/u/${rota.unidade}/${rota.area}`
}
