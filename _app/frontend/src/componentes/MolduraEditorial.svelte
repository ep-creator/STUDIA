<script lang="ts">
  import type { Snippet } from 'svelte'

  // Moldura fina com rótulos nas bordas; só aparece nos temas Editorial (nos demais é um contêiner neutro).
  // ajustada: ocupa a altura que sobrar na tela (para telas que rolam por dentro, como Documentos)
  let { topo, base, ajustada = false, children }: { topo: string; base: string; ajustada?: boolean; children: Snippet } = $props()
</script>

<div class="moldura" class:ajustada>
  <span class="etiqueta topo">{topo}</span>
  {@render children()}
  <span class="etiqueta base">{base}</span>
</div>

<style>
  .moldura { position: relative; }
  .etiqueta { display: none; }
  .ajustada { flex: 1; min-height: 0; display: flex; flex-direction: column; }
  @media print { .ajustada { display: block; } }
  .moldura { border: 1px solid var(--borda); padding: 2rem 1.75rem; margin: 0.75rem 0; }
  .etiqueta {
    display: block; position: absolute; left: 50%; transform: translateX(-50%); background: var(--fundo);
    padding: 0 0.6rem; font-size: 0.65rem; letter-spacing: 0.2em; text-transform: uppercase; white-space: nowrap;
  }
  .topo { top: -0.55rem; }
  .base { bottom: -0.55rem; }
</style>
