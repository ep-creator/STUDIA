<script lang="ts">
  import type { Formula } from '../api/tipos'
  import { renderizarFormula } from '../markdown'
  import Markdown from './Markdown.svelte'
  import MenuMais from './MenuMais.svelte'

  let { formula, oneditar, onapagar }: { formula: Formula; oneditar: () => void; onapagar: () => void } = $props()
  const html = $derived(renderizarFormula(formula.corpo_tex))
</script>

<article class="formula linha-acoes">
  <header>
    <div class="rotulo">{formula.titulo}</div>
    <span class="acoes-linha nao-imprimir">
      <button class="acao-texto" aria-label={`Editar ${formula.titulo}`} onclick={oneditar}>editar</button>
      <MenuMais rotulo={`Mais ações de ${formula.titulo}`} itens={[{ rotulo: 'Apagar', acao: onapagar, perigo: true }]} />
    </span>
  </header>
  <div class="tex">{@html html}</div>
  {#if formula.notas_md}<div class="suave"><Markdown texto={formula.notas_md} /></div>{/if}
</article>

<style>
  .formula { padding: 0.7rem 0; border-bottom: 1px solid var(--fio); break-inside: avoid; }
  header { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; }
  .acoes-linha { display: flex; gap: 0.9rem; align-items: baseline; font-size: 0.85rem; }
  .tex { overflow-x: auto; }
</style>
