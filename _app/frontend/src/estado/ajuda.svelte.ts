// A folha de atalhos e ajuda (tecla ?, ou o link da barra lateral).
export const ajuda = $state<{ aberta: boolean }>({ aberta: false })

/** O alvo do teclado é um campo de texto? Então as teclas soltas (1, 2, ?, N…) são do texto, não atalhos. */
export function digitando(alvo: EventTarget | null): boolean {
  const el = alvo as HTMLElement | null
  return !!el && (el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName))
}
