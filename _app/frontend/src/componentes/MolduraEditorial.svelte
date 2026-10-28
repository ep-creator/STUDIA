<script lang="ts">
  import type { Snippet } from 'svelte'

  // Cabeçalho da matéria: os dois rótulos (matéria e unidade) numa linha com um fio embaixo, sem caixa em volta.
  // ajustada: ocupa a altura que sobrar na tela (para telas que rolam por dentro, como Documentos)
  let { topo, base, ajustada = false, children }: { topo: string; base: string; ajustada?: boolean; children: Snippet } = $props()
</script>

<div class="moldura" class:ajustada>
  <div class="cabecalho-materia"><span class="rotulo">{topo}</span><span class="rotulo">{base}</span></div>
  {@render children()}
</div>

<style>
  .moldura { display: flex; flex-direction: column; gap: 1.2rem; }
  .ajustada { flex: 1; min-height: 0; }
  @media print { .ajustada { display: block; } }
  .cabecalho-materia { display: flex; justify-content: space-between; gap: 1rem; padding-bottom: 0.6rem; border-bottom: 1px solid var(--fio); }
  /* o primeiro bloco logo abaixo não ganha um segundo fio */
  .cabecalho-materia + :global(*) { border-top: 0 !important; }
</style>
