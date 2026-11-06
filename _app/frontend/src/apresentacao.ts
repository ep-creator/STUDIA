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

/** A prova está perto (de hoje até 7 dias): a contagem passa a falar em laranja brasa. */
export function provaPerto(prova: { data: string; hora_inicio: string | null } | null, hoje: Date): boolean {
  if (!prova) return false
  const dias = diasAte(prova.data, hoje)
  return dias >= 0 && dias <= 7
}

/**
 * Nome para mostrar de um PDF: o título, se houver; senão o nome do arquivo sem a extensão e sem "_" e "-" de
 * separador ("Lista1_2026-1.pdf" → "Lista1 2026-1", "Stewart_1_ptbr" → "Stewart 1 ptbr").
 */
export function nomeLegivel(fonte: { titulo: string; caminho: string }): string {
  const bruto = fonte.titulo || (fonte.caminho.split('/').pop() ?? '')
  return bruto.replace(/\.pdf$/i, '').replace(/_+/g, ' ').replace(/\s+/g, ' ').trim()
}

/**
 * O índice do livro devolve a página em volta do exercício (46, 47, 48…). Para a questão aberta, só interessa o item
 * dela e, se houver, o enunciado do bloco ("45–50 Faça o mapa de contorno."). Sem numeração reconhecível, tudo.
 */
export function trechoDoExercicio(trecho: string, rotulo: string): string {
  const linhas = trecho.split('\n')
  const item = (l: string) => l.trim().match(/^(\d+)[.)]\s/)
  const bloco = (l: string) => l.trim().match(/^(\d+)\s*[–-]\s*(\d+)\s/)
  const inicio = linhas.findIndex((l) => item(l)?.[1] === rotulo)
  if (inicio < 0) return trecho
  let fim = inicio + 1
  while (fim < linhas.length && !item(linhas[fim]) && !bloco(linhas[fim])) fim++
  const n = Number(rotulo)
  let cabeca: string | null = null
  for (let i = inicio - 1; i >= 0; i--) {
    const b = bloco(linhas[i])
    if (b) { if (Number(b[1]) <= n && n <= Number(b[2])) cabeca = linhas[i].trim(); break }
  }
  return [...(cabeca ? [cabeca] : []), ...linhas.slice(inicio, fim).map((l) => l.trim())].join('\n')
}

/**
 * Primeira linha do foco de uma sessão do plano em título e detalhe, como no motor (progresso.py):
 * "**15.5 Aplicações** — massa, centro de massa" → { titulo: '15.5 Aplicações', detalhe: 'massa, centro de massa' }.
 */
export function focoDaSessao(foco: string): { titulo: string; detalhe: string } {
  const primeira = foco.split('\n').map((l) => l.trim()).find(Boolean) ?? ''
  const negrito = primeira.match(/\*\*(.+?)\*\*/)
  if (!negrito || negrito.index === undefined) return { titulo: primeira, detalhe: '' }
  const resto = (primeira.slice(0, negrito.index) + primeira.slice(negrito.index + negrito[0].length)).trim()
  return { titulo: negrito[1].trim(), detalhe: resto.replace(/^[—–\-·\s]+/, '').trim() }
}

/**
 * Classe visual de cada estado derivado do tópico: em dia (verde), falta praticar (tinta, peso), hoje (brasa); o resto
 * em tinta suave. Os nomes vêm do motor (progresso.py).
 */
export const CLASSE_ESTADO_TOPICO: Record<string, string> = {
  hoje: 'hoje', 'em dia': 'emdia', 'falta praticar': 'falta', 'a seguir': 'seguir', 'prova passou': 'passou',
}

/** O que cada estado do tópico quer dizer (a mesma frase da folha de ajuda), para a dica ao passar o mouse. */
export const DEFINICAO_ESTADO: Record<string, string> = {
  hoje: 'é o tópico da sessão do dia',
  'em dia': 'a aula já passou e você trabalhou metade ou mais das questões (ou o tópico não tem questões)',
  'falta praticar': 'a aula já passou e você trabalhou menos da metade das questões',
  'a seguir': 'a aula ainda não chegou (o número ao lado mostra se você já adiantou)',
  'prova passou': 'a prova da unidade já foi; o número ao lado mostra quanto você praticou',
}

/** Remove a primeira linha "# título" do texto quando repete o título já mostrado no cabeçalho. */
export function semTituloRepetido(corpo: string, titulo: string): string {
  const normal = (s: string) => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
  const linhas = corpo.split('\n')
  const i = linhas.findIndex((l) => l.trim())
  if (i < 0) return corpo
  const m = linhas[i].match(/^#\s+(.+)$/)
  return m && normal(m[1]) === normal(titulo) ? linhas.slice(i + 1).join('\n') : corpo
}

/** O título cita a seção pelo código ("Massa (15.5)" cita 15.5, mas não 15.50 nem 115.5) — a mesma regra do motor. */
export function citaSecao(titulo: string, codigo: string): boolean {
  const escapado = codigo.replace(/\./g, '\\.')
  return new RegExp(`(?<![\\d.])${escapado}(?![\\d.])`).test(titulo)
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
