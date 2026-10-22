// Marcação de questões: a tela muda na hora (é a ação mais frequente); se o motor recusar, volta e avisa.
// Requisições da mesma questão saem em fila, para a última marca clicada ser a que fica no banco.
import { requisitar } from '../api/cliente'
import type { Marcado } from '../api/tipos'
import { erro } from './avisos.svelte'
import { estadoMateria } from './materia.svelte'

export type Marca = 'ok' | 'err' | 'dub' | null

const CICLO: Marca[] = [null, 'ok', 'err', 'dub']

export function proximaMarca(m: Marca): Marca {
  return CICLO[(CICLO.indexOf(m) + 1) % CICLO.length]
}

export const SIMBOLO: Record<string, string> = { ok: '✓', err: '✗', dub: '?' }

export function marcaDe(questaoId: number): Marca {
  return (estadoMateria.painel?.marcacoes[String(questaoId)] as Marca) ?? null
}

function mostrar(questaoId: number, marca: Marca): void {
  const marcacoes = estadoMateria.painel?.marcacoes
  if (!marcacoes) return
  if (marca === null) delete marcacoes[String(questaoId)]
  else marcacoes[String(questaoId)] = marca
}

const filas = new Map<number, Promise<void>>()
const confirmadas = new Map<number, Marca>()

export function marcar(questaoId: number, marca: Marca): Promise<void> {
  if (!confirmadas.has(questaoId)) confirmadas.set(questaoId, marcaDe(questaoId))
  mostrar(questaoId, marca)
  const uid = estadoMateria.uid
  const anterior = filas.get(questaoId) ?? Promise.resolve()
  const proxima = anterior.then(async () => {
    try {
      const r = await requisitar<Marcado>('PUT', `/api/materias/${uid}/marcacoes/${questaoId}`, { estado: marca })
      confirmadas.set(questaoId, marca)
      if (estadoMateria.painel) estadoMateria.painel.placar = r.placar
    } catch (e) {
      mostrar(questaoId, confirmadas.get(questaoId) ?? null)
      erro(e)
    }
  })
  filas.set(questaoId, proxima)
  void proxima.finally(() => {
    if (filas.get(questaoId) === proxima) {
      filas.delete(questaoId)
      confirmadas.delete(questaoId)
    }
  })
  return proxima
}
