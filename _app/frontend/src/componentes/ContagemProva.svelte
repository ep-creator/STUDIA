<script lang="ts">
  import { dataCurta, diasAte, textoContagem } from '../apresentacao'

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
    <div class="numero-grande">{futura ? textoContagem(prova, hoje) : 'feita'}</div>
    <div class="suave data">{dataCurta(prova.data, prova.hora_inicio)}</div>
  {:else}
    <p class="aviso">Sem data</p>
    {#if hrefImportar}<a class="acao-texto" href={hrefImportar}>importar o calendário</a>{/if}
  {/if}
</section>

<style>
  .numero-grande { margin-top: 0.4rem; }
  .data { font-size: 0.85rem; margin-top: 0.3rem; }
  .aviso { font-family: var(--fonte-titulo); font-size: 1.25rem; margin: 0.4rem 0 0.25rem; }
  .acao-texto { font-size: 0.85rem; }
</style>
