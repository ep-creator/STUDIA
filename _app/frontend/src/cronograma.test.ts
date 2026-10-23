import { expect, test } from 'vitest'
import type { Evento, Sessao } from './api/tipos'
import { agruparFormulas, montarLinhaDoTempo } from './cronograma'

function sessao(id: number, data: string | null, ordem = id): Sessao {
  return { id, unidade_id: 1, codigo: `S${id}`, data, foco_md: '', feito: false, ordem, origem: 'manual', questao_ids: [] }
}

function evento(id: number, tipo: string, data: string, hora: string | null = null): Evento {
  return { id, tipo, data, hora_inicio: hora, hora_fim: null, unidade_id: 1, descricao: '', origem: 'importado' }
}

test('linha do tempo mistura sessões e eventos por data e hora', () => {
  const linha = montarLinhaDoTempo(
    [sessao(1, '2026-09-09'), sessao(2, null)],
    [evento(1, 'prova', '2026-09-14', '14:30'), evento(2, 'aula', '2026-09-09')],
  )
  expect(linha.map((i) => [i.data, i.tipo])).toEqual([
    ['2026-09-09', 'aula'], ['2026-09-09', 'sessao'], ['2026-09-14', 'prova'], [null, 'sessao'],
  ])
})

test('sessões sem data ficam no fim pela ordem', () => {
  const linha = montarLinhaDoTempo([sessao(1, null, 5), sessao(2, null, 2)], [])
  expect(linha.map((i) => i.sessao?.id)).toEqual([2, 1])
})

test('fórmulas agrupadas pelo tópico ligado à seção', () => {
  const formulas = [
    { id: 1, unidade_id: 1, secao_id: 10, titulo: 'Cadeia', corpo_tex: 'a', notas_md: '', ordem: 1, origem: 'manual' },
    { id: 2, unidade_id: 1, secao_id: null, titulo: 'Solta', corpo_tex: 'b', notas_md: '', ordem: 2, origem: 'manual' },
  ]
  const topicos = [{ id: 5, unidade_id: 1, pai_id: null, ordem: 1, titulo: 'Regra da cadeia', status: 'pendente', origem: 'importado', detalhe_md: '' }]
  const vinculos = { '5': [{ secao_id: 10, codigo: '14.5', titulo: 'A Regra da Cadeia', fonte_id: 1, caminho: 'l.pdf', pagina_pdf_ini: 400 }] }
  expect(agruparFormulas(formulas, topicos, vinculos).map(([t, fs]) => [t, fs.map((f) => f.id)])).toEqual([
    ['Regra da cadeia', [1]], ['Sem tópico', [2]],
  ])
})
