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

<section class="cartao bloco" aria-label="Para revisar">
  <header>
    <div class="rotulo">Para revisar</div>
    {#if total}<span class="conta">{total} {total === 1 ? 'questão' : 'questões'}</span>{/if}
  </header>
  {#if total === 0}
    <p class="suave">Nada marcado com ✗ ou ? nesta unidade. Quando errar ou ficar em dúvida numa questão, ela aparece aqui.</p>
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
            >{questao.rotulo} <span aria-hidden="true">{SIMBOLO[marca]}</span></a>
          {/each}
        </div>
      </div>
    {/each}
  {/if}
</section>

<style>
  header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }
  .conta { font-size: 0.8rem; color: var(--destaque); font-weight: 600; }
  .grupo { padding: 0.55rem 0; border-top: 1px solid color-mix(in srgb, var(--borda) 35%, transparent); }
  .assunto { font-family: var(--fonte-titulo); font-size: 0.98rem; margin-bottom: 0.4rem; }
  .questoes { display: flex; flex-wrap: wrap; gap: 0.35rem; }
  .questao {
    min-width: 2.4rem; padding: 0.15rem 0.5rem; border-radius: 6px; text-align: center; text-decoration: none; font-size: 0.92rem;
    transition: transform var(--transicao), box-shadow var(--transicao);
  }
  .questao:hover { transform: translateY(-1px); box-shadow: 0 3px 10px rgb(0 0 0 / 18%); }
  .questao.err { background: var(--err); color: #fff; }
  .questao.dub { background: var(--dub); color: #000; }
  p { margin: 0; }
</style>
