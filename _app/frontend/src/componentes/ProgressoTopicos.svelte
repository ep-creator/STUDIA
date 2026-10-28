<script lang="ts">
  import type { Topico } from '../api/tipos'

  // O que cai na prova: os tópicos da unidade com o status de cada um, e quantos já foram vistos
  let { topicos, hrefTopicos }: { topicos: Topico[]; hrefTopicos: string } = $props()

  const vistos = $derived(topicos.filter((t) => t.status === 'visto').length)
  const fracao = $derived(topicos.length ? vistos / topicos.length : 0)
  const MARCA: Record<string, string> = { visto: '✓', proxima: '→', pendente: '○' }
</script>

<section class="topicos" aria-label="Tópicos vistos">
  <header>
    <div class="rotulo">Tópicos vistos</div>
    <a class="acao-texto todos" href={hrefTopicos}>ver todos</a>
  </header>
  <div class="numero-grande">{vistos}<small>/{topicos.length}</small></div>
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
  .numero-grande { margin-top: 0.4rem; }
  .numero-grande small { font-size: 1.1rem; color: var(--suave); }
  /* fio de progresso: 1 px de fundo, 2 px de verde para os vistos */
  .barra { height: 1px; background: var(--fio); margin: 0.6rem 0 0.9rem; }
  .barra div { height: 2px; margin-top: -0.5px; background: var(--ok); transition: width 500ms ease; }
  ol { list-style: none; margin: 0; padding: 0; columns: 2 14rem; column-gap: 1.6rem; }
  li { display: flex; gap: 0.5rem; padding: 0.2rem 0; font-size: 0.92rem; break-inside: avoid; }
  .marca { width: 1rem; flex: none; text-align: center; font-size: 0.8rem; }
  .visto .marca { color: var(--ok); }
  .proxima .marca { color: var(--destaque); }
  .pendente .marca { color: var(--suave); }
</style>
