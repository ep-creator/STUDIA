// Avisos curtos no canto da tela ("Questão 15.4 #11 marcada ✗ · Desfazer"), com ação opcional.
import { ErroApi, MotorDesligado } from '../api/cliente'
import { verificarMotor } from './conexao.svelte'

export type AcaoAviso = { rotulo: string; executar: () => void }
export type Aviso = { id: number; texto: string; tipo: 'info' | 'erro'; acao?: AcaoAviso }

export const DURACAO_AVISO_MS = 5000

export const avisos = $state<{ lista: Aviso[] }>({ lista: [] })

let proximoId = 1

function adicionar(texto: string, tipo: Aviso['tipo'], acao?: AcaoAviso): void {
  const aviso = { id: proximoId++, texto, tipo, acao }
  avisos.lista.push(aviso)
  setTimeout(() => fecharAviso(aviso.id), DURACAO_AVISO_MS)
}

export function fecharAviso(id: number): void {
  avisos.lista = avisos.lista.filter((a) => a.id !== id)
}

export function avisar(texto: string, acao?: AcaoAviso): void {
  adicionar(texto, 'info', acao)
}

/** Mostra a mensagem do motor; motor fora do ar aciona a faixa e a reconexão em vez de um aviso. */
export function erro(e: unknown): void {
  if (e instanceof MotorDesligado) {
    void verificarMotor()
    return
  }
  adicionar(e instanceof ErroApi || e instanceof Error ? e.message : String(e), 'erro')
}
