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
</script>

<ol class="linha">
  {#each itens as item, i (i)}
    <li class:hoje={item.data === hojeIso} class:prova={item.tipo === 'prova'} class:passado={item.data !== null && item.data < hojeIso}>
      <span class="quando">{item.data ? dataCurta(item.data, item.hora) : 'sem data'}{item.data === hojeIso ? ' · hoje' : ''}</span>
      {#if item.sessao}
        {@const s = item.sessao}
        <label class="feito"><input type="checkbox" checked={s.feito} onchange={() => onfeito(s)} aria-label={`Sessão ${s.codigo} feita`} /></label>
        <span class="texto" class:riscado={s.feito}>
          <b>{s.codigo}</b>{#if s.foco_md} · <span class="foco"><Markdown texto={s.foco_md} /></span>{/if}
        </span>
        <button class="editar" aria-label={`Editar sessão ${s.codigo}`} onclick={() => oneditar(s)}>✎</button>
      {:else if item.evento}
        <span class="texto evento">{ROTULO[item.tipo] ?? item.tipo}{item.evento.descricao ? ` · ${item.evento.descricao}` : ''}</span>
      {/if}
    </li>
  {/each}
</ol>

<style>
  .linha { list-style: none; margin: 0; padding: 0; }
  li { display: flex; align-items: baseline; gap: 0.75rem; padding: 0.4rem 0; border-top: 1px solid color-mix(in srgb, var(--borda) 25%, transparent); }
  .quando { width: 9rem; flex: none; font-weight: 600; }
  .hoje .quando { color: var(--destaque); }
  .prova { font-weight: 700; }
  .passado { opacity: 0.6; }
  .evento { color: var(--suave); }
  .prova .evento { color: var(--texto); }
  .riscado { text-decoration: line-through; color: var(--suave); }
  .foco :global(p) { display: inline; margin: 0; }
  .editar { margin-left: auto; background: none; border: 0; cursor: pointer; opacity: 0.5; }
</style>
