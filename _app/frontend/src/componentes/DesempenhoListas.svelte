<script lang="ts">
  import type { ListaComQuestoes } from '../api/tipos'
  import { desempenho } from '../apresentacao'

  // Quanto já foi feito e acertado em cada lista da unidade, com uma barra empilhada (✓ ✗ ? e o que falta)
  let { listas, marcacoes }: { listas: ListaComQuestoes[]; marcacoes: Record<string, string> } = $props()

  const linhas = $derived(listas.map((l) => ({ lista: l, d: desempenho(l, marcacoes) })))
  const soma = $derived(linhas.reduce((t, { d }) => ({ ok: t.ok + d.ok, feitas: t.feitas + d.total - d.falta, total: t.total + d.total }), { ok: 0, feitas: 0, total: 0 }))
  const pct = (n: number, de: number) => (de ? Math.round((n / de) * 100) : 0)
</script>

<section class="cartao bloco" aria-label="Desempenho nas listas">
  <div class="rotulo">Desempenho nas listas</div>
  {#if listas.length === 0}
    <p class="suave">Nenhuma lista nesta unidade ainda.</p>
  {:else}
    <div class="resumo">
      <div><span class="numero">{pct(soma.feitas, soma.total)}%</span><span class="suave">feito</span></div>
      <div><span class="numero">{pct(soma.ok, soma.feitas)}%</span><span class="suave">de acerto</span></div>
    </div>
    <ul>
      {#each linhas as { lista, d } (lista.id)}
        <li>
          <div class="linha">
            <span class="nome">{lista.titulo}</span>
            <span class="suave">{d.total - d.falta}/{d.total} feitas</span>
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
  .resumo { display: flex; gap: 2rem; margin: 0.4rem 0 0.9rem; }
  .resumo div { display: grid; }
  .numero { font-family: var(--fonte-titulo); font-size: 2rem; line-height: 1.1; }
  ul { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.7rem; }
  .linha { display: flex; justify-content: space-between; gap: 1rem; font-size: 0.92rem; margin-bottom: 0.25rem; }
  .nome { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .linha .suave { flex: none; font-size: 0.85rem; }
  .barra { display: flex; height: 6px; border-radius: 3px; overflow: hidden; background: color-mix(in srgb, var(--borda) 25%, transparent); }
  .barra span { transition: width 400ms ease; }
  .ok { background: var(--ok); }
  .err { background: var(--err); }
  .dub { background: var(--dub); }
  p { margin: 0; }
</style>
