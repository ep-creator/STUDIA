<script lang="ts">
  import { requisitar } from '../api/cliente'
  import type { GrupoHistorico } from '../api/tipos'
  import ItemHistorico from '../componentes/ItemHistorico.svelte'
  import { erro } from '../estado/avisos.svelte'
  import { desfazer, quandoDesfizer } from '../estado/desfazer'

  let { uid }: { uid: string } = $props()

  let grupos = $state<GrupoHistorico[]>([])
  let lido = $state(false)

  async function carregar() {
    try {
      grupos = await requisitar<GrupoHistorico[]>('GET', `/api/materias/${uid}/historico?limite=100`)
      lido = true
    } catch (e) {
      erro(e)
    }
  }

  $effect(() => {
    void uid
    void carregar()
    return quandoDesfizer(() => void carregar())
  })

  // O que o "desfazer" do motor atinge: a ação mais recente que ainda não foi desfeita nem é um desfazer
  const alvo = $derived(grupos.find((g) => !g.desfeito_em && g.desfaz_grupo === null)?.id ?? null)
</script>

<header class="cab"><h1>Histórico</h1><span class="suave dica">Ctrl+Z desfaz a última</span></header>
{#if !lido}
  <p class="suave">Carregando…</p>
{:else if grupos.length === 0}
  <p class="suave">Nada por aqui ainda.</p>
{:else}
  <ul>
    {#each grupos as g (g.id)}<ItemHistorico {uid} grupo={g} ultimo={g.id === alvo} ondesfazer={() => void desfazer()} />{/each}
  </ul>
{/if}

<style>
  .cab { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; }
  h1 { font-size: 2.2rem; margin: 0 0 0.6rem; }
  .dica { font-size: 0.8rem; }
  ul { list-style: none; margin: 1rem 0 0; padding: 0; }
</style>
