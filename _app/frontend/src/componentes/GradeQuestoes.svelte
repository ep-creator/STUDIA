<script lang="ts">
  import { tick } from 'svelte'
  import type { ListaComQuestoes, Questao } from '../api/tipos'
  import { SIMBOLO, type Marca } from '../estado/marcacoes.svelte'
  import { recolhidos } from '../estado/recolhidos.svelte'

  let { listas, marcacoes, selecionada, onmarcar, onselecionar }: {
    listas: ListaComQuestoes[]
    marcacoes: Record<string, string>
    selecionada: number | null
    onmarcar: (questaoId: number, marca: Marca) => void
    onselecionar: (questaoId: number) => void
  } = $props()

  const TECLAS: Record<string, Marca> = { '1': 'ok', '2': 'err', '3': 'dub', '0': null, Backspace: null }

  // cada assunto (lista) abre e fecha pela setinha; as setas do teclado só andam pelos abertos
  const grupos = recolhidos('studia.listas.fechadas')
  const todas = $derived(listas.filter((l) => grupos.aberto(String(l.id))).flatMap((l) => l.questoes))
  let focada = $state<number | null>(null)
  let botoes: Record<number, HTMLButtonElement> = {}

  const marca = (q: Questao) => (marcacoes[String(q.id)] as Marca) ?? null

  function linhas(l: ListaComQuestoes): [string | null, Questao[]][] {
    const temLinha2 = l.questoes.some((q) => q.linha === 2)
    if (!temLinha2) return [[null, l.questoes]]
    return [['Linha 1', l.questoes.filter((q) => q.linha !== 2)], ['Linha 2', l.questoes.filter((q) => q.linha === 2)]]
  }

  // quantas questões da lista já foram feitas (com qualquer marca), no estilo 2/15
  function feitas(l: ListaComQuestoes): number {
    return l.questoes.filter((q) => marcacoes[String(q.id)]).length
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
    {@const aberto = grupos.aberto(String(l.id))}
    <section class="lista">
      <header>
        <button class="assunto" aria-expanded={aberto} onclick={() => grupos.alternar(String(l.id))}>
          <svg class="seta" class:aberto viewBox="0 0 12 12" aria-hidden="true"><path d="M4.5 3 7.5 6 4.5 9" /></svg>
          <h3>{l.titulo}</h3>
        </button>
        <span class="placar" title={`${feitas(l)} de ${l.questoes.length} questões feitas`}>{feitas(l)}/{l.questoes.length}</span>
      </header>
      {#if aberto}
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
            >{q.rotulo}</button>
          {/each}
        </div>
      {/each}
      {/if}
    </section>
  {/each}
</div>

<style>
  .grade { display: grid; gap: 1rem; }
  header { display: flex; align-items: center; gap: 0.4rem 1rem; flex-wrap: wrap; }
  .assunto { display: flex; align-items: center; gap: 0.45rem; background: none; border: 0; padding: 0.15rem 0; cursor: pointer; text-align: left; }
  .assunto:hover h3, .assunto:hover .seta { color: var(--destaque); }
  .seta { width: 0.8rem; height: 0.8rem; flex: none; fill: none; stroke: currentColor; stroke-width: 1.6; color: var(--suave); transition: transform var(--transicao), color var(--transicao); }
  .seta.aberto { transform: rotate(90deg); }
  h3 { transition: color var(--transicao); }
  .placar { font-size: 0.85rem; color: var(--suave); font-variant-numeric: tabular-nums; }
  h3 { font-size: 1.05rem; margin: 0; }
  .rotulo { margin: 0.4rem 0 0.2rem; }
  /* Número solto: a marca aparece pela cor e por um traço embaixo; a questão aberta fica em negrito */
  .questoes { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; margin-top: 0.3rem; }
  .questao { min-width: 1.6rem; padding: 0 2px; background: none; border: 0; border-bottom: 2px solid transparent; font: inherit; font-size: 1rem; font-variant-numeric: tabular-nums; color: var(--suave); cursor: pointer; }
  .questao:hover { color: var(--destaque); }
  .questao.ok { color: var(--ok); border-bottom-color: var(--ok); }
  .questao.err { color: var(--err); border-bottom-color: var(--err); }
  .questao.dub { color: var(--dub); border-bottom-color: var(--dub); }
  .questao.selecionada { color: var(--texto); font-weight: 600; }
  .questao { outline: 2px solid transparent; outline-offset: 2px; }
</style>
