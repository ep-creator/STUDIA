// Pedido de abrir algo já selecionado na próxima tela (ex.: o painel abre uma questão nas Listas ou um resumo
// em Documentos). Quem abre a tela consome o pedido uma vez e o limpa.
export const pedido = $state<{ questao: number | null; documento: number | null }>({ questao: null, documento: null })

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
