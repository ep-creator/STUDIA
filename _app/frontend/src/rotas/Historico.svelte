<script lang="ts">
  import { requisitar } from '../api/cliente'
  import type { GrupoHistorico } from '../api/tipos'
  import ItemHistorico from '../componentes/ItemHistorico.svelte'
  import { erro } from '../estado/avisos.svelte'
  import { desfazer, quandoDesfizer } from '../estado/desfazer'

  let { uid }: { uid: string } = $props()

  let grupos = $state<GrupoHistorico[]>([])

  async function carregar() {
    try {
      grupos = await requisitar<GrupoHistorico[]>('GET', `/api/materias/${uid}/historico?limite=100`)
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

<h2>Histórico</h2>
<p class="suave">Tudo o que mudou nesta matéria, da ação mais recente para a mais antiga. Ctrl+Z desfaz a última em qualquer tela.</p>
{#if grupos.length === 0}
  <p class="suave">Nada por aqui ainda.</p>
{:else}
  <ul>
    {#each grupos as g (g.id)}<ItemHistorico {uid} grupo={g} ultimo={g.id === alvo} ondesfazer={() => void desfazer()} />{/each}
  </ul>
{/if}

<style>
  ul { list-style: none; margin: 1rem 0 0; padding: 0; }
</style>
