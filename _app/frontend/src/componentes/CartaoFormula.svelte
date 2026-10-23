<script lang="ts">
  import type { Formula } from '../api/tipos'
  import { renderizarFormula } from '../markdown'
  import Markdown from './Markdown.svelte'

  let { formula, oneditar, onapagar }: { formula: Formula; oneditar: () => void; onapagar: () => void } = $props()
  const html = $derived(renderizarFormula(formula.corpo_tex))
</script>

<article class="formula">
  <div class="rotulo">{formula.titulo}</div>
  <div class="tex">{@html html}</div>
  {#if formula.notas_md}<div class="suave"><Markdown texto={formula.notas_md} /></div>{/if}
  <span class="acoes nao-imprimir">
    <button aria-label={`Editar ${formula.titulo}`} onclick={oneditar}>✎</button>
    <button aria-label={`Apagar ${formula.titulo}`} onclick={onapagar}>🗑</button>
  </span>
</article>

<style>
  .formula { position: relative; padding: 0.6rem 0; border-top: 1px solid color-mix(in srgb, var(--borda) 30%, transparent); break-inside: avoid; }
  .tex { overflow-x: auto; }
  .acoes { position: absolute; top: 0.4rem; right: 0; opacity: 0.35; }
  .formula:hover .acoes { opacity: 1; }
  .acoes button { background: none; border: 0; cursor: pointer; }
</style>
