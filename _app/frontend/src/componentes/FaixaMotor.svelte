<script lang="ts">
  import { conexao } from '../estado/conexao.svelte'
</script>

{#if !conexao.motorLigado}
  <div class="faixa" role="alert">Motor desligado: abra o abrir-novo.bat. Tentando reconectar…</div>
{/if}

<style>
  .faixa { position: sticky; top: 0; z-index: 30; background: var(--err); color: #fff; padding: 0.5rem 1rem; text-align: center; }
</style>
