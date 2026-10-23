// Alterações não salvas (o editor de documentos): trocar de documento, de tela ou fechar a aba pergunta antes.

const pendentes = new Set<string>()

export function marcarAlteracoes(chave: string, alterado: boolean): void {
  if (alterado) pendentes.add(chave)
  else pendentes.delete(chave)
}

export function haAlteracoes(): boolean {
  return pendentes.size > 0
}

/** true se pode sair: sem alterações, ou o usuário aceitou descartá-las (que então deixam de contar). */
export function podeSair(): boolean {
  if (!haAlteracoes()) return true
  if (!confirm('Há um texto não salvo neste documento. Sair e descartar as alterações?')) return false
  pendentes.clear()
  return true
}
