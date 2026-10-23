<script lang="ts">
  import { escolherTema, tema, type Identidade, type Modo } from '../estado/tema.svelte'
  import Seletor from './Seletor.svelte'

  // 'rodape': empilhado no pé da barra lateral, abrindo para cima. 'topo': em linha, no canto da tela inicial.
  let { posicao = 'rodape' }: { posicao?: 'rodape' | 'topo' } = $props()

  const IDENTIDADES = [{ valor: 'editorial', rotulo: 'Editorial' }, { valor: 'padrao', rotulo: 'Padrão' }]
  const MODOS = [{ valor: 'sistema', rotulo: 'Seguir o sistema' }, { valor: 'claro', rotulo: 'Claro' }, { valor: 'escuro', rotulo: 'Escuro' }]
</script>

<div class="tema {posicao}">
  {#if posicao === 'rodape'}<span class="rotulo">Tema</span>{/if}
  <Seletor rotulo="Identidade visual" opcoes={IDENTIDADES} valor={tema.identidade} onmudar={(v) => escolherTema(v as Identidade, tema.modo)} variante="compacto" />
  <Seletor rotulo="Claro ou escuro" opcoes={MODOS} valor={tema.modo} onmudar={(v) => escolherTema(tema.identidade, v as Modo)} variante="compacto" />
</div>

<style>
  .tema { display: grid; gap: 0.35rem; }
  .rodape :global(.opcoes) { top: auto; bottom: calc(100% + 4px); }
  .topo { display: flex; gap: 0.4rem; }
  .topo :global(.opcoes) { left: auto; right: 0; }
  .topo :global(.gatilho) { border-color: transparent; background: transparent; color: var(--suave); }
  .topo :global(.gatilho:hover), .topo :global(.gatilho[aria-expanded='true']) { color: var(--texto); border-color: var(--destaque); }
</style>
