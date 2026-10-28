<script lang="ts">
  import type { ListaComQuestoes } from '../api/tipos'
  import { paraRevisar } from '../apresentacao'
  import { pedido } from '../estado/pedido.svelte'
  import { SIMBOLO } from '../estado/marcacoes.svelte'

  // Questões marcadas ✗ ou ?: um clique abre a questão nas Listas, com o menu e a resolução
  let { listas, marcacoes, hrefListas }: { listas: ListaComQuestoes[]; marcacoes: Record<string, string>; hrefListas: string } = $props()

  const grupos = $derived(paraRevisar(listas, marcacoes))
  const total = $derived(grupos.reduce((t, g) => t + g.questoes.length, 0))
</script>

<section class="bloco" aria-label="Para revisar">
  <div class="rotulo">Para revisar{total ? ` · ${total}` : ''}</div>
  {#if total === 0}
    <p class="suave">Nada para revisar ainda.</p>
  {:else}
    {#each grupos as g (g.lista.id)}
      <div class="grupo">
        <div class="assunto">{g.lista.titulo}</div>
        <div class="questoes">
          {#each g.questoes as { questao, marca } (questao.id)}
            <a
              class="questao {marca}"
              href={hrefListas}
              aria-label={`${g.lista.codigo} #${questao.rotulo} (${SIMBOLO[marca]})`}
              onclick={() => (pedido.questao = questao.id)}
            >{questao.rotulo}</a>
          {/each}
        </div>
      </div>
    {/each}
  {/if}
</section>

<style>
  .rotulo { margin-bottom: 0.4rem; }
  .grupo { padding: 0.45rem 0; }
  .assunto { font-family: var(--fonte-titulo); font-size: 1rem; margin-bottom: 0.3rem; }
  /* só os números, no estilo da grade das Listas */
  .questoes { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; }
  .questao { padding: 0 2px; text-decoration: none; font-variant-numeric: tabular-nums; border-bottom: 2px solid transparent; }
  .questao:hover { color: var(--destaque); }
  .questao.err { color: var(--err); border-bottom-color: var(--err); }
  .questao.dub { color: var(--dub); border-bottom-color: var(--dub); }
  p { margin: 0; }
</style>
