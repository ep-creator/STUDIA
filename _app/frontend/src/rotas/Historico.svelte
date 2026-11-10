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

  // um título por dia (hoje, ontem, a data), na ordem em que vieram
  const porDia = $derived.by(() => {
    const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    const hoje = iso(new Date())
    const ontem = iso(new Date(Date.now() - 86_400_000))
    const mapa = new Map<string, GrupoHistorico[]>()
    for (const g of grupos) {
      const d = g.momento.slice(0, 10)
      const nome = d === hoje ? 'Hoje' : d === ontem ? 'Ontem' : `${d.slice(8, 10)}/${d.slice(5, 7)}/${d.slice(0, 4)}`
      mapa.set(nome, [...(mapa.get(nome) ?? []), g])
    }
    return [...mapa.entries()]
  })

  // O que o "desfazer" do motor atinge: a ação mais recente que ainda não foi desfeita nem é um desfazer
  const alvo = $derived(grupos.find((g) => !g.desfeito_em && g.desfaz_grupo === null)?.id ?? null)

  // marcar e remarcar a mesma questão em sequência vira uma linha só (a mais recente), com as anteriores a um clique;
  // a linha que o desfazer atinge nunca fica escondida
  const questaoMarcada = (g: GrupoHistorico) => g.descricao.match(/^Marcar questão (\S+ #\S+)/)?.[1] ?? null
  type Linha = { g: GrupoHistorico; antes: GrupoHistorico[] }
  function juntar(doDia: GrupoHistorico[]): Linha[] {
    const linhas: Linha[] = []
    for (const g of doDia) {
      const ultima = linhas.at(-1)
      const q = questaoMarcada(g)
      if (ultima && q && q === questaoMarcada(ultima.g) && g.id !== alvo) ultima.antes.push(g)
      else linhas.push({ g, antes: [] })
    }
    return linhas
  }
  let abertas = $state<number[]>([])
</script>

<header class="cab"><h1>Histórico</h1><span class="suave dica">Ctrl+Z desfaz a última</span></header>
{#if !lido}
  <p class="suave">Carregando…</p>
{:else if grupos.length === 0}
  <p class="suave">Nada por aqui ainda.</p>
{:else}
  {#each porDia as [dia, doDia] (dia)}
    <h2 class="rotulo dia">{dia}</h2>
    <ul>
      {#each juntar(doDia) as { g, antes } (g.id)}
        <ItemHistorico {uid} grupo={g} ultimo={g.id === alvo} ondesfazer={() => void desfazer()} />
        {#if antes.length}
          {#if abertas.includes(g.id)}
            {#each antes as a (a.id)}<ItemHistorico {uid} grupo={a} ultimo={false} ondesfazer={() => void desfazer()} />{/each}
          {:else}
            <li class="antes"><button class="acao-texto" onclick={() => (abertas = [...abertas, g.id])}>
              +{antes.length} {antes.length === 1 ? 'marcação anterior' : 'marcações anteriores'} da mesma questão
            </button></li>
          {/if}
        {/if}
      {/each}
    </ul>
  {/each}
{/if}

<style>
  .dia { margin: 1.2rem 0 0.3rem; font-family: var(--fonte-texto); font-weight: 400; }
  .cab { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; }
  h1 { font-size: 2.2rem; margin: 0 0 0.6rem; }
  .dica { font-size: 0.8rem; }
  ul { list-style: none; margin: 1rem 0 0; padding: 0; }
  .antes { padding: 0.15rem 0 0.4rem 4.2rem; font-size: 0.85rem; }
</style>
