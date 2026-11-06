// Grupos que abrem e fecham pela setinha (documentos, listas…). Os fechados ficam lembrados neste navegador;
// é só conveniência. Antes da primeira escolha, valem os `padrao` (o que a tela prefere começar fechado).

export function recolhidos(chave: string, padrao: string[] = []) {
  let fechados = $state<string[]>(ler(chave) ?? padrao)
  return {
    aberto: (grupo: string) => !fechados.includes(grupo),
    alternar(grupo: string) {
      fechados = fechados.includes(grupo) ? fechados.filter((g) => g !== grupo) : [...fechados, grupo]
      try { localStorage.setItem(chave, JSON.stringify(fechados)) } catch { /* segue sem lembrar */ }
    },
  }
}

function ler(chave: string): string[] | null {
  try {
    const texto = localStorage.getItem(chave)
    if (texto === null) return null
    const salvo = JSON.parse(texto)
    return Array.isArray(salvo) ? salvo : null
  } catch {
    return null
  }
}
