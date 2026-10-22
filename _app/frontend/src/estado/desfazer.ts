// Desfazer a última ação (botão ↩ do topo e Ctrl+Z em qualquer tela).
import { requisitar } from '../api/cliente'
import type { Desfeito } from '../api/tipos'
import { avisar, erro } from './avisos.svelte'
import { estadoMateria, recarregar } from './materia.svelte'

/** Ouvintes extras de "algo foi desfeito" (ex.: a tela de histórico relê a lista). */
const aoDesfazer = new Set<() => void>()

export function quandoDesfizer(f: () => void): () => void {
  aoDesfazer.add(f)
  return () => aoDesfazer.delete(f)
}

export async function desfazer(): Promise<void> {
  if (!estadoMateria.uid) return
  try {
    const r = await requisitar<Desfeito>('POST', `/api/materias/${estadoMateria.uid}/historico/desfazer`)
    if (!r.desfeito) {
      avisar('Nada para desfazer')
      return
    }
    avisar(`Desfeito: ${r.desfeito.descricao}`)
    await recarregar()
    aoDesfazer.forEach((f) => f())
  } catch (e) {
    erro(e)
  }
}

/** Ctrl+Z (ou Cmd+Z) fora de campos de texto, onde o Ctrl+Z continua sendo o do próprio campo. */
export function atalhoDesfazer(e: KeyboardEvent): boolean {
  if (!(e.ctrlKey || e.metaKey) || e.shiftKey || e.altKey || e.key.toLowerCase() !== 'z') return false
  const alvo = e.target as HTMLElement | null
  if (alvo && (alvo.closest?.('input, textarea, select, [contenteditable=""], [contenteditable="true"]'))) return false
  return true
}
