// Instala as dependências e compila a interface só quando precisa (usado pelo abrir-novo.bat).
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { precisaCompilar, precisaInstalar } from './compilacao.mjs'

const raiz = fileURLToPath(new URL('..', import.meta.url))

if (precisaInstalar(raiz)) {
  console.log('Instalando as dependências da interface...')
  execSync('npm ci --no-audit --no-fund', { cwd: raiz, stdio: 'inherit' })
}
if (precisaCompilar(raiz)) {
  console.log('Compilando a interface...')
  execSync('npm run build', { cwd: raiz, stdio: 'inherit' })
} else {
  console.log('Interface já compilada.')
}
