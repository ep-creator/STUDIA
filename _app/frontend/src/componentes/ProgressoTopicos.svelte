<script lang="ts">
  import type { Topico } from '../api/tipos'

  let { topicos, hrefTopicos }: { topicos: Topico[]; hrefTopicos: string } = $props()

  const vistos = $derived(topicos.filter((t) => t.status === 'visto').length)
  const proximo = $derived(topicos.find((t) => t.status === 'proxima') ?? topicos.find((t) => t.status === 'pendente'))
  const fracao = $derived(topicos.length ? vistos / topicos.length : 0)
</script>

<section class="cartao">
  <div class="rotulo">Tópicos vistos</div>
  <div class="numero-grande">{vistos}/{topicos.length}</div>
  <div class="barra" aria-hidden="true"><div style:width={`${fracao * 100}%`}></div></div>
  {#if proximo}
    <div class="suave">Próximo: <a href={hrefTopicos}>{proximo.titulo}</a></div>
  {/if}
</section>

<style>
  .barra { height: 6px; background: color-mix(in srgb, var(--borda) 18%, transparent); border-radius: 3px; margin: 0.5rem 0; }
  .barra div { height: 100%; background: var(--destaque); border-radius: 3px; }
</style>
