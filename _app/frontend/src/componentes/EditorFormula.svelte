<script lang="ts">
  import type { Formula } from '../api/tipos'
  import { renderizarLatex } from '../markdown'

  let { formula, onsalvar, oncancelar }: {
    formula: Partial<Formula> | null
    onsalvar: (dados: { titulo: string; corpo_tex: string; notas_md: string }) => void
    oncancelar: () => void
  } = $props()

  // svelte-ignore state_referenced_locally
  let titulo = $state(formula?.titulo ?? '')
  // svelte-ignore state_referenced_locally
  let corpo = $state(formula?.corpo_tex ?? '')
  // svelte-ignore state_referenced_locally
  let notas = $state(formula?.notas_md ?? '')
  const previa = $derived(corpo.trim() ? renderizarLatex(corpo, true) : '')
</script>

<form class="cartao editor" onsubmit={(e) => { e.preventDefault(); onsalvar({ titulo: titulo.trim(), corpo_tex: corpo, notas_md: notas }) }}>
  <label>Nome <input bind:value={titulo} required placeholder="Ex.: Regra da cadeia" /></label>
  <label>Fórmula (LaTeX) <textarea rows="3" bind:value={corpo} required placeholder={'\\frac{dz}{dt} = \\frac{\\partial z}{\\partial x}\\frac{dx}{dt}'}></textarea></label>
  <div class="previa" aria-label="Prévia da fórmula">{@html previa}</div>
  <label>Notas <textarea rows="2" bind:value={notas}></textarea></label>
  <div class="botoes">
    <button class="botao primario" type="submit" disabled={!titulo.trim() || !corpo.trim()}>Salvar fórmula</button>
    <button class="botao" type="button" onclick={oncancelar}>Cancelar</button>
  </div>
</form>

<style>
  .editor { display: grid; gap: 0.6rem; margin: 1rem 0; }
  label { display: grid; gap: 0.25rem; font-size: 0.85rem; }
  input, textarea { border: 1px solid var(--borda); border-radius: 6px; padding: 0.3rem 0.5rem; background: var(--fundo); font-family: ui-monospace, monospace; }
  input { font-family: inherit; }
  .previa { min-height: 2.5rem; overflow-x: auto; }
  .botoes { display: flex; gap: 0.5rem; }
</style>
