<script lang="ts">
  import type { Snippet } from 'svelte'

  // Moldura fina com rótulos nas bordas; só aparece nos temas Editorial (nos demais é um contêiner neutro).
  let { topo, base, children }: { topo: string; base: string; children: Snippet } = $props()
</script>

<div class="moldura">
  <span class="etiqueta topo">{topo}</span>
  {@render children()}
  <span class="etiqueta base">{base}</span>
</div>

<style>
  .moldura { position: relative; }
  .etiqueta { display: none; }
  :global(:root[data-tema^='editorial']) .moldura { border: 1px solid var(--borda); padding: 2rem 1.75rem; margin: 0.75rem 0; }
  :global(:root[data-tema^='editorial']) .etiqueta {
    display: block; position: absolute; left: 50%; transform: translateX(-50%); background: var(--fundo);
    padding: 0 0.6rem; font-size: 0.65rem; letter-spacing: 0.2em; text-transform: uppercase; white-space: nowrap;
  }
  .topo { top: -0.55rem; }
  .base { bottom: -0.55rem; }
</style>
