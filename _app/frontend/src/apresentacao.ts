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

/** Linha curta da prova no topo: "Prova em 12 dias", "Prova hoje", "Prova já foi (seg 14/09)", "Sem data de prova". */
export function textoTopoProva(prova: { data: string; hora_inicio: string | null } | null, hoje: Date): string {
  if (!prova) return 'Sem data de prova'
  const dias = diasAte(prova.data, hoje)
  if (dias < 0) return `Prova já foi (${dataCurta(prova.data)})`
  if (dias === 0) return 'Prova hoje'
  if (dias === 1) return 'Prova amanhã'
  return `Prova em ${dias} dias`
}

/** Ordem natural ("Aula 2" antes de "Aula 10"), sem diferenciar acento e maiúscula. */
export function compararNomes(a: string, b: string): number {
  return a.localeCompare(b, 'pt-BR', { numeric: true, sensitivity: 'base' })
}

export function saudacao(agora: Date): string {
  const h = agora.getHours()
  if (h >= 5 && h < 12) return 'Bom dia'
  if (h >= 12 && h < 18) return 'Boa tarde'
  return 'Boa noite'
}

export function dataPorExtenso(agora: Date): string {
  return agora.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })
}

/** A prova mais próxima (de hoje em diante) entre todas as matérias, para o resumo da tela inicial. */
export function proximaProvaGeral<M extends { proxima_prova: { data: string; hora_inicio: string | null } | null }>(materias: M[], hoje: Date): M | null {
  const futuras = materias.filter((m) => m.proxima_prova && diasAte(m.proxima_prova.data, hoje) >= 0)
  futuras.sort((a, b) => a.proxima_prova!.data.localeCompare(b.proxima_prova!.data))
  return futuras[0] ?? null
}
