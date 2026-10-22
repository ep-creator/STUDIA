<script lang="ts">
  import { dataCurta, textoContagem } from '../apresentacao'

  let { prova, hoje }: { prova: { data: string; hora_inicio: string | null } | null; hoje: Date } = $props()
</script>

<section class="cartao">
  <div class="rotulo">Prova</div>
  <div class="numero-grande">{textoContagem(prova, hoje)}</div>
  {#if prova}<div class="suave">{dataCurta(prova.data, prova.hora_inicio)}</div>{/if}
</section>
