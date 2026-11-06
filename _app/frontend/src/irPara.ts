// "Ir para" da busca (Ctrl K): destinos que não são texto — áreas, unidades, tópicos da unidade e questões pelo código
// ("14.1 46", "L5 #8"). Tudo local, a partir do painel já carregado; a busca no conteúdo continua no motor.
import type { Painel } from './api/tipos'
import { montarHash, type Area } from './rotas/rota'

export type Destino = { rotulo: string; detalhe: string; href: string }

const AREAS: [Area | 'importar' | 'historico', string, string[]][] = [
  ['painel', 'Hoje', ['hoje', 'inicio', 'sessao', 'painel']],
  ['topicos', 'Tópicos', ['topicos', 'topico', 'mapa']],
  ['listas', 'Praticar', ['praticar', 'listas', 'questoes', 'exercicios']],
  ['documentos', 'Biblioteca', ['biblioteca', 'documentos', 'resumos', 'pdfs']],
  ['cronograma', 'Plano completo', ['plano', 'cronograma', 'sessoes', 'calendario']],
  ['formulario', 'Folha de fórmulas', ['formulas', 'folha', 'formulario']],
  ['importar', 'Adicionar material', ['material', 'importar', 'adicionar']],
  ['historico', 'Histórico', ['historico', 'desfazer']],
]

const normal = (s: string) => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().trim()

export function destinos(consulta: string, painel: Painel, limite = 8): Destino[] {
  const q = normal(consulta)
  const uid = painel.materia.uid
  const unidade = painel.unidade
  const saida: Destino[] = []
  const area = (a: (typeof AREAS)[number][0]) =>
    a === 'importar' || a === 'historico' ? montarHash({ tela: a, uid }) : montarHash({ tela: 'materia', uid, unidade, area: a })

  // questão pelo código da lista e o número: "14.1 46", "14.1 #46", "l5 8"
  const q2 = q.match(/^([^\s#]+)\s*#?\s*([0-9]+[a-z()]*)$/)
  if (q2) {
    for (const l of painel.listas) {
      if (normal(l.codigo) !== q2[1]) continue
      const questao = l.questoes.find((x) => normal(x.rotulo) === q2[2])
      if (questao) saida.push({ rotulo: `${l.codigo} #${questao.rotulo}`, detalhe: `Praticar · ${l.titulo}`, href: montarHash({ tela: 'materia', uid, unidade, area: 'listas', questao: questao.id }) })
    }
  }
  // unidade: "2", "2ª unidade", "unidade 2"
  const qu = q.match(/^(?:unidade\s*)?([0-9])(?:a|ª)?(?:\s*unidade)?$/)
  if (qu) {
    const n = Number(qu[1])
    if (painel.unidades.some((u) => u.numero === n)) saida.push({ rotulo: `${n}ª unidade`, detalhe: 'Hoje desta unidade', href: montarHash({ tela: 'materia', uid, unidade: n, area: 'painel' }) })
  }
  for (const [a, nome, chaves] of AREAS) {
    if (!q || chaves.some((c) => c.startsWith(q) || (q.length >= 3 && c.includes(q)))) saida.push({ rotulo: nome, detalhe: 'Ir para', href: area(a) })
  }
  if (q.length >= 3) {
    for (const t of painel.topicos) {
      if (normal(t.titulo).includes(q)) {
        saida.push({ rotulo: t.titulo, detalhe: 'Tópico', href: montarHash({ tela: 'materia', uid, unidade, area: 'topicos', topico: t.id }) })
      }
    }
  }
  return saida.slice(0, limite)
}
