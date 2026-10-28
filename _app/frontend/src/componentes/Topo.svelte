<script lang="ts">
  import type { Snippet } from 'svelte'
  import type { Painel } from '../api/tipos'
  import { ordinal, textoTopoProva } from '../apresentacao'
  import { montarHash, type Area } from '../rotas/rota'
  import { busca } from '../estado/busca.svelte'

  let { painel, area, hoje = new Date(), acoes }: { painel: Painel; area: Area; hoje?: Date; acoes?: Snippet } = $props()

  const unidade = $derived(painel.unidades.find((u) => u.numero === painel.unidade) ?? null)
  const prova = $derived.by(() => {
    if (!unidade) return null
    const e = painel.eventos.find((ev) => ev.tipo === 'prova' && ev.unidade_id === unidade.id)
    return e ? { data: e.data, hora_inicio: e.hora_inicio } : unidade.data_prova ? { data: unidade.data_prova, hora_inicio: null } : null
  })
</script>

<header class="topo nao-imprimir">
  <nav class="unidades" aria-label="Unidades">
    {#each painel.unidades as u (u.id)}
      <a
        href={montarHash({ tela: 'materia', uid: painel.materia.uid, unidade: u.numero, area })}
        class:ativa={u.numero === painel.unidade}
        aria-current={u.numero === painel.unidade ? 'true' : undefined}
      >{ordinal(u.numero)}</a>
    {/each}
  </nav>
  {#if unidade}<span class="suave contagem">{textoTopoProva(prova, hoje)}</span>{/if}
  <button class="buscar" onclick={() => (busca.aberta = true)} aria-label="Buscar na matéria (Ctrl K)">
    <span>Buscar na matéria…</span><kbd>Ctrl K</kbd>
  </button>
  <div class="acoes">{@render acoes?.()}</div>
</header>

<style>
  .topo { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 0; margin-bottom: 0.5rem; }
  .unidades { display: flex; gap: 1.1rem; font-family: var(--fonte-titulo); font-size: 1.05rem; }
  .unidades a { text-decoration: none; color: var(--suave); padding-bottom: 2px; border-bottom: 1.5px solid transparent; }
  .unidades a:hover { color: var(--texto); }
  .unidades a.ativa { color: var(--texto); border-bottom-color: var(--destaque); }
  .acoes { display: flex; gap: 1.1rem; font-size: 0.9rem; }
  .buscar {
    margin-left: auto; display: flex; align-items: center; gap: 1.5rem; min-width: 15rem; justify-content: space-between;
    background: var(--leve); color: var(--suave); border: 0;
    border-radius: 999px; padding: 0.3rem 0.5rem 0.3rem 0.9rem; cursor: pointer;
  }
  .buscar:hover { color: var(--texto); }
  kbd { font-family: var(--fonte-texto); font-size: 0.72rem; opacity: 0.7; }
</style>
