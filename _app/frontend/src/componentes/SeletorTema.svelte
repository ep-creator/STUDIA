<script lang="ts">
  import { escolherModo, tema, type Modo } from '../estado/tema.svelte'

  // 'rodape': no pé da barra lateral. 'topo': no canto da tela inicial.
  let { posicao = 'rodape' }: { posicao?: 'rodape' | 'topo' } = $props()

  const MODOS: { valor: Modo; rotulo: string }[] = [
    { valor: 'claro', rotulo: 'Claro' }, { valor: 'escuro', rotulo: 'Escuro' }, { valor: 'sistema', rotulo: 'Sistema' },
  ]
</script>

<div class="tema {posicao}" role="group" aria-label="Tema">
  {#each MODOS as m (m.valor)}
    <button class="acao-texto" class:ativa={tema.modo === m.valor} aria-pressed={tema.modo === m.valor} onclick={() => escolherModo(m.valor)}>
      {m.rotulo}
    </button>
  {/each}
</div>

<style>
  .tema { display: flex; gap: 0.9rem; font-size: 0.85rem; padding: 0 0.5rem; }
  .ativa { color: var(--texto); border-bottom: 1.5px solid var(--destaque); }
</style>
