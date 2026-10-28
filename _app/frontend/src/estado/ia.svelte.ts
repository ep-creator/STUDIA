// Área de IA à direita: começa sempre fechada; telas que precisam de espaço (ex.: uma resolução aberta) a recolhem.
// `alvo`/`papel` trocam a conversa do painel (ex.: "Resumir a seção" em Documentos abre o resumidor da seção) e
// `pendente` é um atalho a disparar assim que o painel abrir. `versaoChave` muda quando a chave é salva, para os
// dois painéis (o da questão e o lateral) esconderem a caixa juntos.
export const ia = $state<{ aberta: boolean; alvo: string | null; papel: string | null; pendente: string | null; versaoChave: number }>({
  aberta: false, alvo: null, papel: null, pendente: null, versaoChave: 0,
})

export function abrirNoPainel(alvo: string, papel: string, atalho: string | null = null): void {
  ia.alvo = alvo
  ia.papel = papel
  ia.pendente = atalho
  ia.aberta = true
}
