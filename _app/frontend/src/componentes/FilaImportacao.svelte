<script lang="ts">
  import { requisitar } from '../api/cliente'
  import { NOME_TIPO } from '../api/proposta'
  import { compararNomes } from '../apresentacao'
  import type { FonteResumo, ImportacaoSaida, ResumoImportacao } from '../api/tipos'
  import { avisar, erro } from '../estado/avisos.svelte'
  import AreaSoltar from './AreaSoltar.svelte'

  let { uid, selecionada, onselecionar, versao, onmudou }: {
    uid: string
    selecionada: number | null
    onselecionar: (id: number | null) => void
    versao: number
    onmudou?: () => void
  } = $props()

  let pendentes = $state<ImportacaoSaida[]>([])
  let nomes = $state<Record<number, string>>({})
  let enviando = $state(false)
  let progresso = $state('')

  const base = $derived(`/api/materias/${uid}/importacoes`)
  const prontas = $derived(pendentes.filter((i) => i.pendencias === 0))
  // O que pede revisão vem primeiro; depois por tipo (programa, calendário… slides) e nome
  const ORDEM_TIPO = ['programa', 'calendario', 'turma', 'livro', 'lista', 'prova', 'slides', 'anotacao', 'outro']
  const ordenados = $derived([...pendentes].sort((a, b) =>
    Number(b.pendencias > 0) - Number(a.pendencias > 0) || ORDEM_TIPO.indexOf(a.tipo) - ORDEM_TIPO.indexOf(b.tipo)
    || compararNomes(nomes[a.fonte_id] ?? '', nomes[b.fonte_id] ?? '')))

  async function carregar() {
    try {
      const [lista, fontes] = await Promise.all([
        requisitar<ImportacaoSaida[]>('GET', `${base}?estado=proposta`),
        requisitar<FonteResumo[]>('GET', `/api/materias/${uid}/fontes`),
      ])
      nomes = Object.fromEntries(fontes.map((f) => [f.id, f.caminho.split('/').pop() ?? f.titulo]))
      pendentes = lista
      if (selecionada !== null && !lista.some((i) => i.id === selecionada)) onselecionar(lista[0]?.id ?? null)
    } catch (e) {
      erro(e)
    }
  }

  $effect(() => {
    void versao
    void carregar()
  })

  async function enviar(arquivos: File[]) {
    enviando = true
    let primeira: number | null = null
    for (const [i, arquivo] of arquivos.entries()) {
      progresso = `Lendo ${arquivo.name} (${i + 1} de ${arquivos.length})…`
      const dados = new FormData()
      dados.append('arquivo', arquivo, arquivo.name)
      try {
        const imp = await requisitar<ImportacaoSaida>('POST', base, dados)
        primeira ??= imp.id
      } catch (e) {
        erro(e)   // um arquivo recusado não impede os outros
      }
    }
    enviando = false
    progresso = ''
    await carregar()
    if (primeira !== null && selecionada === null) onselecionar(primeira)
    onmudou?.()
  }

  async function confirmarProntas() {
    const alvo = [...prontas]
    let feitas = 0
    for (const imp of alvo) {
      try {
        await requisitar<ResumoImportacao>('POST', `${base}/${imp.id}/confirmar`)
        feitas++
      } catch (e) {
        erro(e)
      }
    }
    if (feitas) avisar(`${feitas} ${feitas === 1 ? 'arquivo confirmado' : 'arquivos confirmados'}`)
    await carregar()
    onmudou?.()
  }
</script>

<div class="fila">
  <AreaSoltar onarquivos={enviar} ocupado={enviando} {progresso} />

  {#if pendentes.length}
    <ul aria-label="Arquivos esperando revisão">
      {#each ordenados as imp (imp.id)}
        <li>
          <button class:ativa={imp.id === selecionada} aria-current={imp.id === selecionada ? 'true' : undefined} onclick={() => onselecionar(imp.id)}>
            <span class="nome">{nomes[imp.fonte_id] ?? `Arquivo ${imp.fonte_id}`}</span>
            {#if imp.pendencias > 0}
              <span class="estado revisar" title={`${NOME_TIPO[imp.tipo] ?? imp.tipo}: itens que pedem revisão`}>revisar {imp.pendencias}</span>
            {:else}
              <span class="estado pronto" title={NOME_TIPO[imp.tipo] ?? imp.tipo}>pronto</span>
            {/if}
          </button>
        </li>
      {/each}
    </ul>
    <button class="acao-suave confirmar" disabled={prontas.length === 0} onclick={confirmarProntas}>
      ✔ Confirmar todos sem pendências ({prontas.length})
    </button>
  {:else if !enviando}
    <p class="suave">Nenhum arquivo esperando revisão.</p>
  {/if}
</div>

<style>
  .fila { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.9rem; align-content: start; min-width: 0; }
  ul { list-style: none; margin: 0; padding: 0; display: grid; max-height: 55vh; overflow-y: auto; }
  li button { width: 100%; display: flex; gap: 0.6rem; align-items: baseline; text-align: left; background: none; border: 0; border-left: 2px solid transparent; padding: 0.45rem 0.6rem; cursor: pointer; font: inherit; color: var(--texto); }
  li button.ativa { border-left-color: var(--destaque); font-weight: 600; }
  li button:hover:not(.ativa) { border-left-color: color-mix(in srgb, var(--destaque) 45%, transparent); }
  .nome { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .estado { font-size: 0.78rem; font-weight: 400; }
  .revisar { color: var(--dub); }
  .pronto { color: var(--ok); }
  .confirmar { justify-self: start; }
</style>
