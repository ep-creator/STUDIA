<script lang="ts">
  import type { Topico } from '../api/tipos'

  // O que cai na prova: os tópicos da unidade com o status de cada um, e quantos já foram vistos
  let { topicos, hrefTopicos }: { topicos: Topico[]; hrefTopicos: string } = $props()

  const vistos = $derived(topicos.filter((t) => t.status === 'visto').length)
  const fracao = $derived(topicos.length ? vistos / topicos.length : 0)
  const MARCA: Record<string, string> = { visto: '✓', proxima: '→', pendente: '' }
</script>

<section class="topicos" aria-label="Tópicos vistos">
  <header>
    <div class="rotulo">Tópicos vistos</div>
    <a class="suave todos" href={hrefTopicos}>ver todos</a>
  </header>
  <div class="numero-grande">{vistos}/{topicos.length}</div>
  <div class="barra" aria-hidden="true"><div style:width={`${fracao * 100}%`}></div></div>
  {#if topicos.length}
    <ol>
      {#each topicos as t (t.id)}
        <li class={t.status}><span class="marca" aria-hidden="true">{MARCA[t.status] ?? ''}</span>{t.titulo}</li>
      {/each}
    </ol>
  {/if}
</section>

<style>
  header { display: flex; justify-content: space-between; align-items: baseline; }
  .todos { font-size: 0.8rem; }
  .barra { height: 6px; background: color-mix(in srgb, var(--borda) 25%, transparent); border-radius: 3px; margin: 0.5rem 0 0.75rem; }
  .barra div { height: 100%; background: var(--destaque); border-radius: 3px; transition: width 500ms ease; }
  ol { list-style: none; margin: 0; padding: 0; columns: 2 14rem; column-gap: 1.5rem; }
  li { display: flex; gap: 0.5rem; padding: 0.22rem 0; font-size: 0.92rem; break-inside: avoid; }
  .marca { width: 1rem; flex: none; text-align: center; color: var(--ok); }
  .visto { color: var(--suave); }
  .proxima { color: var(--destaque); font-weight: 600; }
  .proxima .marca { color: var(--destaque); }
  .pendente .marca::before { content: '·'; color: var(--suave); }
</style>
