// Matéria e unidade abertas. O painel (uma chamada) alimenta Painel, Tópicos, Listas, Cronograma e Formulário;
// toda escrita que não seja marcação termina em recarregar(), porque as regras derivadas vivem no motor.
import { requisitar } from '../api/cliente'
import type { Painel } from '../api/tipos'
import { erro } from './avisos.svelte'

export const estadoMateria = $state<{
  uid: string | null
  unidade: number | null
  painel: Painel | null
  carregando: boolean
}>({ uid: null, unidade: null, painel: null, carregando: false })

export async function carregarPainel(uid: string, unidade: number | null = null): Promise<void> {
  estadoMateria.carregando = true
  try {
    const consulta = unidade === null ? '' : `?unidade=${unidade}`
    const painel = await requisitar<Painel>('GET', `/api/materias/${encodeURIComponent(uid)}/painel${consulta}`)
    Object.assign(estadoMateria, { uid, unidade: painel.unidade, painel })
  } catch (e) {
    erro(e)
  } finally {
    estadoMateria.carregando = false
  }
}

export function recarregar(): Promise<void> {
  if (!estadoMateria.uid) return Promise.resolve()
  return carregarPainel(estadoMateria.uid, estadoMateria.unidade)
}
