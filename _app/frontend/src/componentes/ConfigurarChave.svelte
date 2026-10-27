<script lang="ts">
  // Chave do Gemini: vai para _app/.segredos.toml (fora do Git); a tela nunca a recebe de volta.
  import { requisitar } from '../api/cliente'
  import { avisar, erro } from '../estado/avisos.svelte'

  let { onsalvo }: { onsalvo: () => void } = $props()
  let chave = $state('')

  async function salvar(e: SubmitEvent) {
    e.preventDefault()
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

<form class="chave" onsubmit={salvar}>
  <p>
    Para o assistente responder aqui, cole a sua chave da API do Gemini (crie uma de graça no Google AI Studio). Enquanto
    isso, "Copiar o contexto" monta o pedido com os materiais da matéria para colar em qualquer chat.
  </p>
  <label>
    Chave do Gemini
    <input type="password" autocomplete="off" bind:value={chave} placeholder="AIza…" />
  </label>
  <button class="botao primario" type="submit" disabled={!chave.trim()}>Salvar a chave</button>
</form>

<style>
  .chave { display: grid; gap: 0.45rem; padding: 0.6rem; border: 1px dashed var(--borda); border-radius: var(--raio); font-size: 0.88rem; }
  .chave p { margin: 0; }
  label { display: grid; gap: 0.2rem; }
  input { border: 1px solid var(--borda); border-radius: 6px; padding: 0.3rem 0.45rem; background: var(--fundo); color: var(--texto); }
</style>
