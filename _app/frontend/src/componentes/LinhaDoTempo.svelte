<script lang="ts">
  import type { Sessao } from '../api/tipos'
  import { dataCurta, isoDe } from '../apresentacao'
  import type { ItemLinha } from '../cronograma'
  import Markdown from './Markdown.svelte'

  let { itens, hoje = new Date(), onfeito, oneditar }: {
    itens: ItemLinha[]
    hoje?: Date
    onfeito: (s: Sessao) => void
    oneditar: (s: Sessao) => void
  } = $props()

  const ROTULO: Record<string, string> = {
    aula: 'Aula', prova: 'PROVA', extra: 'Aula extra', feriado: 'Feriado · sem aula', segunda_chamada: 'Segunda chamada',
    exame_final: 'Exame final',
  }
  const hojeIso = $derived(isoDe(hoje))
  // na linha do tempo, só a primeira linha do foco (o resto aparece ao editar)
  const primeiraLinha = (md: string) => md.split('\n').find((l) => l.trim()) ?? ''
</script>

<ol class="linha">
  {#each itens as item, i (i)}
    <li class="linha-acoes" class:hoje={item.data === hojeIso} class:prova={item.tipo === 'prova'} class:passado={item.data !== null && item.data < hojeIso}>
      <span class="quando">{item.data ? dataCurta(item.data, item.hora) : 'sem data'}{item.data === hojeIso ? ' · hoje' : ''}</span>
      {#if item.sessao}
        {@const s = item.sessao}
        <span class="texto">
          <b>{s.codigo}</b>{#if s.foco_md} · <span class="foco"><Markdown texto={primeiraLinha(s.foco_md)} /></span>{/if}
        </span>
        {#if s.feito}<span class="selo-feita">feita</span>{/if}
        <span class="acoes-linha">
          <button class="acao-texto" aria-label={`Sessão ${s.codigo}: ${s.feito ? 'desmarcar feita' : 'marcar feita'}`} onclick={() => onfeito(s)}>
            {s.feito ? 'desmarcar' : 'feita'}
          </button>
          <button class="acao-texto" aria-label={`Editar sessão ${s.codigo}`} onclick={() => oneditar(s)}>editar</button>
        </span>
      {:else if item.evento}
        <span class="texto evento">{ROTULO[item.tipo] ?? item.tipo}{item.evento.descricao ? ` · ${item.evento.descricao}` : ''}</span>
      {/if}
    </li>
  {/each}
</ol>

<style>
  .linha { list-style: none; margin: 0; padding: 0; }
  li { display: flex; align-items: baseline; gap: 0.9rem; padding: 0.5rem 0; border-bottom: 1px solid var(--fio); }
  .quando { width: 8.5rem; flex: none; color: var(--suave); font-size: 0.85rem; font-variant-numeric: tabular-nums; }
  .hoje .quando { color: var(--destaque); }
  .prova .quando, .prova .evento { color: var(--destaque); font-weight: 600; }
  .passado { opacity: 0.6; }
  .texto { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .evento { color: var(--suave); }
  .foco :global(p) { display: inline; margin: 0; }
  .selo-feita { font-size: 0.78rem; color: var(--ok); }
  .acoes-linha { margin-left: auto; display: flex; gap: 0.9rem; font-size: 0.85rem; }
</style>
