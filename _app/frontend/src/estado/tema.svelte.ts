// Tema: só o Editorial, em claro, escuro ou seguindo o sistema. Preferência só deste navegador.

export type Modo = 'sistema' | 'claro' | 'escuro'

const CHAVE = 'estudos.tema'
const MODOS: Modo[] = ['sistema', 'claro', 'escuro']

function ler(): { modo: Modo } {
  try {
    // Preferências antigas guardavam também a identidade (Padrão ou Editorial): só o modo conta agora
    const salvo = JSON.parse(localStorage.getItem(CHAVE) ?? 'null')
    if (salvo && MODOS.includes(salvo.modo)) return { modo: salvo.modo }
  } catch {
    // armazenamento bloqueado ou valor estragado: fica o padrão
  }
  return { modo: 'sistema' }
}

export const tema = $state(ler())

function sistemaEscuro(): boolean {
  return typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: dark)').matches
}

export function temaEfetivo(): 'editorial-claro' | 'editorial-escuro' {
  const escuro = tema.modo === 'escuro' || (tema.modo === 'sistema' && sistemaEscuro())
  return escuro ? 'editorial-escuro' : 'editorial-claro'
}

export function aplicarTema(): void {
  document.documentElement.dataset.tema = temaEfetivo()
}

export function escolherModo(modo: Modo): void {
  tema.modo = modo
  try {
    localStorage.setItem(CHAVE, JSON.stringify({ modo }))
  } catch {
    // sem armazenamento: vale só até recarregar
  }
  aplicarTema()
}

/** Reaplica quando o Windows troca entre claro e escuro (só importa no modo "sistema"). */
export function acompanharSistema(): () => void {
  if (typeof matchMedia !== 'function') return () => {}
  const consulta = matchMedia('(prefers-color-scheme: dark)')
  const mudou = () => aplicarTema()
  consulta.addEventListener('change', mudou)
  return () => consulta.removeEventListener('change', mudou)
}
