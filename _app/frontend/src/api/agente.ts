// Conversa com o assistente: a resposta chega aos pedaços (uma linha JSON por evento). É o único lugar, além do
// cliente.ts, que chama fetch direto — o cliente comum lê a resposta inteira de uma vez.
import { API_BASE, ErroApi, MotorDesligado } from './cliente'
import type { PedidoAgente } from './tipos'

export type EventoAgente =
  | { tipo: 'texto'; dados: { texto: string } }
  | { tipo: 'ferramenta'; dados: { nome: string; aviso: string } }
  | { tipo: 'gravado'; dados: { tipo: string; id: number; titulo: string; grupo_id: number } }
  | { tipo: 'confirmar'; dados: { total_mes: number; teto: number } }
  | { tipo: 'erro'; dados: { motivo: string; detalhe: string } }
  | { tipo: 'fim'; dados: { custo_brl: number; total_mes: number } }

export async function conversar(uid: string, pedido: PedidoAgente, aoEvento: (e: EventoAgente) => void, sinal?: AbortSignal): Promise<void> {
  let resposta: Response
  try {
    resposta = await fetch(`${API_BASE}/api/materias/${uid}/agente/mensagem`, {
      method: 'POST', body: JSON.stringify(pedido), headers: { 'content-type': 'application/json' }, signal: sinal,
    })
  } catch (e) {
    if ((e as Error).name === 'AbortError') return
    throw new MotorDesligado()
  }
  if (!resposta.ok || !resposta.body) {
    let mensagem = `Erro no motor (${resposta.status})`
    try { mensagem = (await resposta.json()).erro ?? mensagem } catch { /* corpo sem JSON */ }
    throw new ErroApi(mensagem, resposta.status)
  }
  const leitor = resposta.body.getReader()
  const decodificador = new TextDecoder()
  let resto = ''
  for (;;) {
    const { value, done } = await leitor.read()
    resto += decodificador.decode(value ?? new Uint8Array(), { stream: !done })
    const linhas = resto.split('\n')
    resto = linhas.pop() ?? ''
    for (const linha of linhas) if (linha.trim()) aoEvento(JSON.parse(linha) as EventoAgente)
    if (done) break
  }
  if (resto.trim()) aoEvento(JSON.parse(resto) as EventoAgente)
}
