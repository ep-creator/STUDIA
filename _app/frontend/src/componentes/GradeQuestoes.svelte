<script lang="ts">
  import { tick } from 'svelte'
  import type { ListaComQuestoes, Questao } from '../api/tipos'
  import { SIMBOLO, type Marca } from '../estado/marcacoes.svelte'

  let { listas, marcacoes, selecionada, onmarcar, onselecionar }: {
    listas: ListaComQuestoes[]
    marcacoes: Record<string, string>
    selecionada: number | null
    onmarcar: (questaoId: number, marca: Marca) => void
    onselecionar: (questaoId: number) => void
  } = $props()

  const TECLAS: Record<string, Marca> = { '1': 'ok', '2': 'err', '3': 'dub', '0': null, Backspace: null }

  const todas = $derived(listas.flatMap((l) => l.questoes))
  let focada = $state<number | null>(null)
  let botoes: Record<number, HTMLButtonElement> = {}

  const marca = (q: Questao) => (marcacoes[String(q.id)] as Marca) ?? null

  function linhas(l: ListaComQuestoes): [string | null, Questao[]][] {
    const temLinha2 = l.questoes.some((q) => q.linha === 2)
    if (!temLinha2) return [[null, l.questoes]]
    return [['Linha 1', l.questoes.filter((q) => q.linha !== 2)], ['Linha 2', l.questoes.filter((q) => q.linha === 2)]]
  }

  function placar(l: ListaComQuestoes): string {
    const conta = (m: string) => l.questoes.filter((q) => marcacoes[String(q.id)] === m).length
    const feitas = l.questoes.filter((q) => marcacoes[String(q.id)]).length
    return `${conta('ok')} ✓ · ${conta('err')} ✗ · ${conta('dub')} ? · ${l.questoes.length - feitas} por fazer`
  }

  // Clicar só abre a questão no menu ao lado (marcar é lá, ou pelas teclas 1/2/3/0).
  // O contorno laranja só confirma o clique: aparece e some sozinho, a cada clique (o foco do teclado continua visível)
  function confirmar(id: number) {
    const el = botoes[id]
    const cor = el && getComputedStyle(el).getPropertyValue('--destaque').trim()
    el?.animate?.([{ outlineColor: cor }, { outlineColor: cor, offset: 0.35 }, { outlineColor: 'transparent' }], { duration: 1100, easing: 'ease-out' })
  }

  function clicar(q: Questao) {
    confirmar(q.id)
    focada = q.id
    onselecionar(q.id)
  }

  async function mover(delta: number) {
    const i = todas.findIndex((q) => q.id === focada)
    const alvo = todas[Math.min(Math.max(i + delta, 0), todas.length - 1)]
    if (!alvo) return
    focada = alvo.id
    onselecionar(alvo.id)
    await tick()
    botoes[alvo.id]?.focus()
  }

  function teclar(e: KeyboardEvent, q: Questao) {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); void mover(1) }
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); void mover(-1) }
    else if (e.key in TECLAS) { e.preventDefault(); onmarcar(q.id, TECLAS[e.key]) }
  }
</script>

<div class="grade">
  {#each listas as l (l.id)}
    <section class="lista">
      <header>
        <h3>{l.titulo}</h3>
        <span class="suave">{placar(l)}</span>
      </header>
      {#each linhas(l) as [titulo, questoes] (titulo)}
        {#if titulo}<div class="rotulo">{titulo}</div>{/if}
        <div class="questoes">
          {#each questoes as q (q.id)}
            {@const m = marca(q)}
            <button
              bind:this={botoes[q.id]}
              class="questao {m ?? ''}"
              class:selecionada={selecionada === q.id}
              tabindex={(focada ?? todas[0]?.id) === q.id ? 0 : -1}
              aria-label={`Questão ${l.codigo} #${q.rotulo}${m ? ` (${SIMBOLO[m]})` : ''}`}
              aria-pressed={selecionada === q.id}
              onclick={() => clicar(q)}
              onkeydown={(e) => teclar(e, q)}
              onfocus={() => (focada = q.id)}
            >{q.rotulo}{#if m}<span aria-hidden="true"> {SIMBOLO[m]}</span>{/if}</button>
          {/each}
        </div>
      {/each}
    </section>
  {/each}
</div>

<style>
  .grade { display: grid; gap: 1.25rem; }
  header { display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; }
  h3 { font-size: 1.05rem; margin: 0; }
  .rotulo { margin: 0.4rem 0 0.2rem; }
  .questoes { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.3rem; }
  .questao { min-width: 2.6rem; padding: 0.2rem 0.55rem; border: 1.5px solid var(--borda); border-radius: 6px; background: var(--cartao); cursor: pointer; }
  .questao:hover { transform: translateY(-1px); box-shadow: 0 3px 10px rgb(0 0 0 / 14%); }
  .questao:not(.ok, .err, .dub):hover { border-color: var(--destaque); color: var(--destaque); }
  .questao.ok { background: var(--ok); border-color: var(--ok); color: #fff; }
  .questao.err { background: var(--err); border-color: var(--err); color: #fff; }
  .questao.dub { background: var(--dub); border-color: var(--dub); color: #000; }
  .questao { outline: 2px solid transparent; outline-offset: 2px; }
</style>
