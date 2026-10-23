// Montagem das visões de Cronograma e Formulário a partir do painel.
import type { Evento, Formula, SecaoVinculada, Sessao, Topico } from './api/tipos'

export type ItemLinha = {
  data: string | null
  hora: string | null
  tipo: 'sessao' | string
  sessao?: Sessao
  evento?: Evento
}

/** Sessões de estudo e eventos do calendário numa linha só, por data e hora; sessões sem data no fim, pela ordem. */
export function montarLinhaDoTempo(sessoes: Sessao[], eventos: Evento[]): ItemLinha[] {
  const comData: ItemLinha[] = [
    ...eventos.map((e) => ({ data: e.data, hora: e.hora_inicio, tipo: e.tipo, evento: e })),
    ...sessoes.filter((s) => s.data).map((s) => ({ data: s.data, hora: null, tipo: 'sessao', sessao: s })),
  ]
  // No mesmo dia: eventos com hora pela hora, depois o restante (aula antes da sessão de estudo do dia)
  const chave = (i: ItemLinha) => `${i.data}|${i.hora ?? ''}|${i.tipo === 'sessao' ? 1 : 0}`
  comData.sort((a, b) => chave(a).localeCompare(chave(b)))
  const semData = sessoes
    .filter((s) => !s.data)
    .sort((a, b) => a.ordem - b.ordem)
    .map((s) => ({ data: null, hora: null, tipo: 'sessao', sessao: s }))
  return [...comData, ...semData]
}

/** Fórmulas agrupadas pelo tópico ligado à seção da fórmula; as demais em "Sem tópico" (no fim). */
export function agruparFormulas(
  formulas: Formula[],
  topicos: Topico[],
  vinculos: Record<string, SecaoVinculada[]>,
): [string, Formula[]][] {
  const topicoDaSecao = new Map<number, string>()
  for (const t of topicos) {
    for (const s of vinculos[String(t.id)] ?? []) if (!topicoDaSecao.has(s.secao_id)) topicoDaSecao.set(s.secao_id, t.titulo)
  }
  const grupos = new Map<string, Formula[]>()
  for (const f of [...formulas].sort((a, b) => a.ordem - b.ordem)) {
    const nome = (f.secao_id !== null && topicoDaSecao.get(f.secao_id)) || 'Sem tópico'
    grupos.set(nome, [...(grupos.get(nome) ?? []), f])
  }
  const semTopico = grupos.get('Sem tópico')
  grupos.delete('Sem tópico')
  return [...grupos.entries(), ...(semTopico ? [['Sem tópico', semTopico] as [string, Formula[]]] : [])]
}
