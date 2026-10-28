<script lang="ts">
  import { requisitar, urlArquivo } from '../api/cliente'
  import type { SecaoVinculada, Topico } from '../api/tipos'
  import { erro } from '../estado/avisos.svelte'
  import MenuMais from './MenuMais.svelte'
  import SeloStatus from './SeloStatus.svelte'

  let { uid, unidadeId, topicos, vinculos, listasDoTopico, onmudou }: {
    uid: string
    unidadeId: number
    topicos: Topico[]
    vinculos: Record<string, SecaoVinculada[]>
    listasDoTopico: Record<string, string[]>
    onmudou: () => void
  } = $props()

  const PROXIMO: Record<string, string> = { pendente: 'proxima', proxima: 'visto', visto: 'pendente' }
  const base = $derived(`/api/materias/${uid}/topicos`)

  let editando = $state<number | null>(null)
  let tituloEditado = $state('')
  let novo = $state('')

  const filhos = (pai: number | null) => topicos.filter((t) => t.pai_id === pai).sort((a, b) => a.ordem - b.ordem)

  async function executar(acao: () => Promise<unknown>) {
    try {
      await acao()
      onmudou()
    } catch (e) {
      erro(e)
    }
  }

  const mudarStatus = (t: Topico) => executar(() => requisitar('PATCH', `${base}/${t.id}`, { status: PROXIMO[t.status] ?? 'pendente' }))
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
  <li>
    <div class="linha linha-acoes">
      <SeloStatus status={t.status} onclick={() => mudarStatus(t)} />
      {#if editando === t.id}
        <form onsubmit={(e) => { e.preventDefault(); void renomear(t) }}>
          <input aria-label="Novo título" bind:value={tituloEditado} />
          <button class="acao-texto" type="submit">Salvar</button>
        </form>
      {:else}
        <span class="titulo">{t.titulo}</span>
      {/if}
      {#each vinculos[String(t.id)] ?? [] as s (s.secao_id)}
        <a class="secao" href={urlArquivo(uid, s.caminho, s.pagina_pdf_ini)} target="_blank" rel="noopener" title={s.titulo}>{s.codigo} ↗</a>
      {/each}
      {#each listasDoTopico[String(t.id)] ?? [] as codigo (codigo)}<span class="suave">· {codigo}</span>{/each}
      <span class="acoes-linha">
        <button class="acao-texto" aria-label={`Subir ${t.titulo}`} onclick={() => mover(t, -1)}>↑</button>
        <button class="acao-texto" aria-label={`Descer ${t.titulo}`} onclick={() => mover(t, 1)}>↓</button>
        <button class="acao-texto" aria-label={`Renomear ${t.titulo}`} onclick={() => { editando = t.id; tituloEditado = t.titulo }}>editar</button>
        <MenuMais rotulo={`Mais ações de ${t.titulo}`} itens={[{ rotulo: 'Apagar', acao: () => apagar(t), perigo: true }]} />
      </span>
    </div>
    {#if filhos(t.id).length}
      <ul>{#each filhos(t.id) as f (f.id)}{@render item(f)}{/each}</ul>
    {/if}
  </li>
{/snippet}

<ul class="arvore">{#each filhos(null) as t (t.id)}{@render item(t)}{/each}</ul>

<form class="novo" onsubmit={criar}>
  <input aria-label="Novo tópico" placeholder="Novo tópico… (Enter adiciona)" bind:value={novo} />
</form>

<style>
  ul { list-style: none; margin: 0; padding: 0; }
  ul ul { padding-left: 1.5rem; }
  .linha { display: flex; align-items: baseline; gap: 0.8rem; padding: 0.55rem 0.4rem; border-bottom: 1px solid var(--fio); transition: background-color var(--transicao); }
  .linha:hover { background: linear-gradient(90deg, var(--leve), transparent 80%); }
  .titulo { font-size: 0.97rem; }
  .secao { font-size: 0.82rem; color: var(--suave); text-decoration-color: color-mix(in srgb, var(--destaque) 50%, transparent); text-underline-offset: 3px; }
  .acoes-linha { margin-left: auto; display: flex; gap: 0.9rem; align-items: baseline; font-size: 0.85rem; }
  form { display: flex; gap: 0.5rem; }
  input { border: 0; border-bottom: 1px solid var(--fio); padding: 0.25rem 0; background: transparent; color: var(--texto); font: inherit; }
  .novo { margin-top: 0.8rem; }
  .novo input { flex: 0 1 20rem; }
</style>
