<script lang="ts">
  import type { Sessao, SessaoProgresso } from '../api/tipos'
  import { dataCurta, focoDaSessao, isoDe } from '../apresentacao'
  import type { ItemLinha } from '../cronograma'

  let { itens, hoje = new Date(), progresso = {}, onfeito, oneditar, hrefPraticar }: {
    itens: ItemLinha[]
    hoje?: Date
    progresso?: Record<number, SessaoProgresso>   // estado derivado no motor (o mesmo da tela Hoje)
    onfeito: (s: Sessao) => void
    oneditar: (s: Sessao) => void
    hrefPraticar?: (s: Sessao) => string          // Praticar dentro da sessão (só para sessão com questões)
  } = $props()

  const ROTULO: Record<string, string> = {
    aula: 'Aula', prova: 'PROVA', extra: 'Aula extra', feriado: 'Feriado · sem aula', segunda_chamada: 'Segunda chamada',
    exame_final: 'Exame final',
  }
  const hojeIso = $derived(isoDe(hoje))
  // na linha do tempo, só a primeira linha do foco, em título e detalhe como em Hoje (o resto aparece ao editar)
</script>

<ol class="linha">
  {#each itens as item, i (i)}
    <!-- a linha de hoje, mesmo sem nada marcado para hoje: separa o que passou do que vem -->
    {#if item.data && item.data > hojeIso && (i === 0 || (itens[i - 1].data ?? '') < hojeIso)}
      <li class="marco-hoje" aria-label="Hoje, {dataCurta(hojeIso)}"><span class="quando">{dataCurta(hojeIso)} · hoje</span><span class="fio-hoje"></span></li>
    {/if}
    <li class="linha-acoes" class:hoje={item.data === hojeIso} class:prova={item.tipo === 'prova'} class:passado={item.data !== null && item.data < hojeIso}>
      <span class="quando">{item.data ? dataCurta(item.data, item.hora) : 'sem data'}{item.data === hojeIso ? ' · hoje' : ''}</span>
      {#if item.sessao}
        {@const s = item.sessao}
        {@const foco = focoDaSessao(s.foco_md)}
        {@const p = progresso[s.id]}
        <span class="texto">
          <b>{s.codigo}</b>{#if foco.titulo} <span class="foco-titulo">{foco.titulo}</span>{/if}{#if foco.detalhe} <span class="suave foco-detalhe">{foco.detalhe}</span>{/if}
        </span>
        {#if p?.estado === 'feita' || (!p && s.feito)}<span class="selo-feita">feita</span>
        {:else if p && p.total > 0}<span class="selo-parcial" title="questões trabalhadas / questões da sessão">{p.trabalhadas}/{p.total}</span>{/if}
        <span class="acoes-linha">
          {#if hrefPraticar && s.questao_ids.length && p?.estado !== 'feita'}
            <a class="acao-texto" aria-label={`Praticar a sessão ${s.codigo}`} href={hrefPraticar(s)}>praticar</a>
          {/if}
          <!-- feita pelas questões não se desmarca à mão: o botão só aparece quando a mão decide -->
          {#if s.feito || p?.estado !== 'feita'}
            <button class="acao-texto" aria-label={`Sessão ${s.codigo}: ${s.feito ? 'desmarcar feita' : 'marcar feita'}`} onclick={() => onfeito(s)}>
              {s.feito ? 'desmarcar' : 'marcar feita'}
            </button>
          {/if}
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
  .foco-titulo { margin-left: 0.5rem; }
  .foco-detalhe { margin-left: 0.6rem; }
  /* o estado numa coluna à direita, antes das ações que aparecem no hover */
  .marco-hoje { border-bottom: 0; padding: 0.3rem 0; }
  .marco-hoje .quando { color: var(--destaque-texto); }
  .fio-hoje { flex: 1; height: 1px; background: var(--destaque); align-self: center; }
  .selo-parcial, .selo-feita { margin-left: auto; min-width: 3.5rem; text-align: right; font-variant-numeric: tabular-nums; }
  .selo-parcial { font-size: 0.85rem; color: var(--suave); }
  .selo-feita { font-size: 0.8rem; color: var(--ok); }
  .acoes-linha { margin-left: auto; display: flex; gap: 0.9rem; font-size: 0.85rem; }
  .selo-parcial + .acoes-linha, .selo-feita + .acoes-linha { margin-left: 0; }
</style>
