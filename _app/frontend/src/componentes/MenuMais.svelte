<script lang="ts">
  // Menu "···" das ações pouco usadas (Recomeçar, Apagar…). Fecha com Esc (devolvendo o foco ao botão), com clique
  // fora, quando o foco sai dele (senão ficaria aberto numa linha que já se escondeu) ou ao escolher um item.
  let { rotulo, itens }: { rotulo: string; itens: { rotulo: string; acao: () => void; perigo?: boolean }[] } = $props()

  let aberto = $state(false)
  let botao: HTMLButtonElement
  let caixa: HTMLDivElement

  function fechar(devolverFoco = false) {
    aberto = false
    if (devolverFoco) botao.focus()
  }

  function escolher(acao: () => void) {
    fechar(true)
    acao()
  }

  $effect(() => {
    if (!aberto) return
    const fora = (e: MouseEvent) => { if (!caixa.contains(e.target as Node)) fechar() }
    const tecla = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); fechar(true) } }
    document.addEventListener('mousedown', fora)
    document.addEventListener('keydown', tecla, true)
    return () => {
      document.removeEventListener('mousedown', fora)
      document.removeEventListener('keydown', tecla, true)
    }
  })
</script>

<div class="mais" bind:this={caixa} onfocusout={(e) => { if (aberto && !caixa.contains(e.relatedTarget as Node | null)) fechar() }}>
  <button bind:this={botao} class="acao-texto gatilho" aria-label={rotulo} aria-haspopup="menu" aria-expanded={aberto}
    onclick={() => (aberto = !aberto)}>···</button>
  {#if aberto}
    <div class="opcoes" role="menu">
      {#each itens as item (item.rotulo)}
        <button role="menuitem" class="acao-texto" class:perigo={item.perigo} onclick={() => escolher(item.acao)}>{item.rotulo}</button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .mais { position: relative; display: inline-block; }
  .gatilho { letter-spacing: 0.12em; padding: 0 0.2rem; }
  .opcoes {
    position: absolute; right: 0; top: calc(100% + 4px); z-index: 20; display: grid; min-width: 9rem;
    background: var(--lateral); border-radius: 6px; padding: 0.3rem 0; box-shadow: 0 8px 24px rgb(0 0 0 / 30%);
  }
  .opcoes button { text-align: left; padding: 0.3rem 0.8rem; }
  .perigo:hover { color: var(--err); }
</style>
