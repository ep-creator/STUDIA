// Tema: identidade (Padrão ou Editorial) × modo (sistema, claro, escuro). Preferência só deste navegador.

export type Identidade = 'padrao' | 'editorial'
export type Modo = 'sistema' | 'claro' | 'escuro'

const CHAVE = 'estudos.tema'

function ler(): { identidade: Identidade; modo: Modo } {
  try {
    const salvo = JSON.parse(localStorage.getItem(CHAVE) ?? 'null')
    if (salvo && ['padrao', 'editorial'].includes(salvo.identidade) && ['sistema', 'claro', 'escuro'].includes(salvo.modo)) {
      return salvo
    }
  } catch {
    // armazenamento bloqueado ou valor estragado: fica o padrão
  }
  return { identidade: 'editorial', modo: 'sistema' }
}

export const tema = $state(ler())

function sistemaEscuro(): boolean {
  return typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: dark)').matches
}

export function temaEfetivo(): string {
  const escuro = tema.modo === 'escuro' || (tema.modo === 'sistema' && sistemaEscuro())
  return `${tema.identidade}-${escuro ? 'escuro' : 'claro'}`
}

export function aplicarTema(): void {
  document.documentElement.dataset.tema = temaEfetivo()
}

export function escolherTema(identidade: Identidade, modo: Modo): void {
  tema.identidade = identidade
  tema.modo = modo
  try {
    localStorage.setItem(CHAVE, JSON.stringify({ identidade, modo }))
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
