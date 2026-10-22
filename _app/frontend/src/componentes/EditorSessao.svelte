<script lang="ts">
  import type { Sessao } from '../api/tipos'

  let { sessao, onsalvar, oncancelar }: {
    sessao: Partial<Sessao> | null
    onsalvar: (dados: { codigo: string; data: string | null; foco_md: string }) => void
    oncancelar: () => void
  } = $props()

  // svelte-ignore state_referenced_locally
  let codigo = $state(sessao?.codigo ?? '')
  // svelte-ignore state_referenced_locally
  let data = $state(sessao?.data ?? '')
  // svelte-ignore state_referenced_locally
  let foco = $state(sessao?.foco_md ?? '')
</script>

<form
  class="cartao editor"
  onsubmit={(e) => { e.preventDefault(); onsalvar({ codigo: codigo.trim(), data: data || null, foco_md: foco }) }}
>
  <label>Nome da sessão <input bind:value={codigo} required placeholder="Ex.: P1, Revisão 14.3" /></label>
  <label>Data <input type="date" bind:value={data} /></label>
  <label class="largo">Foco <textarea rows="2" bind:value={foco} placeholder="O que estudar (aceita Markdown e $fórmulas$)"></textarea></label>
  <div class="botoes">
    <button class="botao primario" type="submit" disabled={!codigo.trim()}>Salvar sessão</button>
    <button class="botao" type="button" onclick={oncancelar}>Cancelar</button>
  </div>
</form>

<style>
  .editor { display: grid; grid-template-columns: 1fr 12rem; gap: 0.75rem; margin: 1rem 0; }
  label { display: grid; gap: 0.25rem; font-size: 0.85rem; }
  .largo, .botoes { grid-column: 1 / -1; }
  .botoes { display: flex; gap: 0.5rem; }
  input, textarea { border: 1px solid var(--borda); border-radius: 6px; padding: 0.3rem 0.5rem; background: var(--fundo); }
</style>
