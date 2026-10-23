import { defineConfig } from '@playwright/test'
import { existsSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

// Motor real num workspace vazio e temporário, porta própria para não colidir com o motor do dia a dia (8790).
const PORTA = 8792
const workspace = mkdtempSync(join(tmpdir(), 'estudos-e2e-'))
const venv = join('..', 'backend', '.venv', 'Scripts', 'python.exe')
const python = process.env.PYTHON ?? (existsSync(venv) ? venv : 'python')

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [['list']],
  use: { baseURL: `http://127.0.0.1:${PORTA}`, trace: 'retain-on-failure', viewport: { width: 1366, height: 860 } },
  webServer: {
    command: `"${python}" tests/e2e/servidor_e2e.py "${workspace}" ${PORTA}`,
    url: `http://127.0.0.1:${PORTA}/api/materias`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
})
