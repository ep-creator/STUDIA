<script lang="ts" module>
  const CHAVE = 'studia.abertura'

  /** A abertura roda uma vez por sessão, e nunca com "reduzir movimento" ligado. */
  export function deveAbrir(): boolean {
    try {
      if (typeof matchMedia !== 'function' || matchMedia('(prefers-reduced-motion: reduce)').matches) return false
      return sessionStorage.getItem(CHAVE) !== 'vista'
    } catch {
      return false
    }
  }
</script>

<script lang="ts">
  // STUDIA desenhado traço a traço em laranja, preenchido, e depois "voando" para o lugar da marca no topo.
  // Um clique em qualquer lugar pula direto para o fim.
  import { onMount } from 'svelte'

  let { alvo, onfim }: { alvo: () => HTMLElement | null | undefined; onfim: () => void } = $props()

  let raiz: HTMLDivElement
  let texto: SVGTextElement
  let fundo: HTMLDivElement
  let traco: HTMLSpanElement
  let desenhando = $state(false)
  let terminou = false

  function terminar() {
    if (terminou) return
    terminou = true
    try { sessionStorage.setItem(CHAVE, 'vista') } catch { /* sem armazenamento: só repete na próxima vez */ }
    onfim()
  }

  function voar() {
    const destino = alvo()
    if (!destino || terminou) return terminar()
    const de = texto.getBoundingClientRect()
    const para = destino.getBoundingClientRect()
    const escala = parseFloat(getComputedStyle(destino).fontSize) / parseFloat(getComputedStyle(texto).fontSize)
    const dx = para.left - de.left
    const dy = para.top + para.height / 2 - (de.top + de.height / 2)
    const curva = 'cubic-bezier(0.7, 0, 0.2, 1)'
    texto.animate(
      [{ transform: 'none' }, { transform: `translate(${dx}px, ${dy}px) scale(${escala})` }],
      { duration: 750, easing: curva, fill: 'forwards' },
    )
    raiz.style.pointerEvents = 'none'
    fundo.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 600, delay: 250, easing: 'ease-out', fill: 'forwards' }).finished.then(terminar, terminar)
  }

  onMount(() => {
    let espera: ReturnType<typeof setTimeout>
    const comecar = () => {
      // o sublinhado acompanha a palavra desenhada (o espaçamento entre letras desloca o centro do texto)
      const r = texto.getBoundingClientRect()
      const sobra = parseFloat(getComputedStyle(texto).letterSpacing) || 0
      Object.assign(traco.style, { left: `${r.left}px`, width: `${r.width - sobra}px`, top: `${r.bottom + 18}px` })
      desenhando = true
      espera = setTimeout(voar, 2100)
    }
    // espera a fonte do título carregar, senão o desenho começa numa fonte e termina em outra
    void (document.fonts?.ready ?? Promise.resolve()).then(() => requestAnimationFrame(comecar))
    return () => clearTimeout(espera)
  })
</script>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div class="abertura" bind:this={raiz} onclick={terminar} aria-hidden="true">
  <div class="fundo" bind:this={fundo}></div>
  <svg class="palavra" class:desenhando width="1" height="1">
    <text bind:this={texto} text-anchor="middle" dominant-baseline="central">STUDIA</text>
  </svg>
  <span class="traco" class:desenhando bind:this={traco}></span>
</div>

<style>
  .abertura { position: fixed; inset: 0; z-index: 100; cursor: pointer; }
  .fundo { position: absolute; inset: 0; background: var(--fundo); }
  .palavra { position: absolute; left: 50%; top: 46%; overflow: visible; }
  text {
    font-family: var(--fonte-titulo); font-weight: 600; letter-spacing: 0.28em;
    font-size: clamp(3.2rem, 12vw, 8.5rem);
    fill: var(--texto); fill-opacity: 0; stroke: var(--destaque); stroke-width: 1.2;
    stroke-dasharray: 1400; stroke-dashoffset: 1400; transform-box: fill-box; transform-origin: left center;
  }
  :global(:root[data-tema^='editorial']) text { font-weight: 500; }
  .desenhando text { animation: desenhar 1.5s cubic-bezier(0.55, 0, 0.3, 1) forwards, preencher 0.6s ease 1.15s forwards; }
  @keyframes desenhar { to { stroke-dashoffset: 0; } }
  @keyframes preencher { to { fill-opacity: 1; stroke-opacity: 0; } }

  /* sublinhado laranja que corre por baixo enquanto a palavra é desenhada, e some antes do voo */
  .traco {
    position: absolute; height: 2px; background: var(--destaque); transform: scaleX(0); transform-origin: left;
  }
  .traco.desenhando { animation: correr 1.3s cubic-bezier(0.55, 0, 0.3, 1) 0.2s forwards, apagar 0.4s ease 1.7s forwards; }
  @keyframes correr { to { transform: scaleX(1); } }
  @keyframes apagar { to { opacity: 0; } }
</style>
