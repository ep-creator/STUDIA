<script lang="ts">
  // Caixa de seleção do próprio app (a nativa abre branca e ilegível no tema escuro).
  // Teclado: ↓/↑ abre e anda, Enter/Espaço escolhe, Esc fecha, letras pulam para a opção que começa por elas.
  import { tick } from 'svelte'

  export type Opcao = { valor: string; rotulo: string; detalhe?: string }

  let { rotulo, opcoes, valor, onmudar, variante = 'campo', mostrarRotulo = false, vazio = 'escolha…' }: {
    rotulo: string
    opcoes: Opcao[]
    valor: string | null
    onmudar: (valor: string) => void
    variante?: 'campo' | 'titulo' | 'compacto'
    mostrarRotulo?: boolean
    vazio?: string
  } = $props()

  const id = `seletor-${Math.random().toString(36).slice(2, 9)}`
  let aberto = $state(false)
  let ativo = $state(0)
  let raiz: HTMLDivElement
  let lista = $state<HTMLUListElement>()

  const atual = $derived(opcoes.find((o) => o.valor === valor) ?? null)

  async function abrir() {
    ativo = Math.max(0, opcoes.findIndex((o) => o.valor === valor))
    aberto = true
    await tick()
    lista?.querySelector<HTMLElement>(`[data-indice="${ativo}"]`)?.scrollIntoView?.({ block: 'nearest' })
  }

  function escolher(i: number) {
    const opcao = opcoes[i]
    aberto = false
    if (opcao && opcao.valor !== valor) onmudar(opcao.valor)
  }

  async function mover(delta: number) {
    ativo = (ativo + delta + opcoes.length) % opcoes.length
    await tick()
    lista?.querySelector<HTMLElement>(`[data-indice="${ativo}"]`)?.scrollIntoView?.({ block: 'nearest' })
  }

  function teclar(e: KeyboardEvent) {
    if (!aberto) {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) { e.preventDefault(); void abrir() }
      return
    }
    if (e.key === 'ArrowDown') { e.preventDefault(); void mover(1) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); void mover(-1) }
    else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); escolher(ativo) }
    else if (e.key === 'Escape' || e.key === 'Tab') { aberto = false }
    else if (e.key.length === 1) {
      const i = opcoes.findIndex((o) => o.rotulo.toLowerCase().startsWith(e.key.toLowerCase()))
      if (i >= 0) { ativo = i; void mover(0) }
    }
  }

  $effect(() => {
    if (!aberto) return
    const fora = (e: MouseEvent) => { if (!raiz.contains(e.target as Node)) aberto = false }
    document.addEventListener('mousedown', fora)
    return () => document.removeEventListener('mousedown', fora)
  })
</script>

<div class="seletor {variante}" bind:this={raiz}>
  {#if mostrarRotulo}<span class="rotulo" id={`${id}-rotulo`}>{rotulo}</span>{/if}
  <button
    type="button"
    class="gatilho"
    aria-haspopup="listbox"
    aria-expanded={aberto}
    aria-label={`${rotulo}: ${atual?.rotulo ?? vazio}`}
    onclick={() => (aberto ? (aberto = false) : abrir())}
    onkeydown={teclar}
  >
    <span class="texto" class:vazio={!atual}>{atual?.rotulo ?? vazio}</span>
    <svg class="seta" viewBox="0 0 12 12" aria-hidden="true"><path d="M3 4.5 6 7.5 9 4.5" /></svg>
  </button>
  {#if aberto}
    <ul class="opcoes" role="listbox" aria-label={rotulo} bind:this={lista}>
      {#each opcoes as o, i (o.valor)}
        <li
          role="option"
          data-indice={i}
          aria-selected={o.valor === valor}
          class:ativo={i === ativo}
          onmousedown={(e) => e.preventDefault()}
          onclick={() => escolher(i)}
          onkeydown={teclar}
          onmouseenter={() => (ativo = i)}
        >
          <span>{o.rotulo}</span>
          {#if o.detalhe}<span class="detalhe">{o.detalhe}</span>{/if}
          {#if o.valor === valor}<span class="marca" aria-hidden="true">✓</span>{/if}
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .seletor { position: relative; display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.2rem; min-width: 0; }
  .gatilho {
    display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; width: 100%;
    background: var(--cartao); color: var(--texto); border: 1px solid color-mix(in srgb, var(--borda) 60%, transparent);
    border-radius: 8px; padding: 0.3rem 0.6rem; cursor: pointer; text-align: left;
    transition: border-color 150ms ease, box-shadow 150ms ease;
  }
  .gatilho:hover, .gatilho[aria-expanded='true'] { border-color: var(--destaque); }
  .gatilho:focus-visible { outline: none; box-shadow: 0 0 0 3px color-mix(in srgb, var(--destaque) 30%, transparent); }
  .texto { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .vazio { color: var(--suave); }
  .seta { width: 0.8rem; height: 0.8rem; flex: none; fill: none; stroke: currentColor; stroke-width: 1.5; opacity: 0.6; transition: transform 150ms ease; }
  .gatilho[aria-expanded='true'] .seta { transform: rotate(180deg); }

  .titulo .gatilho { background: transparent; border-color: transparent; padding: 0.2rem 0.4rem; font-family: var(--fonte-titulo); font-weight: 600; font-size: 1.05rem; }
  .titulo .gatilho:hover, .titulo .gatilho[aria-expanded='true'] { background: color-mix(in srgb, var(--destaque) 8%, transparent); border-color: transparent; }
  /* nome longo de matéria quebra em duas linhas em vez de empurrar a barra lateral para o lado */
  .titulo .texto { white-space: normal; line-height: 1.25; }
  .titulo .opcoes { max-width: 100%; }
  .titulo li { white-space: normal; }
  .compacto .gatilho { padding: 0.15rem 0.5rem; font-size: 0.9rem; }

  .opcoes {
    position: absolute; top: calc(100% + 4px); left: 0; min-width: 100%; max-width: 30rem; max-height: 18rem; overflow-y: auto;
    z-index: 40; list-style: none; margin: 0; padding: 0.3rem; background: var(--cartao); color: var(--texto);
    border: 1px solid color-mix(in srgb, var(--borda) 50%, transparent); border-radius: 10px;
    box-shadow: 0 12px 32px rgb(0 0 0 / 28%); animation: surgir 120ms ease-out;
  }
  li { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.6rem; border-radius: 6px; cursor: pointer; white-space: nowrap; }
  li.ativo { background: color-mix(in srgb, var(--destaque) 14%, transparent); }
  li[aria-selected='true'] { font-weight: 600; }
  .detalhe { color: var(--suave); font-size: 0.85em; }
  .marca { margin-left: auto; color: var(--destaque); }
  .opcoes { border-radius: 4px; }
  .gatilho { border-radius: 4px; }

  @keyframes surgir { from { opacity: 0; transform: translateY(-4px); } }
  @media (prefers-reduced-motion: reduce) { .opcoes { animation: none; } .seta { transition: none; } }
</style>
