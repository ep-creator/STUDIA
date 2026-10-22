// Compila o frontend só quando o código-fonte é mais novo que o build (usado pelo abrir-novo.bat).
import { execSync } from 'node:child_process'
import { existsSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const raiz = fileURLToPath(new URL('..', import.meta.url))
const indice = join(raiz, 'dist', 'index.html')

function maisRecente(caminho) {
  const info = statSync(caminho)
  if (!info.isDirectory()) return info.mtimeMs
  return Math.max(0, ...readdirSync(caminho).map((nome) => maisRecente(join(caminho, nome))))
}

const fontes = ['src', 'public', 'index.html', 'package-lock.json', 'vite.config.ts'].map((p) => join(raiz, p)).filter(existsSync)
const precisa = !existsSync(indice) || Math.max(...fontes.map(maisRecente)) > statSync(indice).mtimeMs

if (precisa) {
  console.log('Compilando a interface...')
  execSync('npm run build', { cwd: raiz, stdio: 'inherit' })
} else {
  console.log('Interface já compilada.')
}
