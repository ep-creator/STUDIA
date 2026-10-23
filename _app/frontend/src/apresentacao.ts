// Textos de apresentação montados a partir dos dados (nunca guardados no banco).

export function ordinal(n: number): string {
  return `${n}ª`
}

export function nomeUnidade(n: number): string {
  return `${ordinal(n)} unidade`
}

function diaLocal(d: Date): number {
  return Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())
}

/** Dias de calendário entre hoje e a data ISO (AAAA-MM-DD), ignorando a hora. */
export function diasAte(data: string, hoje: Date): number {
  const [a, m, d] = data.split('-').map(Number)
  return Math.round((Date.UTC(a, m - 1, d) - diaLocal(hoje)) / 86_400_000)
}

export function textoContagem(prova: { data: string; hora_inicio: string | null } | null, hoje: Date): string {
  if (!prova) return 'sem data de prova'
  const dias = diasAte(prova.data, hoje)
  if (dias < 0) return 'prova já passou'
  if (dias === 0) return 'hoje'
  if (dias === 1) return 'amanhã'
  return `${dias} dias`
}

const DIAS_SEMANA = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']

/** "seg 14/09" (e " · 14:30" quando há hora). */
export function dataCurta(data: string, hora?: string | null): string {
  const [a, m, d] = data.split('-').map(Number)
  const dia = DIAS_SEMANA[new Date(a, m - 1, d).getDay()]
  return `${dia} ${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}${hora ? ` · ${hora}` : ''}`
}

const ROTULO_STATUS: Record<string, string> = { pendente: 'pendente', proxima: 'próxima', visto: 'visto' }

export function rotuloStatus(status: string): string {
  return ROTULO_STATUS[status] ?? status
}

export function isoDe(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
