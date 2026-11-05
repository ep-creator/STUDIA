<script lang="ts">
  // A IA da matéria numa gaveta por cima da página: a página não muda de largura, um véu escurece o resto.
  // Diz no topo sobre o que está conversando (a matéria inteira, ou a seção pedida em Biblioteca); embaixo, a chave.
  // A ajuda de uma questão fica na própria questão, em Praticar.
  // Esc, o ✕ ou clicar no véu fecham; o foco vai para o campo ao abrir, fica preso na gaveta e volta a quem abriu.
  import { tick } from 'svelte'
  import { atalhosDoPapel, ia } from '../estado/ia.svelte'
  import ChaveAgente from './ChaveAgente.svelte'
  import PainelIA from './PainelIA.svelte'

  let { uid, onfechar }: { uid: string; onfechar: () => void } = $props()

  let gaveta: HTMLElement
  const alvo = $derived(ia.alvo ?? 'geral')
  const papel = $derived(ia.papel ?? 'estrategista')

  $effect(() => {
    const anterior = document.activeElement as HTMLElement | null
    void tick().then(() => gaveta.querySelector<HTMLTextAreaElement>('textarea')?.focus())
    return () => anterior?.focus()
  })

  const focaveis = () => [...gaveta.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), textarea, input')]

  function tecla(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault()
      onfechar()
    } else if (e.key === 'Tab') {
      const lista = focaveis()
      if (!lista.length) return
      const i = lista.indexOf(document.activeElement as HTMLElement)
      const proximo = e.shiftKey ? (i <= 0 ? lista.length - 1 : i - 1) : (i === lista.length - 1 ? 0 : i + 1)
      e.preventDefault()
      lista[proximo].focus()
    }
  }

  const sobre = $derived(
    alvo.startsWith('secao:') ? 'resumos da seção pedida' : alvo.startsWith('questao:') ? 'a questão pedida' : 'plano e dúvidas da matéria',
  )
</script>

<button class="veu" aria-label="Fechar a IA" tabindex="-1" onclick={onfechar}></button>
<div bind:this={gaveta} class="gaveta nao-imprimir" role="dialog" aria-label="IA da matéria" aria-modal="true" tabindex="-1" onkeydown={tecla}>
  <header>
    <div class="titulo"><b>IA da matéria</b><span class="suave sobre">{sobre}</span></div>
    <button class="acao-texto" aria-label="Fechar" onclick={onfechar}>✕</button>
  </header>
  {#key `${alvo}|${papel}`}
    <PainelIA {uid} {alvo} {papel} atalhos={atalhosDoPapel(papel)} />
  {/key}
  <div class="chave"><ChaveAgente /></div>
</div>

<style>
  .veu { position: fixed; inset: 0; z-index: 40; border: 0; padding: 0; background: rgb(10 9 8 / 45%); cursor: default; }
  .gaveta {
    position: fixed; top: 0; right: 0; bottom: 0; z-index: 41; width: min(24rem, 100vw); box-sizing: border-box;
    display: flex; flex-direction: column; gap: 0.9rem; padding: 1.1rem 1.2rem; overflow-y: auto;
    background: var(--lateral); border-left: 1px solid var(--fio); box-shadow: -18px 0 40px rgb(0 0 0 / 35%);
  }
  .gaveta:focus { outline: none; }
  header { display: flex; align-items: baseline; gap: 1rem; }
  .titulo { display: grid; gap: 0.1rem; margin-right: auto; }
  .titulo b { font-family: var(--fonte-titulo); font-weight: 500; font-size: 1.1rem; }
  .sobre { font-size: 0.85rem; }
  header .acao-texto { font-size: 0.85rem; }
  .chave { margin-top: auto; padding-top: 0.8rem; border-top: 1px solid var(--fio); }
</style>
