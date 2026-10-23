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

const PALAVRAS_VAZIAS = new Set(['para', 'como', 'sobre', 'entre', 'pelo', 'pela', 'unidade', 'resumo', 'resolucao'])

function palavrasChave(texto: string): Set<string> {
  const limpo = texto.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
  return new Set(limpo.split(/[^a-z0-9]+/).filter((p) => p.length >= 4 && !/^\d/.test(p) && !PALAVRAS_VAZIAS.has(p)))
}

/** Ordem "do assunto" para resumos e afins: cada documento vai para a posição do tópico com que mais se parece
 *  (na mesma unidade); quem não casa com tópico nenhum fica logo depois do vizinho de número (14.6 → 14.7 → 14.8).
 *  Documentos de outra unidade (revisão trazida para esta) vêm antes dos da unidade atual. */
export function ordenarPeloAssunto<D extends { titulo: string; unidade_id: number | null }>(
  docs: D[],
  topicos: { unidade_id: number; ordem: number; titulo: string }[],
  unidadeAtual: number | null,
): D[] {
  const base = [...docs].sort((a, b) => compararNomes(a.titulo, b.titulo))
  const grupo = (d: D) => (d.unidade_id !== null && d.unidade_id !== unidadeAtual ? d.unidade_id : Number.MAX_SAFE_INTEGER)
  const chaves = topicos.map((t) => ({ ...t, palavras: palavrasChave(t.titulo) }))

  const posicao = new Map<D, number>()
  const anterior = new Map<number, number>()
  for (const d of base) {
    const minhas = palavrasChave(d.titulo)
    let melhor: { ordem: number; pontos: number } | null = null
    for (const t of chaves) {
      if (d.unidade_id !== null && t.unidade_id !== d.unidade_id) continue
      const pontos = [...minhas].filter((p) => t.palavras.has(p)).length
      if (pontos > 0 && (!melhor || pontos > melhor.pontos || (pontos === melhor.pontos && t.ordem < melhor.ordem))) melhor = { ordem: t.ordem, pontos }
    }
    const g = grupo(d)
    const p = melhor ? melhor.ordem : (anterior.get(g) ?? 0) + 0.001
    posicao.set(d, p)
    anterior.set(g, p)
  }
  return base
    .map((d, i) => ({ d, i }))
    .sort((a, b) => grupo(a.d) - grupo(b.d) || posicao.get(a.d)! - posicao.get(b.d)! || a.i - b.i)
    .map(({ d }) => d)
}

type MarcaRevisao = 'err' | 'dub'

/** Questões marcadas ✗ ou ?, agrupadas por lista (só as listas que têm alguma), na ordem das listas. */
export function paraRevisar<L extends { questoes: { id: number }[] }>(
  listas: L[],
  marcacoes: Record<string, string>,
): { lista: L; questoes: { questao: L['questoes'][number]; marca: MarcaRevisao }[] }[] {
  return listas
    .map((lista) => ({
      lista,
      questoes: lista.questoes
        .filter((q) => marcacoes[String(q.id)] === 'err' || marcacoes[String(q.id)] === 'dub')
        .map((questao) => ({ questao, marca: marcacoes[String(questao.id)] as MarcaRevisao })),
    }))
    .filter((g) => g.questoes.length)
}

export function desempenho(lista: { questoes: { id: number }[] }, marcacoes: Record<string, string>) {
  const conta = (m: string) => lista.questoes.filter((q) => marcacoes[String(q.id)] === m).length
  const ok = conta('ok'), err = conta('err'), dub = conta('dub'), total = lista.questoes.length
  return { ok, err, dub, falta: total - ok - err - dub, total }
}

/** O documento (resumo) que mais se parece com o título do tópico, ou null se nenhum tiver palavra em comum. */
export function documentoDoTopico<D extends { titulo: string }>(titulo: string, docs: D[]): D | null {
  const minhas = palavrasChave(titulo)
  let melhor: { doc: D; pontos: number } | null = null
  for (const doc of docs) {
    const pontos = [...palavrasChave(doc.titulo)].filter((p) => minhas.has(p)).length
    if (pontos > 0 && (!melhor || pontos > melhor.pontos)) melhor = { doc, pontos }
  }
  return melhor?.doc ?? null
}
