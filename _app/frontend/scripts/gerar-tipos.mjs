// Gera src/api/tipos.gerados.ts a partir do OpenAPI do motor.
// Uso: npm run tipos               (motor rodando em http://127.0.0.1:8790)
//      npm run tipos -- <url|arquivo.json>
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const fonte = process.argv[2] ?? 'http://127.0.0.1:8790/openapi.json'
const destino = fileURLToPath(new URL('../src/api/tipos.gerados.ts', import.meta.url))
const aspas = (s) => `"${s.replaceAll('"', '\\"')}"`  // caminhos com espaço (a pasta do projeto tem)
// Versão fixa e fora das devDependencies: o openapi-typescript ainda declara peer typescript ^5.
execSync(`npx -y openapi-typescript@7.13.0 ${aspas(fonte)} -o ${aspas(destino)}`, { stdio: 'inherit' })
