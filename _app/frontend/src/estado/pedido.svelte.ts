// Pedido de abrir algo já selecionado na próxima tela (ex.: o painel abre uma questão nas Listas, a busca abre um PDF
// na página ou um texto no bloco certo em Documentos). Quem abre a tela consome o pedido uma vez e o limpa.
export const pedido = $state<{
  questao: number | null
  documento: number | null
  fonte: { id: number; pagina: number | null } | null
  ancora: string | null
}>({ questao: null, documento: null, fonte: null, ancora: null })

export function consumirQuestao(): number | null {
  const id = pedido.questao
  pedido.questao = null
  return id
}

export function consumirDocumento(): number | null {
  const id = pedido.documento
  pedido.documento = null
  return id
}

export function consumirFonte(): { id: number; pagina: number | null } | null {
  const f = pedido.fonte
  pedido.fonte = null
  return f
}

export function consumirAncora(): string | null {
  const a = pedido.ancora
  pedido.ancora = null
  return a
}
