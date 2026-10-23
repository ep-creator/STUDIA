<script lang="ts">
  import { avisos, fecharAviso } from '../estado/avisos.svelte'
</script>

<div class="avisos" role="status" aria-live="polite">
  {#each avisos.lista as aviso (aviso.id)}
    <div class="aviso" class:erro={aviso.tipo === 'erro'}>
      <span>{aviso.texto}</span>
      {#if aviso.acao}
        <button class="botao" onclick={() => { aviso.acao?.executar(); fecharAviso(aviso.id) }}>{aviso.acao.rotulo}</button>
      {/if}
      <button class="fechar" aria-label="Fechar aviso" onclick={() => fecharAviso(aviso.id)}>×</button>
    </div>
  {/each}
</div>

<style>
  .avisos { position: fixed; bottom: 1rem; left: 50%; transform: translateX(-50%); display: grid; gap: 0.5rem; z-index: 20; }
  .aviso { display: flex; gap: 0.75rem; align-items: center; background: var(--texto); color: var(--fundo); padding: 0.5rem 0.9rem; border-radius: var(--raio); box-shadow: 0 4px 16px rgb(0 0 0 / 20%); }
  .aviso.erro { background: var(--err); color: #fff; }
  .aviso .botao { background: transparent; color: inherit; border-color: currentColor; padding: 0 0.6rem; }
  .fechar { background: none; border: 0; color: inherit; cursor: pointer; font-size: 1.1rem; }
</style>
