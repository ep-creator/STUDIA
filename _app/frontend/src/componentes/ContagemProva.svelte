<script lang="ts">
  import { dataCurta, diasAte, textoContagem } from '../apresentacao'

  let { prova, hoje, hrefImportar }: {
    prova: { data: string; hora_inicio: string | null } | null
    hoje: Date
    hrefImportar?: string
  } = $props()

  // Número grande só para a contagem; prova passada ou sem data é um aviso, não uma manchete
  const futura = $derived(prova !== null && diasAte(prova.data, hoje) >= 0)
</script>

<section class="cartao">
  <div class="rotulo">Prova</div>
  {#if futura}
    <div class="numero-grande">{textoContagem(prova, hoje)}</div>
    <div class="suave">{dataCurta(prova!.data, prova!.hora_inicio)}</div>
  {:else if prova}
    <p class="aviso">Já foi em {dataCurta(prova.data, prova.hora_inicio)}.</p>
  {:else}
    <p class="aviso">Sem data de prova nesta unidade.</p>
    {#if hrefImportar}<a class="suave" href={hrefImportar}>Importar o calendário</a>{/if}
  {/if}
</section>

<style>
  .aviso { font-family: var(--fonte-titulo); font-size: 1.15rem; margin: 0.4rem 0 0.25rem; }
</style>
