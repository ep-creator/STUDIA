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
  // ritmo de quem digita com calma: teclas desiguais e uma hesitação no meio da palavra (antes do D)
  const INTERVALOS = [360, 250, 300, 470, 240, 330]

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
      let t = 1050 // o cursor pisca um pouco antes da primeira tecla
      depois(t, () => (digitando = true))
      for (let i = 0; i < PALAVRA.length; i++) {
        t += INTERVALOS[i]
        depois(t, () => (digitadas = i + 1))
      }
      depois(t + 150, () => (digitando = false))
      depois(t + 1150, () => (cursorFora = true))
      depois(t + 1350, voar)
    })
    return () => esperas.forEach(clearTimeout)
  })
</script>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div class="abertura" bind:this={raiz} onclick={terminar} aria-hidden="true">
  <div class="fundo" bind:this={fundo}></div>
  <div class="linha">
    <span class="palavra" class:digitando class:cursor-fora={cursorFora} bind:this={texto}
      >{#each PALAVRA as letra, i}<span class="letra" class:visivel={i < digitadas} class:proxima={i === digitadas}>{letra}</span>{/each}<span
        class="fim" class:proxima={digitadas === PALAVRA.length}></span></span
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
  .palavra { font-weight: 500; }

  /* A palavra inteira já ocupa o lugar (fica centrada desde o início); cada tecla só revela a sua letra */
  .letra { display: inline-block; color: transparent; }
  .letra { position: relative; }
  .letra.visivel { color: inherit; animation: tecla 220ms ease-out; }
  @keyframes tecla { from { opacity: 0.2; transform: translateY(0.04em); } }

  /* O cursor é um sublinhado no chão da próxima letra (ou logo depois da última): pisca parado,
     fica firme enquanto digita e some antes do voo. O espaçamento entre letras fica de fora da largura. */
  .fim { display: inline-block; position: relative; width: 0; height: 1em; vertical-align: top; }
  .proxima::after {
    content: ''; position: absolute; left: 0; right: 0.28em; bottom: 0.04em; height: 0.07em; opacity: 1;
    background: var(--destaque); border-radius: 1px; animation: piscar 1.05s steps(1) infinite;
  }
  .letra.proxima::after { right: 0.28em; }
  .fim.proxima::after { right: auto; width: 0.62em; }
  .digitando .proxima::after { animation: none; }
  .cursor-fora .proxima::after { opacity: 0; animation: none; transition: opacity 250ms ease; }
  @keyframes piscar { 50% { opacity: 0; } }
</style>
