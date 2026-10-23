// Grupos que abrem e fecham pela setinha (documentos, listas…). Os fechados ficam lembrados neste navegador;
// é só conveniência: sem armazenamento, tudo começa aberto.

export function recolhidos(chave: string) {
  let fechados = $state<string[]>(ler(chave))
  return {
    aberto: (grupo: string) => !fechados.includes(grupo),
    alternar(grupo: string) {
      fechados = fechados.includes(grupo) ? fechados.filter((g) => g !== grupo) : [...fechados, grupo]
      try { localStorage.setItem(chave, JSON.stringify(fechados)) } catch { /* segue sem lembrar */ }
    },
  }
}

function ler(chave: string): string[] {
  try {
    const salvo = JSON.parse(localStorage.getItem(chave) ?? '[]')
    return Array.isArray(salvo) ? salvo : []
  } catch {
    return []
  }
}
