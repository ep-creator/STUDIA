// Estado da conexão com o motor: quando ele cai, a faixa avisa e o app tenta de novo a cada 3 s.
import { API_BASE } from '../api/cliente'

export const INTERVALO_RECONEXAO_MS = 3000

export const conexao = $state({ motorLigado: true })

let verificando: Promise<void> | null = null

async function motorResponde(): Promise<boolean> {
  try {
    return (await fetch(`${API_BASE}/api/materias`)).ok
  } catch {
    return false
  }
}

const aoVoltar = new Set<() => void>()

/** Avisa quando o motor volta depois de cair (para recarregar o que falhou enquanto estava fora). */
export function aoReconectar(f: () => void): () => void {
  aoVoltar.add(f)
  return () => aoVoltar.delete(f)
}

/** Testa o motor e, se estiver desligado, repete até ele voltar. Chamadas simultâneas compartilham a mesma espera. */
export function verificarMotor(): Promise<void> {
  verificando ??= (async () => {
    let caiu = false
    while (!(await motorResponde())) {
      caiu = true
      conexao.motorLigado = false
      await new Promise((r) => setTimeout(r, INTERVALO_RECONEXAO_MS))
    }
    conexao.motorLigado = true
    if (caiu) aoVoltar.forEach((f) => f())
  })().finally(() => { verificando = null })
  return verificando
}
