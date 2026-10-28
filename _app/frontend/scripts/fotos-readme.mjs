// Fotos do README: fotografa as telas principais de uma matéria (sem a janela do app aberta).
// Uso: node scripts/fotos-readme.mjs <baseURL> <uid> <pasta-saida>
// Rode contra uma CÓPIA da matéria, com o servidor em modo de demonstração (ESTUDOS_AGENTE_FALSO=1).
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

const [base, uid, saida] = process.argv.slice(2)
mkdirSync(saida, { recursive: true })
const m = `${base}/#/m/${uid}`

const navegador = await chromium.launch()

async function pagina(modo) {
  const p = await navegador.newPage({ viewport: { width: 1440, height: 900 } })
  await p.addInitScript((modo) => localStorage.setItem('estudos.tema', JSON.stringify({ modo })), modo)
  return p
}

async function foto(p, nome) {
  // a troca de hash não recarrega a página: espera a rede acalmar e a tela desenhar
  await p.waitForLoadState('networkidle')
  await p.waitForTimeout(1600)
  await p.screenshot({ path: join(saida, `${nome}.png`) })
  console.log('ok', nome)
}

const escuro = await pagina('escuro')

await escuro.goto(`${m}/u/3/painel`)
await foto(escuro, 'painel')

await escuro.goto(`${m}/u/1/painel`)
await foto(escuro, 'painel-revisar')

await escuro.goto(`${m}/u/1/listas`)
await escuro.waitForTimeout(900)
await escuro.locator('button[aria-label^="Questão 14.1 #22"]').click()
await foto(escuro, 'listas')

await escuro.getByRole('button', { name: 'IA ›' }).click()
await foto(escuro, 'gaveta')
await escuro.keyboard.press('Escape')
await escuro.evaluate(() => (document.activeElement)?.blur())   // sem o contorno de foco nas próximas fotos
await escuro.mouse.move(700, 880)                              // nem o realce de hover

await escuro.goto(`${m}/u/3/topicos`)
await foto(escuro, 'topicos')

await escuro.goto(`${m}/assistente`)
await foto(escuro, 'assistente')

await escuro.goto(`${m}/importar`)
await foto(escuro, 'importar')

const claro = await pagina('claro')
await claro.goto(`${base}/#/`)
await claro.waitForTimeout(4000)   // a tela inicial abre com uma animação do nome
await foto(claro, 'inicio-claro')
await claro.goto(`${m}/u/1/listas`)
await claro.waitForTimeout(900)
await claro.locator('button[aria-label^="Questão 14.1 #30"]').click()
await foto(claro, 'listas-claro')

await navegador.close()
