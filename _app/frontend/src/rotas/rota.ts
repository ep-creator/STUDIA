// Rotas por hash: atualizar a página ou usar um favorito volta à mesma matéria, unidade e área.

export const AREAS = ['painel', 'topicos', 'listas', 'cronograma', 'documentos', 'formulario'] as const
export type Area = (typeof AREAS)[number]

export type Rota =
  | { tela: 'materias' }
  | {
      tela: 'materia'; uid: string; unidade: number | null; area: Area
      topico?: number | null; questao?: number | null; documento?: number | null
      sessao?: number | null   // Praticar aberto por uma sessão do plano: anterior, próxima e N andam por ela
    }
  | { tela: 'importar' | 'historico'; uid: string }

const INICIO: Rota = { tela: 'materias' }

export function analisarRota(hash: string): Rota {
  let partes: string[]
  const [caminho, consulta = ''] = hash.split('?')
  try {
    partes = caminho.replace(/^#\/?/, '').split('/').filter(Boolean).map(decodeURIComponent)
  } catch {
    return INICIO   // endereço com escape inválido (favorito estragado): tela inicial em vez de quebrar
  }
  const numSessao = Number(new URLSearchParams(consulta).get('sessao'))
  const comSessao = Number.isInteger(numSessao) && numSessao >= 1 ? { sessao: numSessao } : {}
  if (partes[0] !== 'm' || !partes[1]) return INICIO
  const uid = partes[1]
  if (partes.length === 2) return { tela: 'materia', uid, unidade: null, area: 'painel' }
  // a antiga página do Assistente virou a gaveta da IA: o endereço velho abre a matéria
  if (partes.length === 3 && partes[2] === 'assistente') return { tela: 'materia', uid, unidade: null, area: 'painel' }
  if (partes.length === 3 && (partes[2] === 'importar' || partes[2] === 'historico')) {
    return { tela: partes[2], uid }
  }
  // área sem unidade (endereço digitado ou antigo): a matéria na unidade atual, na área pedida
  if (partes.length === 3 && AREAS.includes(partes[2] as Area)) return { tela: 'materia', uid, unidade: null, area: partes[2] as Area }
  if (partes.length === 5 && partes[2] === 'u') {
    const unidade = Number(partes[3])
    const area = partes[4] as Area
    if (Number.isInteger(unidade) && unidade >= 1 && AREAS.includes(area)) {
      return { tela: 'materia', uid, unidade, area, ...(area === 'listas' ? comSessao : {}) }
    }
  }
  // um item aberto tem endereço próprio: tópico (…/topicos/<id>), questão em Praticar (…/listas/<id>) e texto na
  // Biblioteca (…/documentos/<id>)
  if (partes.length === 6 && partes[2] === 'u' && ['topicos', 'listas', 'documentos'].includes(partes[4])) {
    const unidade = Number(partes[3])
    const id = Number(partes[5])
    if (Number.isInteger(unidade) && unidade >= 1 && Number.isInteger(id) && id >= 1) {
      if (partes[4] === 'topicos') return { tela: 'materia', uid, unidade, area: 'topicos', topico: id }
      if (partes[4] === 'listas') return { tela: 'materia', uid, unidade, area: 'listas', questao: id, ...comSessao }
      return { tela: 'materia', uid, unidade, area: 'documentos', documento: id }
    }
  }
  return INICIO
}

export function montarHash(rota: Rota): string {
  if (rota.tela === 'materias') return '#/'
  const base = `#/m/${encodeURIComponent(rota.uid)}`
  if (rota.tela !== 'materia') return `${base}/${rota.tela}`
  if (rota.unidade === null) return base
  const id = rota.area === 'topicos' ? rota.topico : rota.area === 'listas' ? rota.questao : rota.area === 'documentos' ? rota.documento : null
  const item = id ? `/${id}` : ''
  const sessao = rota.area === 'listas' && rota.sessao ? `?sessao=${rota.sessao}` : ''
  return `${base}/u/${rota.unidade}/${rota.area}${item}${sessao}`
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
