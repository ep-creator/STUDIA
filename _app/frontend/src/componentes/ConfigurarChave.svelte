<script lang="ts">
  // Chave do Gemini: vai para _app/.segredos.toml (fora do Git); a tela nunca a recebe de volta. Enter salva.
  import { requisitar } from '../api/cliente'
  import { avisar, erro } from '../estado/avisos.svelte'

  let { onsalvo }: { onsalvo: () => void } = $props()
  let chave = $state('')

  async function salvar(e: SubmitEvent) {
    e.preventDefault()
    if (!chave.trim()) return
    try {
      await requisitar('PUT', '/api/agente/chave', { chave: chave.trim() })
      chave = ''
      avisar('Chave do Gemini salva')
      onsalvo()
    } catch (err) {
      erro(err)
    }
  }
</script>

<form onsubmit={salvar}>
  <input type="password" autocomplete="off" aria-label="API key do Gemini" placeholder="API key" bind:value={chave} />
</form>

<style>
  input { width: 100%; box-sizing: border-box; border: 1px solid var(--borda); border-radius: 6px; padding: 0.35rem 0.5rem; background: var(--fundo); color: var(--texto); font: inherit; font-size: 0.88rem; }
</style>
