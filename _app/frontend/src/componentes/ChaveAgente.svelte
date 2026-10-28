<script lang="ts">
  // Chave do Gemini na página do Assistente: mostra se há chave e deixa trocar (para corrigir uma chave errada).
  // A chave nunca volta para a tela; trocar grava por cima.
  import { tick } from 'svelte'
  import { requisitar } from '../api/cliente'
  import type { EstadoAgente } from '../api/tipos'
  import { ia } from '../estado/ia.svelte'
  import ConfigurarChave from './ConfigurarChave.svelte'

  let configurada = $state<boolean | null>(null)
  let trocando = $state(false)
  let caixa: HTMLElement

  $effect(() => {
    void ia.versaoChave
    requisitar<EstadoAgente>('GET', '/api/agente/estado').then((e) => (configurada = e.chave_configurada), () => {})
  })

  async function abrir() {
    trocando = true
    await tick()
    caixa.querySelector('input')?.focus()
  }

  function salvo() {
    trocando = false
    ia.versaoChave++   // os painéis abertos releem o estado e escondem a caixa da chave
  }
</script>

<section class="chave" aria-label="Chave do Gemini" bind:this={caixa}>
  <div class="linha">
    <span class="rotulo">API key</span>
    {#if configurada !== null}
      <span class:ok={configurada}>{configurada ? 'configurada' : 'não configurada'}</span>
    {/if}
    {#if !trocando}
      <button class="acao-texto" aria-label="trocar a chave" onclick={() => void abrir()}>{configurada ? 'trocar' : 'colar'}</button>
    {:else}
      <button class="acao-texto" onclick={() => (trocando = false)}>cancelar</button>
    {/if}
  </div>
  {#if trocando}<ConfigurarChave onsalvo={salvo} />{/if}
</section>

<style>
  .chave { display: grid; gap: 0.5rem; padding: 0.8rem 0.6rem 0; margin-top: 1.2rem; border-top: 1px solid var(--fio); font-size: 0.85rem; }
  .linha { display: flex; align-items: baseline; gap: 0.6rem; color: var(--suave); }
  .linha .acao-texto { margin-left: auto; }
  .ok { color: var(--ok); }
</style>
