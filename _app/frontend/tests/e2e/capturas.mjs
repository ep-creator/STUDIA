// Auditoria visual: fotografa as telas de uma matéria nos temas pedidos.
// Uso: node tests/e2e/capturas.mjs <baseURL> <uid> <pasta-saida> [temas separados por vírgula]
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

const [base, uid, saida, temasArg] = process.argv.slice(2)
const temas = (temasArg ?? 'editorial-claro,editorial-escuro,padrao-claro,padrao-escuro').split(',')
const telas = ['u/1/painel', 'u/1/topicos', 'u/1/listas', 'u/1/cronograma', 'u/1/documentos', 'u/1/formulario', 'importar', 'historico']
mkdirSync(saida, { recursive: true })

const navegador = await chromium.launch()
for (const tema of temas) {
  const [identidade, modo] = tema.split('-')
  const pagina = await navegador.newPage({ viewport: { width: 1600, height: 950 } })
  await pagina.addInitScript(([i, m]) => localStorage.setItem('estudos.tema', JSON.stringify({ identidade: i, modo: m })), [identidade, modo])
  await pagina.goto(`${base}/#/`)
  await pagina.waitForTimeout(700)
  await pagina.screenshot({ path: join(saida, `${tema}-materias.png`) })
  for (const tela of telas) {
    await pagina.goto(`${base}/#/m/${uid}/${tela}`)
    await pagina.waitForTimeout(900)
    await pagina.screenshot({ path: join(saida, `${tema}-${tela.replaceAll('/', '_')}.png`), fullPage: false })
  }
  await pagina.close()
}
await navegador.close()
console.log('ok', temas.length * (telas.length + 1), 'capturas')
