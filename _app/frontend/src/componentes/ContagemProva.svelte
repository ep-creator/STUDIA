<script lang="ts">
  import { dataCurta, diasAte, provaPerto, textoContagem } from '../apresentacao'

  let { prova, hoje, hrefImportar }: {
    prova: { data: string; hora_inicio: string | null } | null
    hoje: Date
    hrefImportar?: string
  } = $props()

  const futura = $derived(prova !== null && diasAte(prova.data, hoje) >= 0)
</script>

<section aria-label="Prova">
  <div class="rotulo">Prova</div>
  {#if prova}
    <div class="numero-grande" class:perto={provaPerto(prova, hoje)}>{futura ? textoContagem(prova, hoje) : 'feita'}</div>
    <div class="suave data">{dataCurta(prova.data, prova.hora_inicio)}</div>
    {#if diasAte(prova.data, hoje) === 0}<p class="dia">Boa prova.</p>{/if}
  {:else}
    <p class="aviso">Sem data</p>
    {#if hrefImportar}<a class="acao-texto" href={hrefImportar}>importar o calendário</a>{/if}
  {/if}
</section>

<style>
  .numero-grande { margin-top: 0.4rem; }
  /* com 7 dias ou menos a contagem fala em brasa (número grande: 3:1 basta) */
  .numero-grande.perto { color: var(--destaque); }
  .dia { margin: 0.5rem 0 0; font-family: var(--fonte-titulo); color: var(--destaque-texto); }
  .data { font-size: 0.85rem; margin-top: 0.3rem; }
  .aviso { font-family: var(--fonte-titulo); font-size: 1.25rem; margin: 0.4rem 0 0.25rem; }
  .acao-texto { font-size: 0.85rem; }
</style>
