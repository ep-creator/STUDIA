<script lang="ts">
  import type { Snippet } from 'svelte'
  import type { Painel } from '../api/tipos'
  import { ordinal, textoContagem } from '../apresentacao'
  import { montarHash, type Area } from '../rotas/rota'

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
  {#if unidade}<span class="suave contagem">Prova: {textoContagem(prova, hoje)}</span>{/if}
  <div class="acoes">{@render acoes?.()}</div>
</header>

<style>
  .topo { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 0; margin-bottom: 0.5rem; }
  .unidades { display: flex; gap: 0.4rem; }
  .unidades a { text-decoration: none; border: 1.5px solid var(--borda); border-radius: 999px; padding: 0.1rem 0.8rem; }
  .unidades a.ativa { background: var(--texto); color: var(--fundo); border-color: var(--texto); }
  .acoes { margin-left: auto; display: flex; gap: 0.5rem; }
</style>
