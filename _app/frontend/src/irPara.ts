// "Ir para" da busca (Ctrl K): destinos que não são texto — áreas, unidades, tópicos da unidade e questões pelo código
// ("14.1 46", "L5 #8"). Tudo local, a partir do painel já carregado; a busca no conteúdo continua no motor.
import type { Indice, Painel } from './api/tipos'
import { montarHash, type Area } from './rotas/rota'

export type Destino = { rotulo: string; detalhe: string; href: string }

const AREAS: [Area | 'importar' | 'historico', string, string[]][] = [
  ['painel', 'Hoje', ['hoje', 'inicio', 'sessao', 'painel']],
  ['topicos', 'Tópicos', ['topicos', 'topico', 'mapa']],
  ['listas', 'Praticar', ['praticar', 'listas', 'questoes', 'exercicios']],
  ['documentos', 'Biblioteca', ['biblioteca', 'documentos', 'resumos', 'pdfs']],
  ['cronograma', 'Plano', ['plano', 'cronograma', 'sessoes', 'calendario']],
  ['formulario', 'Folha de fórmulas', ['formulas', 'folha', 'formulario']],
  ['importar', 'Adicionar material', ['material', 'importar', 'adicionar']],
  ['historico', 'Histórico', ['historico', 'desfazer']],
]

const normal = (s: string) => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().trim()

export function destinos(consulta: string, painel: Painel, indice: Indice | null = null, limite = 8): Destino[] {
  const q = normal(consulta)
  const uid = painel.materia.uid
  const unidade = painel.unidade
  const saida: Destino[] = []
  const area = (a: (typeof AREAS)[number][0]) =>
    a === 'importar' || a === 'historico' ? montarHash({ tela: a, uid }) : montarHash({ tela: 'materia', uid, unidade, area: a })

  // questão pelo código da lista e o número: "14.1 46", "14.1 #46", "l5 8"
  const q2 = q.match(/^([^\s#]+)\s*#?\s*([0-9]+[a-z()]*)$/)
  if (q2) {
    // com o índice, a matéria toda (a questão abre na unidade dela); sem ele, as listas da unidade aberta
    const questoes = indice?.questoes ?? painel.listas.flatMap((l) => l.questoes.map((x) => ({
      id: x.id, rotulo: x.rotulo, lista_codigo: l.codigo, lista_titulo: l.titulo, unidade: unidade ?? 1,
    })))
    for (const x of questoes) {
      if (normal(x.lista_codigo) !== q2[1] || normal(x.rotulo) !== q2[2]) continue
      const outra = x.unidade !== unidade ? ` · ${x.unidade}ª unidade` : ''
      saida.push({ rotulo: `${x.lista_codigo} #${x.rotulo}`, detalhe: `Praticar · ${x.lista_titulo}${outra}`, href: montarHash({ tela: 'materia', uid, unidade: x.unidade, area: 'listas', questao: x.id }) })
    }
  }
  // unidade: "2", "2ª unidade", "unidade 2"
  const qu = q.match(/^(?:unidade\s*)?([0-9])(?:a|ª)?(?:\s*unidade)?$/)
  if (qu) {
    const n = Number(qu[1])
    if (painel.unidades.some((u) => u.numero === n)) saida.push({ rotulo: `${n}ª unidade`, detalhe: 'Hoje desta unidade', href: montarHash({ tela: 'materia', uid, unidade: n, area: 'painel' }) })
  }
  AREAS.forEach(([a, nome, chaves], i) => {
    const atalho = i < 4 ? ` · Alt ${i + 1}` : ''
    if (!q || chaves.some((c) => c.startsWith(q) || (q.length >= 3 && c.includes(q)))) saida.push({ rotulo: nome, detalhe: `Ir para${atalho}`, href: area(a) })
  })
  if (q.length >= 3) {
    const topicos = indice?.topicos ?? painel.topicos.map((t) => ({ id: t.id, titulo: t.titulo, unidade: unidade ?? 1 }))
    for (const t of topicos) {
      if (normal(t.titulo).includes(q)) {
        const outra = t.unidade !== unidade ? ` · ${t.unidade}ª unidade` : ''
        saida.push({ rotulo: t.titulo, detalhe: `Tópico${outra}`, href: montarHash({ tela: 'materia', uid, unidade: t.unidade, area: 'topicos', topico: t.id }) })
      }
    }
  }
  return saida.slice(0, limite)
}
