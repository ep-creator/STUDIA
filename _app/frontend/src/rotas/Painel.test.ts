import { render, screen } from '@testing-library/svelte'
import { expect, test } from 'vitest'
import { lista, painel, painelVazio, questao, topico } from '../teste-dados'
import Painel from './Painel.svelte'

const hoje = new Date(2026, 8, 2)

test('painel de matéria vazia leva à importação', () => {
  render(Painel, { painel: painelVazio, hoje })
  expect(screen.getByText(/Envie o programa/)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /Importar/ })).toHaveAttribute('href', '#/m/ab/importar')
})

test('contagem, progresso e pendências da unidade', () => {
  render(Painel, {
    hoje,
    painel: painel({
      topicos: [topico(1, 'visto'), topico(2, 'proxima', { titulo: 'Derivadas parciais' }), topico(3, 'pendente')],
      eventos: [{ id: 9, tipo: 'prova', data: '2026-09-14', hora_inicio: '14:30', hora_fim: null, unidade_id: 1, descricao: '', origem: 'importado' }],
      importacoes_pendentes: 2,
    }),
  })
  expect(screen.getByText('12 dias')).toBeInTheDocument()
  expect(screen.getByText(/14:30/)).toBeInTheDocument()
  expect(screen.getByRole('region', { name: 'Tópicos vistos' })).toHaveTextContent('1/3')
  expect(screen.getByRole('link', { name: /Derivadas parciais/ })).toHaveAttribute('href', '#/m/ab/u/1/topicos')
  expect(screen.getByRole('link', { name: /2 importações esperando revisão/ })).toHaveAttribute('href', '#/m/ab/importar')
})

test('para revisar lista as questões ✗ e ? e abre cada uma direto nas listas', async () => {
  const { pedido } = await import('../estado/pedido.svelte')
  render(Painel, {
    hoje,
    painel: painel({
      listas: [lista(1, '14.1', [questao(10, '22'), questao(11, '46'), questao(12, '50')])],
      marcacoes: { '10': 'ok', '11': 'err', '12': 'dub' },
    }),
  })
  const link = screen.getByRole('link', { name: /14\.1 #46/ })
  expect(link).toHaveAttribute('href', '#/m/ab/u/1/listas')
  expect(screen.getByRole('link', { name: /14\.1 #50/ })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: /14\.1 #22/ })).toBeNull()
  link.click()
  expect(pedido.questao).toBe(11)
  // desempenho da lista: 3 de 3 feitas
  expect(screen.getByRole('region', { name: 'Desempenho nas listas' })).toHaveTextContent('3/3')
})

const RESUMO = {
  id: 7, tipo: 'resumo', titulo: 'Valores máximo e mínimo', caminho: 'r.md', unidade_id: 1, secao_id: 42, questao_id: null,
  origem: 'manual', atualizado_em: '2026-10-26', secao_decidida: false, secao_codigo: '14.7', secao_posicao: 9,
}
const VINCULO = {
  topicos: { '2': [{ secao_id: 42, codigo: '14.7', titulo: 'Valores Máximo e Mínimo', fonte_id: 1, caminho: 'l.pdf', pagina_pdf_ini: 361 }] },
  listas: {},
}

test('faixa de cima: próxima aula com ler o resumo (achado pela seção); sem semana nem próximo passo', async () => {
  const { pedido } = await import('../estado/pedido.svelte')
  const outro = { ...RESUMO, id: 8, titulo: 'Extremos absolutos', secao_id: 99, secao_codigo: '15.4' }
  render(Painel, {
    hoje,
    painel: painel({
      topicos: [topico(1, 'visto'), topico(2, 'proxima', { titulo: 'Extremos absolutos em região fechada' })],
      documentos: [outro, RESUMO],
      vinculos: VINCULO,
    }),
  })
  expect(screen.getByRole('region', { name: 'Próxima aula' })).toHaveTextContent('Extremos absolutos em região fechada')
  screen.getByRole('link', { name: 'ler o resumo' }).click()
  expect(pedido.documento).toBe(7)
  expect(screen.queryByRole('region', { name: 'Semana' })).toBeNull()
  expect(screen.queryByText(/Próximo passo/)).toBeNull()
})

test('prova que já passou mostra feita e a data', () => {
  render(Painel, {
    hoje: new Date(2026, 9, 28),
    painel: painel({ eventos: [{ id: 9, tipo: 'prova', data: '2026-09-14', hora_inicio: null, hora_fim: null, unidade_id: 1, descricao: '', origem: 'importado' }] }),
  })
  const prova = screen.getByRole('region', { name: 'Prova' })
  expect(prova).toHaveTextContent('feita')
  expect(prova).toHaveTextContent(/14\/09/)
})

test('sem tópico pendente, a próxima aula some', () => {
  render(Painel, { hoje, painel: painel({ topicos: [topico(1, 'visto'), topico(2, 'visto')] }) })
  expect(screen.queryByRole('region', { name: 'Próxima aula' })).toBeNull()
})

test('para revisar agrupa por lista e mostra só os números', () => {
  render(Painel, {
    hoje,
    painel: painel({
      listas: [lista(1, '14.1', [questao(10, '46', { enunciado_md: 'Faça o **mapa de contorno**.' }), questao(11, '50')])],
      marcacoes: { '10': 'err', '11': 'err' },
    }),
  })
  const revisar = screen.getByRole('region', { name: 'Para revisar' })
  expect(revisar).toHaveTextContent('Para revisar · 2')
  expect([...revisar.querySelectorAll('a')].map((a) => a.textContent?.trim())).toEqual(['46', '50'])
  expect(screen.queryByText(/mapa de contorno/i)).toBeNull()
})

test('sem marcação: Nada para revisar ainda. e acerto —', () => {
  render(Painel, { hoje, painel: painel({ listas: [lista(1, '14.1', [questao(10, '1')])], marcacoes: {} }) })
  expect(screen.getByText('Nada para revisar ainda.')).toBeInTheDocument()
  expect(screen.getByRole('region', { name: 'Desempenho nas listas' })).toHaveTextContent(/—\s*de acerto/)
})
