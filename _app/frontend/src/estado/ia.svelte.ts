// Assistente: a gaveta à direita (começa fechada) e a conversa que a página do Assistente abre ao chegar.
// `alvo`/`papel` trocam a conversa do painel (ex.: "Resumir a seção" em Documentos abre o resumidor da seção) e
// `pendente` é um atalho a disparar assim que o painel abrir. `versaoChave` muda quando a chave é salva, para os
// dois painéis (o da questão e o lateral) esconderem a caixa juntos.
export const ia = $state<{ aberta: boolean; alvo: string | null; papel: string | null; pendente: string | null; versaoChave: number }>({
  aberta: false, alvo: null, papel: null, pendente: null, versaoChave: 0,
})

/** Atalhos de cada papel: N1–N4 no tutor, Resumir no resumidor, Plano de revisão no estrategista. */
export function atalhosDoPapel(papel: string): string[] {
  return papel === 'tutor' ? ['N1', 'N2', 'N3', 'N4'] : papel === 'resumidor' ? ['resumir'] : ['plano']
}

/** Leva a conversa aberta na gaveta para a página do Assistente. */
export function abrirNaPagina(uid: string, alvo: string, papel: string): void {
  ia.alvo = alvo
  ia.papel = papel
  ia.aberta = false
  location.hash = `#/m/${encodeURIComponent(uid)}/assistente`
}

export function abrirNoPainel(alvo: string, papel: string, atalho: string | null = null): void {
  ia.alvo = alvo
  ia.papel = papel
  ia.pendente = atalho
  ia.aberta = true
}
