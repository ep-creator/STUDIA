// A IA da matéria: a gaveta à direita (começa fechada).
// `alvo`/`papel` trocam a conversa do painel (ex.: "Resumir a seção" em Documentos abre o resumidor da seção) e
// `pendente` é um atalho a disparar assim que o painel abrir. `versaoChave` muda quando a chave é salva, para os
// dois painéis (o da questão e o lateral) esconderem a caixa juntos.
export const ia = $state<{
  aberta: boolean; alvo: string | null; papel: string | null; pendente: string | null; versaoChave: number
}>({
  aberta: false, alvo: null, papel: null, pendente: null, versaoChave: 0,
})

/** Atalhos de cada papel: N1–N4 no tutor, Resumir no resumidor, Plano de revisão no estrategista. */
export function atalhosDoPapel(papel: string): string[] {
  return papel === 'tutor' ? ['N1', 'N2', 'N3', 'N4'] : papel === 'resumidor' ? ['resumir'] : ['plano']
}

export function abrirNoPainel(alvo: string, papel: string, atalho: string | null = null): void {
  ia.alvo = alvo
  ia.papel = papel
  ia.pendente = atalho
  ia.aberta = true
}
