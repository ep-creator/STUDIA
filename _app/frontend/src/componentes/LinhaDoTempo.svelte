<script lang="ts">
  import type { Sessao, SessaoProgresso } from '../api/tipos'
  import { dataCurta, isoDe } from '../apresentacao'
  import type { ItemLinha } from '../cronograma'
  import Markdown from './Markdown.svelte'

  let { itens, hoje = new Date(), progresso = {}, onfeito, oneditar }: {
    itens: ItemLinha[]
    hoje?: Date
    progresso?: Record<number, SessaoProgresso>   // estado derivado no motor (o mesmo da tela Hoje)
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
        {@const p = progresso[s.id]}
        {#if p?.estado === 'feita' || (!p && s.feito)}<span class="selo-feita">feita</span>
        {:else if p && p.trabalhadas > 0}<span class="selo-parcial" title="questões trabalhadas / questões da sessão">{p.trabalhadas}/{p.total}</span>{/if}
        <span class="acoes-linha">
          <button class="acao-texto" aria-label={`Sessão ${s.codigo}: ${s.feito ? 'desmarcar feita' : 'marcar feita'}`} onclick={() => onfeito(s)}>
            {s.feito ? 'desmarcar' : 'marcar feita'}
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
  .hoje .quando { color: var(--destaque-texto); }
  .prova .quando, .prova .evento { color: var(--destaque-texto); font-weight: 600; }
  .passado, .passado :global(*) { color: var(--suave); }
  .texto { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .evento { color: var(--suave); }
  /* o foco vem do Markdown (um div com parágrafo): aqui fica na mesma linha do código ("S3 · Polares…") */
  .foco :global(.markdown), .foco :global(p) { display: inline; margin: 0; }
  /* o estado numa coluna à direita, antes das ações que aparecem no hover */
  .selo-parcial, .selo-feita { margin-left: auto; min-width: 3.5rem; text-align: right; font-variant-numeric: tabular-nums; }
  .selo-parcial { font-size: 0.85rem; color: var(--suave); }
  .selo-feita { font-size: 0.8rem; color: var(--ok); }
  .acoes-linha { margin-left: auto; display: flex; gap: 0.9rem; font-size: 0.85rem; }
  .selo-parcial + .acoes-linha, .selo-feita + .acoes-linha { margin-left: 0; }
</style>
