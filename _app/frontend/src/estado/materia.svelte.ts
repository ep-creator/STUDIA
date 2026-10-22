// Matéria e unidade abertas. O painel (uma chamada) alimenta Painel, Tópicos, Listas, Cronograma e Formulário;
// toda escrita que não seja marcação termina em recarregar(), porque as regras derivadas vivem no motor.
import { ErroApi, requisitar } from '../api/cliente'
import type { Painel } from '../api/tipos'
import type { Rota } from '../rotas/rota'
import { erro } from './avisos.svelte'

export const estadoMateria = $state<{
  uid: string | null
  unidade: number | null
  painel: Painel | null
  carregando: boolean
}>({ uid: null, unidade: null, painel: null, carregando: false })

/** Qual painel a rota pede, ou null se o que está carregado já serve. Outra matéria nunca herda a unidade da anterior. */
export function painelACarregar(
  rota: Rota,
  atual: { uid: string | null; unidade: number | null },
): { uid: string; unidade: number | null } | null {
  if (rota.tela === 'materias') return null
  const pedida = rota.tela === 'materia' ? rota.unidade : null
  if (rota.uid !== atual.uid) return { uid: rota.uid, unidade: pedida }
  if (pedida !== null && pedida !== atual.unidade) return { uid: rota.uid, unidade: pedida }
  return null
}

export async function carregarPainel(uid: string, unidade: number | null = null): Promise<void> {
  estadoMateria.carregando = true
  try {
    const consulta = unidade === null ? '' : `?unidade=${unidade}`
    let painel: Painel
    try {
      painel = await requisitar<Painel>('GET', `/api/materias/${encodeURIComponent(uid)}/painel${consulta}`)
    } catch (e) {
      // Unidade de um favorito antigo (ou apagada): mostra a unidade atual da matéria em vez de travar
      if (!(e instanceof ErroApi && e.status === 404 && unidade !== null)) throw e
      painel = await requisitar<Painel>('GET', `/api/materias/${encodeURIComponent(uid)}/painel`)
    }
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
