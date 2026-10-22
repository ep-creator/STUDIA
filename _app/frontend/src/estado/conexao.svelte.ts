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

/** Testa o motor e, se estiver desligado, repete até ele voltar. Chamadas simultâneas compartilham a mesma espera. */
export function verificarMotor(): Promise<void> {
  verificando ??= (async () => {
    while (!(await motorResponde())) {
      conexao.motorLigado = false
      await new Promise((r) => setTimeout(r, INTERVALO_RECONEXAO_MS))
    }
    conexao.motorLigado = true
  })().finally(() => { verificando = null })
  return verificando
}
