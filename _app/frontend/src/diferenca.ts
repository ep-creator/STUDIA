// Diferença por linhas (maior subsequência comum), para o "ver diferença" do histórico.

export type LinhaDiferenca = { tipo: 'igual' | 'removida' | 'adicionada'; texto: string }

export function diferencaLinhas(antes: string | null, depois: string | null): LinhaDiferenca[] {
  const a = antes === null ? [] : antes.split('\n')
  const b = depois === null ? [] : depois.split('\n')
  // comum[i][j] = tamanho da maior subsequência comum entre a[i:] e b[j:]
  const comum = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0))
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      comum[i][j] = a[i] === b[j] ? comum[i + 1][j + 1] + 1 : Math.max(comum[i + 1][j], comum[i][j + 1])
    }
  }
  const saida: LinhaDiferenca[] = []
  let i = 0
  let j = 0
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      saida.push({ tipo: 'igual', texto: a[i] })
      i++
      j++
    } else if (comum[i + 1][j] >= comum[i][j + 1]) {
      saida.push({ tipo: 'removida', texto: a[i++] })
    } else {
      saida.push({ tipo: 'adicionada', texto: b[j++] })
    }
  }
  while (i < a.length) saida.push({ tipo: 'removida', texto: a[i++] })
  while (j < b.length) saida.push({ tipo: 'adicionada', texto: b[j++] })
  return saida
}
