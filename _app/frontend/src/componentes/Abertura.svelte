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
  // STUDIA digitado letra a letra, como numa máquina de escrever, com o cursor laranja piscando;
  // depois a palavra "voa" para o lugar da marca no topo. Um clique em qualquer lugar pula direto para o fim.
  import { onMount } from 'svelte'

  let { alvo, onfim }: { alvo: () => HTMLElement | null | undefined; onfim: () => void } = $props()

  const PALAVRA = 'STUDIA'
  // ritmo de quem digita: nem todas as teclas levam o mesmo tempo
  const INTERVALOS = [170, 120, 150, 110, 160, 130]

  let raiz: HTMLDivElement
  let texto: HTMLSpanElement
  let fundo: HTMLDivElement
  let digitadas = $state(0)
  let digitando = $state(false)
  let cursorFora = $state(false)
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
    texto.animate(
      [{ transform: 'none' }, { transform: `translate(${dx}px, ${dy}px) scale(${escala})` }],
      { duration: 750, easing: 'cubic-bezier(0.7, 0, 0.2, 1)', fill: 'forwards' },
    )
    raiz.style.pointerEvents = 'none'
    fundo.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 600, delay: 250, easing: 'ease-out', fill: 'forwards' }).finished.then(terminar, terminar)
  }

  onMount(() => {
    const esperas: ReturnType<typeof setTimeout>[] = []
    const depois = (ms: number, f: () => void) => esperas.push(setTimeout(f, ms))
    // espera a fonte do título carregar, senão a palavra muda de fonte no meio da digitação
    void (document.fonts?.ready ?? Promise.resolve()).then(() => {
      let t = 650 // o cursor pisca um pouco antes da primeira tecla
      depois(t, () => (digitando = true))
      for (let i = 0; i < PALAVRA.length; i++) {
        t += INTERVALOS[i]
        depois(t, () => (digitadas = i + 1))
      }
      depois(t + 120, () => (digitando = false))
      depois(t + 900, () => (cursorFora = true))
      depois(t + 1100, voar)
    })
    return () => esperas.forEach(clearTimeout)
  })
</script>

{#snippet cursor()}<span class="cursor" class:digitando class:fora={cursorFora}></span>{/snippet}

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div class="abertura" bind:this={raiz} onclick={terminar} aria-hidden="true">
  <div class="fundo" bind:this={fundo}></div>
  <div class="linha">
    <span class="palavra" bind:this={texto}
      >{#each PALAVRA as letra, i}{#if i === digitadas}{@render cursor()}{/if}<span class="letra" class:visivel={i < digitadas}>{letra}</span>{/each}{#if digitadas === PALAVRA.length}{@render cursor()}{/if}</span
    >
  </div>
</div>

<style>
  .abertura { position: fixed; inset: 0; z-index: 100; cursor: pointer; }
  .fundo { position: absolute; inset: 0; background: var(--fundo); }
  .linha { position: absolute; left: 50%; top: 46%; transform: translate(-50%, -50%); }
  .palavra {
    display: inline-block; transform-origin: left center; white-space: nowrap;
    font-family: var(--fonte-titulo); font-weight: 600; letter-spacing: 0.28em; line-height: 1;
    font-size: clamp(3.2rem, 12vw, 8.5rem); color: var(--texto);
  }
  :global(:root[data-tema^='editorial']) .palavra { font-weight: 500; }

  /* A palavra inteira já ocupa o lugar (fica centrada desde o início); cada tecla só revela a sua letra */
  .letra { display: inline-block; opacity: 0; }
  .letra.visivel { opacity: 1; animation: tecla 160ms ease-out; }
  @keyframes tecla { from { opacity: 0.2; transform: translateY(0.04em); } }

  /* O cursor fica logo depois da última letra digitada: pisca parado, fica firme enquanto digita e some antes do voo */
  .cursor { display: inline-block; position: relative; width: 0; height: 1em; vertical-align: top; }
  .cursor::after {
    content: ''; position: absolute; left: -0.06em; top: 0.02em; width: 0.08em; height: 0.96em;
    background: var(--destaque); border-radius: 1px; animation: piscar 1s steps(1) infinite;
  }
  .cursor.digitando::after { animation: none; }
  .cursor.fora::after { opacity: 0; animation: none; transition: opacity 200ms ease; }
  @keyframes piscar { 50% { opacity: 0; } }
</style>
