// Quando instalar dependências e quando recompilar a interface (usado pelo build-se-preciso.mjs / abrir-novo.bat).
import { existsSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

const FONTES = ['src', 'public', 'index.html', 'package.json', 'package-lock.json', 'vite.config.ts', 'svelte.config.js']

function maisRecente(caminho) {
  const info = statSync(caminho)
  if (!info.isDirectory()) return info.mtimeMs
  return Math.max(0, ...readdirSync(caminho).map((nome) => maisRecente(join(caminho, nome))))
}

/** Sem build, ou com alguma fonte/configuração (inclusive tsconfig*.json) mais nova que o build. */
export function precisaCompilar(raiz) {
  const indice = join(raiz, 'dist', 'index.html')
  if (!existsSync(indice)) return true
  const tsconfigs = readdirSync(raiz).filter((n) => /^tsconfig.*\.json$/.test(n))
  const fontes = [...FONTES, ...tsconfigs].map((p) => join(raiz, p)).filter(existsSync)
  return Math.max(...fontes.map(maisRecente)) > statSync(indice).mtimeMs
}

/** Sem node_modules instalado, ou com o package-lock mais novo que a última instalação (dependência nova). */
export function precisaInstalar(raiz) {
  const registro = join(raiz, 'node_modules', '.package-lock.json')
  if (!existsSync(registro)) return true
  return statSync(join(raiz, 'package-lock.json')).mtimeMs > statSync(registro).mtimeMs
}
