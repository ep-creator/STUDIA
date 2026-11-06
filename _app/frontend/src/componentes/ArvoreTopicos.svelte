<script lang="ts">
  // Mapa dos tópicos da unidade: o título abre a página do tópico; o estado e o placar vêm derivados do motor.
  // Reordenar, renomear e o "visto" à mão (raro: o estado já se deriva sozinho) ficam nas ações da linha.
  import { requisitar } from '../api/cliente'
  import type { Topico, TopicoProgresso } from '../api/tipos'
  import { CLASSE_ESTADO_TOPICO, DEFINICAO_ESTADO } from '../apresentacao'
  import { erro } from '../estado/avisos.svelte'
  import { montarHash } from '../rotas/rota'
  import MenuMais from './MenuMais.svelte'

  let { uid, unidade, unidadeId, topicos, onmudou }: {
    uid: string
    unidade: number
    unidadeId: number
    topicos: Topico[]
    onmudou: () => void
  } = $props()

  const base = $derived(`/api/materias/${uid}/topicos`)
  let progresso = $state<Record<number, TopicoProgresso>>({})

  // o painel (topicos) é relido depois de cada escrita: o progresso acompanha
  $effect(() => {
    void topicos
    requisitar<TopicoProgresso[]>('GET', `/api/materias/${encodeURIComponent(uid)}/progresso?unidade=${unidade}`).then(
      (lista) => (progresso = Object.fromEntries(lista.map((t) => [t.id, t]))),
      () => (progresso = {}),
    )
  })

  let editando = $state<number | null>(null)
  let tituloEditado = $state('')
  let novo = $state('')
  let criando = $state(false)   // o campo de novo tópico só aparece quando se pede (a tela é para ler o mapa)

  const filhos = (pai: number | null) => topicos.filter((t) => t.pai_id === pai).sort((a, b) => a.ordem - b.ordem)

  async function executar(acao: () => Promise<unknown>) {
    try {
      await acao()
      onmudou()
    } catch (e) {
      erro(e)
    }
  }

  const alternarVisto = (t: Topico) => executar(() => requisitar('PATCH', `${base}/${t.id}`, { status: t.status === 'visto' ? 'pendente' : 'visto' }))
  const renomear = (t: Topico) => executar(async () => {
    if (tituloEditado.trim() && tituloEditado !== t.titulo) await requisitar('PATCH', `${base}/${t.id}`, { titulo: tituloEditado.trim() })
    editando = null
  })
  const apagar = (t: Topico) => {
    if (confirm(`Apagar o tópico "${t.titulo}"? (dá para desfazer)`)) void executar(() => requisitar('DELETE', `${base}/${t.id}`))
  }
  // Reordenar troca a ordem com o vizinho (mesmo pai)
  const mover = (t: Topico, delta: -1 | 1) => {
    const irmaos = filhos(t.pai_id)
    const vizinho = irmaos[irmaos.findIndex((x) => x.id === t.id) + delta]
    if (!vizinho) return
    void executar(async () => {
      await requisitar('PATCH', `${base}/${t.id}`, { ordem: vizinho.ordem })
      await requisitar('PATCH', `${base}/${vizinho.id}`, { ordem: t.ordem })
    })
  }
  const criar = (e: SubmitEvent) => {
    e.preventDefault()
    if (!novo.trim()) return
    void executar(async () => {
      await requisitar('POST', base, { unidade_id: unidadeId, titulo: novo.trim() })
      novo = ''
    })
  }
</script>

{#snippet item(t: Topico)}
  {@const p = progresso[t.id]}
  <li>
    <div class="linha linha-acoes">
      {#if editando === t.id}
        <form onsubmit={(e) => { e.preventDefault(); void renomear(t) }}>
          <input aria-label="Novo título" bind:value={tituloEditado} />
          <button class="acao-texto" type="submit">Salvar</button>
        </form>
      {:else}
        <a class="titulo" href={montarHash({ tela: 'materia', uid, unidade, area: 'topicos', topico: t.id })}>{t.titulo}</a>
      {/if}
      {#if p?.secoes.length}<span class="suave secoes">{p.secoes.join(' · ')}</span>{/if}
      <span class="acoes-linha">
        <button class="acao-texto" aria-label={`Subir ${t.titulo}`} onclick={() => mover(t, -1)}>↑</button>
        <button class="acao-texto" aria-label={`Descer ${t.titulo}`} onclick={() => mover(t, 1)}>↓</button>
        <button class="acao-texto" aria-label={`Renomear ${t.titulo}`} onclick={() => { editando = t.id; tituloEditado = t.titulo }}>editar</button>
        <MenuMais rotulo={`Mais ações de ${t.titulo}`} itens={[
          { rotulo: t.status === 'visto' ? 'Tirar o visto à mão' : 'Marcar como visto', acao: () => void alternarVisto(t) },
          { rotulo: 'Apagar', acao: () => apagar(t), perigo: true },
        ]} />
      </span>
      {#if p}
        <span class="estado {CLASSE_ESTADO_TOPICO[p.estado] ?? ''}" title={DEFINICAO_ESTADO[p.estado]}>{p.estado}</span>
        {#if p.err + p.dub}<span class="revisar">{p.err + p.dub} para revisar</span>{/if}
        <span class="placar suave" title="questões trabalhadas / questões ligadas ao tópico">{p.total ? `${p.trabalhadas}/${p.total}` : ''}</span>
      {/if}
    </div>
    {#if filhos(t.id).length}
      <ul>{#each filhos(t.id) as f (f.id)}{@render item(f)}{/each}</ul>
    {/if}
  </li>
{/snippet}

<ul class="arvore">{#each filhos(null) as t (t.id)}{@render item(t)}{/each}</ul>

{#if criando}
  <form class="novo" onsubmit={criar}>
    <!-- svelte-ignore a11y_autofocus -->
    <input aria-label="Novo tópico" placeholder="Título do tópico (Enter adiciona, Esc cancela)" bind:value={novo} autofocus
      onkeydown={(e) => { if (e.key === 'Escape') { novo = ''; criando = false } }} onblur={() => { if (!novo.trim()) criando = false }} />
  </form>
{:else}
  <button class="acao-texto novo" onclick={() => (criando = true)}>+ tópico</button>
{/if}

<style>
  ul { list-style: none; margin: 0; padding: 0; }
  ul ul { padding-left: 1.5rem; }
  .linha { display: flex; align-items: baseline; gap: 0.9rem; padding: 0.65rem 0.4rem; border-bottom: 1px solid var(--fio); transition: background-color var(--transicao); }
  .linha:hover { background: linear-gradient(90deg, var(--leve), transparent 80%); }
  .titulo { font-family: var(--fonte-titulo); font-size: 1.1rem; text-decoration: none; }
  .titulo:hover { text-decoration: underline; text-decoration-color: var(--destaque); text-underline-offset: 3px; }
  .secoes { font-size: 0.85rem; font-variant-numeric: tabular-nums; }
  .acoes-linha { margin-left: auto; display: flex; gap: 0.9rem; align-items: baseline; font-size: 0.85rem; }
  .estado { font-size: 0.85rem; color: var(--suave); min-width: 4.5rem; text-align: right; }
  .estado.hoje { color: var(--destaque-texto); font-weight: 500; }
  .estado.emdia { color: var(--ok); }
  .estado.falta { color: var(--texto); font-weight: 500; }
  .estado.comecado { color: var(--texto); }
  .revisar { font-size: 0.85rem; color: var(--err); white-space: nowrap; }
  .placar { font-size: 0.85rem; min-width: 3.2rem; text-align: right; font-variant-numeric: tabular-nums; }
  form { display: flex; gap: 0.5rem; }
  input { border: 0; border-bottom: 1px solid var(--fio); padding: 0.25rem 0; background: transparent; color: var(--texto); font: inherit; }
  .novo { margin-top: 0.8rem; }
  .novo input { flex: 0 1 20rem; }
</style>
