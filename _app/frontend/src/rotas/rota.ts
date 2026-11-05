// Rotas por hash: atualizar a página ou usar um favorito volta à mesma matéria, unidade e área.

export const AREAS = ['painel', 'topicos', 'listas', 'cronograma', 'documentos', 'formulario'] as const
export type Area = (typeof AREAS)[number]

export type Rota =
  | { tela: 'materias' }
  | { tela: 'materia'; uid: string; unidade: number | null; area: Area; topico?: number | null }
  | { tela: 'importar' | 'historico'; uid: string }

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
  // a antiga página do Assistente virou a gaveta da IA: o endereço velho abre a matéria
  if (partes.length === 3 && partes[2] === 'assistente') return { tela: 'materia', uid, unidade: null, area: 'painel' }
  if (partes.length === 3 && (partes[2] === 'importar' || partes[2] === 'historico')) {
    return { tela: partes[2], uid }
  }
  if (partes.length === 5 && partes[2] === 'u') {
    const unidade = Number(partes[3])
    const area = partes[4] as Area
    if (Number.isInteger(unidade) && unidade >= 1 && AREAS.includes(area)) return { tela: 'materia', uid, unidade, area }
  }
  // página de um tópico: #/m/<uid>/u/<n>/topicos/<id>
  if (partes.length === 6 && partes[2] === 'u' && partes[4] === 'topicos') {
    const unidade = Number(partes[3])
    const topico = Number(partes[5])
    if (Number.isInteger(unidade) && unidade >= 1 && Number.isInteger(topico) && topico >= 1) {
      return { tela: 'materia', uid, unidade, area: 'topicos', topico }
    }
  }
  return INICIO
}

export function montarHash(rota: Rota): string {
  if (rota.tela === 'materias') return '#/'
  const base = `#/m/${encodeURIComponent(rota.uid)}`
  if (rota.tela !== 'materia') return `${base}/${rota.tela}`
  if (rota.unidade === null) return base
  const topico = rota.area === 'topicos' && rota.topico ? `/${rota.topico}` : ''
  return `${base}/u/${rota.unidade}/${rota.area}${topico}`
}

/**
 * A lista de matérias (tela inicial e seletor da barra lateral) precisa ser lida de novo? Na tela inicial, ou quando a
 * matéria aberta não está nela — a recém-criada, ou a lista ainda vazia. `jaPedidaPara` evita pedir de novo, em laço,
 * para um endereço de matéria que não existe (ou com o workspace sem matérias).
 */
export function precisaListaDeMaterias(rota: Rota, materias: { uid: string }[], jaPedidaPara: string | null): boolean {
  if (rota.tela === 'materias') return true
  return !materias.some((m) => m.uid === rota.uid) && jaPedidaPara !== rota.uid
}
