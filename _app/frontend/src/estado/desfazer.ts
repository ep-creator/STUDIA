// Desfazer a última ação (botão ↩ do topo e Ctrl+Z em qualquer tela).
import { requisitar } from '../api/cliente'
import type { Desfeito, GrupoHistorico } from '../api/tipos'
import { avisar, erro } from './avisos.svelte'
import { estadoMateria, recarregar } from './materia.svelte'

/** Ouvintes extras de "algo foi desfeito" (ex.: a tela de histórico relê a lista). */
const aoDesfazer = new Set<() => void>()

export function quandoDesfizer(f: () => void): () => void {
  aoDesfazer.add(f)
  return () => aoDesfazer.delete(f)
}

/** A ação que o Desfazer vai desfazer: a mais recente que não foi desfeita e não é ela mesma um desfazer. */
export async function alvoDoDesfazer(): Promise<GrupoHistorico | null> {
  if (!estadoMateria.uid) return null
  const grupos = await requisitar<GrupoHistorico[]>('GET', `/api/materias/${estadoMateria.uid}/historico?limite=30`)
  return Array.isArray(grupos) ? grupos.find((g) => !g.desfeito_em && g.desfaz_grupo === null) ?? null : null
}

const UMA_HORA = 60 * 60 * 1000

/**
 * Desfaz a última ação. Se ela tem mais de uma hora (outro dia de estudo, uma resolução da IA de ontem…), primeiro diz
 * qual é e só desfaz se a pessoa confirmar no aviso: desfazer às cegas o que não se lembra de ter feito assusta.
 */
export async function desfazer(): Promise<void> {
  if (!estadoMateria.uid) return
  // sem conseguir ler o histórico, desfaz direto (o motor é quem diz se há o que desfazer)
  const alvo = await alvoDoDesfazer().catch(() => null)
  if (alvo && Date.now() - new Date(alvo.momento).getTime() > UMA_HORA) {
      const quando = new Date(alvo.momento).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
    avisar(`A última ação é de ${quando}: ${alvo.descricao}`, { rotulo: 'Desfazer mesmo', executar: () => void desfazerJa() })
    return
  }
  await desfazerJa()
}

async function desfazerJa(): Promise<void> {
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
