<script lang="ts">
  // Busca na matéria (Ctrl K): procura em livros, listas e textos e abre o resultado no lugar certo
  // (PDF na página; texto no bloco ## que casou). Teclado: setas andam, Enter abre, Esc fecha.
  import { onDestroy, tick, untrack } from 'svelte'
  import { requisitar } from '../api/cliente'
  import type { ExercicioLivro, ResultadoBusca } from '../api/tipos'
  import { slugTitulo } from '../markdown'
  import { pedido } from '../estado/pedido.svelte'
  import { montarHash } from '../rotas/rota'

  let { uid, unidade, aberta, onfechar }: { uid: string; unidade: number | null; aberta: boolean; onfechar: () => void } = $props()

  type Resultado = ResultadoBusca['resultados'][number]
  type Filtro = 'tudo' | 'livros' | 'listas' | 'textos'

  const TIPOS: Record<Exclude<Filtro, 'tudo'>, string[]> = {
    livros: ['livro', 'gabarito'],
    listas: ['lista', 'prova', 'slides'],
    textos: ['resumo', 'resolucao', 'anotacao', 'plano', 'contexto'],
  }
  const GRUPOS: [Exclude<Filtro, 'tudo'> | 'outros', string][] = [['livros', 'Livros'], ['listas', 'Listas e provas'], ['textos', 'Textos'], ['outros', 'Outros']]
  const FILTROS: [Filtro, string][] = [['tudo', 'Tudo'], ['livros', 'Livros'], ['listas', 'Listas e provas'], ['textos', 'Textos']]
  // palavras que sozinhas não fazem uma busca (o motor também as ignora)
  const VAZIAS = new Set(['de', 'da', 'do', 'das', 'dos', 'a', 'o', 'as', 'os', 'e', 'em', 'no', 'na', 'um', 'uma', 'para', 'com', 'que', 'por', 'se'])

  let consulta = $state('')
  let escopo = $state<'unidade' | 'materia'>('unidade')
  let filtro = $state<Filtro>('tudo')
  let resultados = $state<Resultado[]>([])
  let exercicios = $state<ExercicioLivro[]>([]) // exercícios do livro, à parte da teoria, com a resposta do gabarito
  let montando = $state(false)
  let buscou = $state(false)
  let ativo = $state(0)
  let campo = $state<HTMLInputElement>()
  let espera: ReturnType<typeof setTimeout> | undefined

  const valeBuscar = (q: string) =>
    q.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().split(/[^a-z0-9]+/).some((p) => p.length >= 2 && !VAZIAS.has(p))

  const grupoDe = (r: Resultado) => (Object.keys(TIPOS) as (keyof typeof TIPOS)[]).find((g) => TIPOS[g].includes(r.tipo)) ?? 'outros'
  const agrupados = $derived(
    [
      ...GRUPOS.map(([g, nome]) => ({ nome, itens: resultados.filter((r) => grupoDe(r) === g) })),
      { nome: 'Exercícios do livro', itens: exercicios.map((e) => e.exercicio) },
    ].filter((g) => g.itens.length),
  )
  const respostaDe = $derived(new Map(exercicios.map((e) => [e.exercicio.trecho_id, e.resposta])))
  const ordem = $derived(agrupados.flatMap((g) => g.itens))

  async function buscar() {
    const q = consulta.trim()
    if (!valeBuscar(q)) {
      resultados = []
      exercicios = []
      buscou = false
      return
    }
    const params = new URLSearchParams({ q, limite: '20' })
    if (escopo === 'unidade' && unidade !== null) params.set('unidade', String(unidade))
    if (filtro !== 'tudo') for (const t of TIPOS[filtro]) params.append('tipo', t)
    try {
      const r = await requisitar<ResultadoBusca>('GET', `/api/materias/${uid}/busca?${params}`)
      if (q !== consulta.trim()) return // chegou depois de outra digitação
      resultados = r.resultados
      exercicios = r.exercicios ?? []
      montando = (r.sincronizacao.avisos ?? []).some((a) => a.includes('andamento'))
      buscou = true
      ativo = 0
    } catch {
      resultados = []
      exercicios = []
      buscou = true
    }
  }

  function agendar() {
    clearTimeout(espera)
    espera = setTimeout(() => void buscar(), 200)
  }

  // trocar o escopo ou o tipo refaz a busca na hora; digitar espera 200 ms (agendar)
  $effect(() => {
    void escopo
    void filtro
    untrack(() => {
      if (consulta.trim()) void buscar()
    })
  })
  onDestroy(() => clearTimeout(espera))

  $effect(() => {
    if (aberta) void tick().then(() => campo?.focus())
  })

  /** "15.4 Integrais — Mudança para polares" → âncora do bloco ## (o texto antes do " — " é o título do documento). */
  function ancoraDe(titulo: string): string | null {
    const i = titulo.lastIndexOf(' — ')
    return i >= 0 ? slugTitulo(titulo.slice(i + 3)) : null
  }

  function abrir(r: Resultado) {
    if (r.fonte_id !== null) {
      pedido.fonte = { id: r.fonte_id, pagina: r.pagina }
    } else if (r.documento_id !== null) {
      pedido.documento = r.documento_id
      pedido.ancora = ancoraDe(r.titulo)
    }
    location.hash = montarHash({ tela: 'materia', uid, unidade, area: 'documentos' })
    onfechar()
  }

  function teclar(e: KeyboardEvent) {
    if (e.key === 'Escape') { e.preventDefault(); onfechar() }
    else if (e.key === 'ArrowDown') { e.preventDefault(); ativo = Math.min(ativo + 1, ordem.length - 1) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); ativo = Math.max(ativo - 1, 0) }
    else if (e.key === 'Enter' && ordem[ativo]) { e.preventDefault(); abrir(ordem[ativo]) }
  }

  // o trecho do FTS marca as palavras com [ ]; o resto é escapado antes de virar <mark>
  function destacar(texto: string): string {
    const seguro = texto.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    return seguro.replace(/\[([^\]]*)\]/g, '<mark>$1</mark>')
  }
</script>

<svelte:window onkeydown={(e) => aberta && teclar(e)} />

{#if aberta}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="fundo" onclick={onfechar}></div>
  <div class="busca" role="dialog" aria-modal="true" aria-label="Buscar na matéria">
    <input
      bind:this={campo}
      bind:value={consulta}
      oninput={agendar}
      role="combobox"
      aria-expanded={ordem.length > 0}
      aria-controls="busca-resultados"
      aria-label="Buscar na matéria"
      placeholder="Buscar na matéria…"
      autocomplete="off"
    />
    <div class="filtros">
      <div role="radiogroup" aria-label="Onde buscar">
        {#each [['unidade', 'Esta unidade'], ['materia', 'Toda a matéria']] as [valor, nome] (valor)}
          <button role="radio" aria-checked={escopo === valor} class:ativo={escopo === valor} onclick={() => (escopo = valor as 'unidade' | 'materia')}>{nome}</button>
        {/each}
      </div>
      <div role="radiogroup" aria-label="Tipo">
        {#each FILTROS as [valor, nome] (valor)}
          <button role="radio" aria-checked={filtro === valor} class:ativo={filtro === valor} onclick={() => (filtro = valor)}>{nome}</button>
        {/each}
      </div>
    </div>

    {#if montando}<p class="aviso">Montando o índice… os resultados podem ainda não incluir tudo.</p>{/if}

    <div class="resultados" id="busca-resultados" role="listbox" aria-label="Resultados">
      {#each agrupados as g (g.nome)}
        <div class="grupo rotulo">{g.nome}</div>
        {#each g.itens as r (r.trecho_id)}
          {@const i = ordem.indexOf(r)}
          <div
            class="item"
            class:ativo={i === ativo}
            role="option"
            tabindex="-1"
            aria-selected={i === ativo}
            onmouseenter={() => (ativo = i)}
            onclick={() => abrir(r)}
            onkeydown={teclar}
          >
            <div class="titulo">
              {r.titulo}{#if r.pagina}<span class="suave"> · p. {r.pagina}</span>{/if}
              {#if r.por === 'sentido'}<span class="sentido" title="Achado pelo sentido, sem palavras em comum com a busca">pelo sentido</span>{/if}
            </div>
            <div class="trecho">{@html destacar(r.trecho)}</div>
            {#if respostaDe.get(r.trecho_id)}<div class="resposta"><strong>Resposta:</strong> {respostaDe.get(r.trecho_id)?.trecho}</div>{/if}
          </div>
        {/each}
      {/each}
      {#if buscou && ordem.length === 0}
        <div class="vazio">
          <p class="suave">Nada encontrado {escopo === 'unidade' ? 'nesta unidade' : 'na matéria'}.</p>
          {#if escopo === 'unidade'}<button class="acao-texto" onclick={() => (escopo = 'materia')}>Buscar na matéria toda</button>{/if}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .fundo { position: fixed; inset: 0; z-index: 60; background: rgb(0 0 0 / 35%); }
  .busca {
    position: fixed; z-index: 61; top: 12vh; left: 50%; transform: translateX(-50%); width: min(44rem, calc(100vw - 2rem));
    max-height: 72vh; display: flex; flex-direction: column; background: var(--cartao); color: var(--texto);
    border: 1px solid color-mix(in srgb, var(--borda) 60%, transparent); border-radius: var(--raio);
    box-shadow: 0 24px 60px rgb(0 0 0 / 35%); animation: surgir 140ms ease-out; overflow: hidden;
  }
  input { border: 0; border-bottom: 1px solid color-mix(in srgb, var(--borda) 50%, transparent); background: transparent; padding: 0.9rem 1.1rem; font-size: 1.1rem; outline: none; }
  .filtros { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.5rem; padding: 0.55rem 1rem; border-bottom: 1px solid color-mix(in srgb, var(--borda) 30%, transparent); }
  .filtros div { display: flex; gap: 0.25rem; }
  .filtros button { background: none; border: 1px solid transparent; border-radius: 999px; padding: 0.1rem 0.6rem; font-size: 0.82rem; color: var(--suave); cursor: pointer; }
  .filtros button:hover { color: var(--destaque); }
  .filtros button.ativo { border-color: var(--destaque); color: var(--destaque); }
  .aviso { margin: 0; padding: 0.5rem 1.1rem; font-size: 0.85rem; color: var(--destaque); }
  .resultados { overflow-y: auto; padding: 0.3rem 0.5rem 0.7rem; }
  .grupo { margin: 0.6rem 0.6rem 0.2rem; }
  .item { padding: 0.45rem 0.6rem; border-radius: 6px; cursor: pointer; border-left: 2px solid transparent; }
  .item.ativo { background: var(--realce); border-left-color: var(--destaque); }
  .titulo { font-weight: 600; font-size: 0.95rem; }
  .sentido {
    margin-left: 0.4rem; padding: 0 0.35rem; border-radius: 4px; vertical-align: 0.1em; font-size: 0.66rem; font-weight: 600;
    letter-spacing: 0.04em; color: var(--destaque); border: 1px solid color-mix(in srgb, var(--destaque) 50%, transparent);
  }
  .item.ativo .titulo { color: var(--destaque); }
  .resposta { font-size: 0.82rem; margin-top: 0.2rem; color: var(--texto); }
  .trecho { font-size: 0.85rem; color: var(--suave); margin-top: 0.15rem; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .trecho :global(mark) { background: none; color: var(--texto); font-weight: 600; }
  .vazio { padding: 0.8rem 0.6rem; display: grid; gap: 0.5rem; justify-items: start; }
  .vazio p { margin: 0; }
  @keyframes surgir { from { opacity: 0; transform: translate(-50%, -6px); } }
</style>
