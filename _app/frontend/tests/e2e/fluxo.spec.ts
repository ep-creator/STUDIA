// Fluxos principais contra o motor real (PDFs reais de Cálculo 2). Rodam em série sobre a mesma matéria.
import { expect, test, type Page } from '@playwright/test'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

// PDFs reais do Cálculo 2: documentos da turma (com as listas 1 e 2) e a pasta das listas 3 a 6
const FONTES = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..', 'Calculo 2', 'fontes')
const PROGRAMA = join(FONTES, 'documentos', 'Programa.pdf')
const CALENDARIO = join(FONTES, 'documentos', 'Calendario.pdf')
const LISTA1 = join(FONTES, 'documentos', 'Lista1_2026-1.pdf')
const LISTA3 = join(FONTES, 'listas', 'Lista3_2026-1.pdf')

test.describe.configure({ mode: 'serial' })
test.skip(!existsSync(PROGRAMA), 'PDFs reais de Cálculo 2 ausentes')

let inicioMateria = ''

async function abrirArea(page: Page, unidade: string, area: string) {
  await page.goto(inicioMateria)
  await page.getByRole('navigation', { name: 'Unidades' }).getByRole('link', { name: unidade, exact: true }).click()
  await page.getByRole('navigation', { name: 'Áreas da matéria' }).getByRole('link', { name: area, exact: true }).click()
}

test('matéria nova só com cliques', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '＋ Nova matéria' }).click()
  await page.getByLabel('Nome').fill('Cálculo E2E')
  await page.getByRole('button', { name: 'Criar', exact: true }).click()
  await expect(page).toHaveURL(/#\/m\/[^/]+\/importar$/)
  inicioMateria = page.url().replace(/\/importar$/, '')

  await page.setInputFiles('input[type=file]', [PROGRAMA, CALENDARIO, LISTA1, LISTA3])
  const fila = page.getByRole('list', { name: 'Arquivos esperando revisão' })
  await expect(fila.getByRole('listitem')).toHaveCount(4, { timeout: 60_000 })

  // Revisão: a L1 vai para a 1ª unidade (escolha do usuário)
  await fila.getByText('Lista1_2026-1.pdf').click()
  await page.getByRole('button', { name: /^Unidade da lista L1/ }).click()
  await page.getByRole('option', { name: '1ª unidade' }).click()

  // Primeiro o que não tem pendência (o programa); com os tópicos no banco, o motor recalcula a unidade da L3
  await page.getByRole('button', { name: /Confirmar todos sem pendências/ }).click()
  await expect(page.getByRole('status').getByText(/confirmado/)).toBeVisible()
  await expect(fila.getByRole('listitem')).toHaveCount(3)

  // Depois o resto, um por um
  for (let restantes = await fila.getByRole('listitem').count(); restantes > 0; restantes--) {
    await fila.getByRole('button').first().click()
    await page.getByRole('button', { name: 'Confirmar', exact: true }).click()
    await expect(fila.getByRole('listitem')).toHaveCount(restantes - 1)   // espera a fila andar
  }
  await expect(page.getByText('Nenhum arquivo esperando revisão.')).toBeVisible()

  await page.getByRole('link', { name: 'Painel', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Prova' }).getByText(/^\d+ dias$|^hoje$|^amanhã$/)).toBeVisible()
  await expect(page.getByText('Tópicos vistos')).toBeVisible()
})

test('marcar e desfazer', async ({ page }) => {
  await abrirArea(page, '1ª', 'Listas')
  const q1 = page.getByRole('button', { name: /^Questão L1 #1( |$)/ })
  await q1.click()   // clicar só abre a questão no menu ao lado
  await expect(page.getByRole('button', { name: 'Questão L1 #1', exact: true })).toBeVisible()
  await page.getByRole('group', { name: 'Marcar questão' }).getByRole('button', { name: /Errei/ }).click()
  await expect(page.getByRole('button', { name: 'Questão L1 #1 (✗)' })).toBeVisible()
  await page.getByRole('button', { name: 'Questão L1 #1 (✗)' }).focus()
  await page.keyboard.press('ArrowRight')
  await page.keyboard.press('3')
  await expect(page.getByRole('button', { name: 'Questão L1 #2 (?)' })).toBeVisible()
  await expect(page.getByText('2/8', { exact: true })).toBeVisible()

  await page.keyboard.press('Control+z')
  await expect(page.getByRole('status').getByText(/^Desfeito: Marcar questão L1 #2/)).toBeVisible()
  await expect(page.getByText('1/8', { exact: true })).toBeVisible()
})

test('editar resumo e ver a diferença', async ({ page }) => {
  await abrirArea(page, '1ª', 'Documentos')
  await page.getByRole('button', { name: '＋ Novo documento' }).click()
  await page.getByLabel('Título do documento').fill('Resumo E2E')
  await page.getByRole('button', { name: 'Criar', exact: true }).click()
  await page.getByRole('textbox', { name: 'Texto do documento' }).fill('Primeira linha com $x^2$')
  await page.getByRole('button', { name: 'Salvar', exact: true }).click()
  await expect(page.getByRole('status').getByText('Documento salvo')).toBeVisible()
  await expect(page.locator('.leitor .katex')).toHaveCount(1)

  await page.getByRole('link', { name: 'Histórico', exact: true }).click()
  await page.getByRole('button', { name: 'Detalhes' }).first().click()
  await expect(page.getByText('+ Primeira linha com $x^2$')).toBeVisible()
})

test('busca com Ctrl K abre o texto e o PDF', async ({ page }) => {
  await abrirArea(page, '1ª', 'Painel')
  await page.keyboard.press('Control+k')
  const campo = page.getByRole('combobox', { name: 'Buscar na matéria' })
  await campo.fill('primeira linha')
  await page.getByRole('option', { name: /Resumo E2E/ }).first().click()
  await expect(page.locator('.leitor h2', { hasText: 'Resumo E2E' })).toBeVisible()

  await page.getByRole('button', { name: /Buscar na matéria/ }).click()
  await campo.fill('lista')
  await page.getByRole('radio', { name: 'Toda a matéria' }).click()
  await page.getByRole('radio', { name: 'Listas e provas' }).click()
  await page.getByRole('option').first().click()
  await expect(page.locator('.leitor iframe')).toBeVisible()
})

test('quatro temas persistem', async ({ page }) => {
  await page.goto(inicioMateria)
  for (const [identidade, modo, esperado] of [
    ['Padrão', 'Claro', 'padrao-claro'], ['Padrão', 'Escuro', 'padrao-escuro'],
    ['Editorial', 'Claro', 'editorial-claro'], ['Editorial', 'Escuro', 'editorial-escuro'],
  ]) {
    await page.getByRole('button', { name: /^Identidade visual/ }).click()
    await page.getByRole('option', { name: identidade }).click()
    await page.getByRole('button', { name: /^Claro ou escuro/ }).click()
    await page.getByRole('option', { name: modo, exact: true }).click()
    await page.reload()
    await expect(page.locator('html')).toHaveAttribute('data-tema', esperado)
  }
})

test('criar outra matéria depois de abrir uma não trava em "Carregando"', async ({ page }) => {
  await abrirArea(page, '1ª', 'Listas')
  await page.getByRole('link', { name: 'STUDIA' }).click()
  await page.getByRole('button', { name: '＋ Nova matéria' }).click()
  await page.getByLabel('Nome').fill('Segunda matéria')
  await page.getByRole('button', { name: 'Criar', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Importar arquivos' })).toBeVisible()
  await expect(page.getByText('Carregando…')).toHaveCount(0)
})
