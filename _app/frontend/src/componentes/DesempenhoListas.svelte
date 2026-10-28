<script lang="ts">
  import type { ListaComQuestoes } from '../api/tipos'
  import { desempenho } from '../apresentacao'

  // Quanto já foi feito e acertado em cada lista da unidade, com uma barra empilhada (✓ ✗ ? e o que falta)
  let { listas, marcacoes }: { listas: ListaComQuestoes[]; marcacoes: Record<string, string> } = $props()

  const linhas = $derived(listas.map((l) => ({ lista: l, d: desempenho(l, marcacoes) })))
  const soma = $derived(linhas.reduce((t, { d }) => ({ ok: t.ok + d.ok, feitas: t.feitas + d.total - d.falta, total: t.total + d.total }), { ok: 0, feitas: 0, total: 0 }))
  const pct = (n: number, de: number) => (de ? Math.round((n / de) * 100) : 0)
</script>

<section class="bloco" aria-label="Desempenho nas listas">
  <div class="rotulo">Desempenho nas listas</div>
  {#if listas.length === 0}
    <p class="suave">Nenhuma lista ainda.</p>
  {:else}
    <div class="resumo">
      <div><span class="numero-grande">{pct(soma.feitas, soma.total)}<small>%</small></span><span class="suave">feito</span></div>
      <div><span class="numero-grande">{#if soma.feitas}{pct(soma.ok, soma.feitas)}<small>%</small>{:else}—{/if}</span><span class="suave">de acerto</span></div>
    </div>
    <ul>
      {#each linhas as { lista, d } (lista.id)}
        <li>
          <div class="linha">
            <span class="nome">{lista.titulo}</span>
            <span class="suave">{d.total - d.falta}/{d.total}</span>
          </div>
          <div class="barra" aria-hidden="true">
            <span class="ok" style:width={`${pct(d.ok, d.total)}%`}></span>
            <span class="err" style:width={`${pct(d.err, d.total)}%`}></span>
            <span class="dub" style:width={`${pct(d.dub, d.total)}%`}></span>
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .resumo { display: flex; gap: 2.4rem; margin: 0.4rem 0 1rem; }
  .resumo div { display: grid; gap: 0.3rem; }
  .resumo .suave { font-size: 0.85rem; }
  .numero-grande small { font-size: 1.1rem; color: var(--suave); }
  ul { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.55rem; }
  .linha { display: flex; justify-content: space-between; gap: 1rem; font-size: 0.92rem; margin-bottom: 0.3rem; }
  .nome { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .linha .suave { flex: none; font-size: 0.8rem; font-variant-numeric: tabular-nums; }
  /* fio: 1 px de fundo, 2 px coloridos para acertos, erros e dúvidas */
  .barra { display: flex; height: 1px; background: var(--fio); }
  .barra span { height: 2px; margin-top: -0.5px; transition: width 400ms ease; }
  .ok { background: var(--ok); }
  .err { background: var(--err); }
  .dub { background: var(--dub); }
  p { margin: 0; }
</style>
