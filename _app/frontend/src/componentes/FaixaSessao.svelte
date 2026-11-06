<script lang="ts">
  // Praticar aberto a partir de uma sessão do plano: a faixa mantém as questões dela à vista, diz quantas faltam e,
  // feitas todas, fecha a sessão com a próxima do plano e o caminho de volta para Hoje.
  import { dataCurta } from '../apresentacao'

  type QuestaoDaSessao = { id: number; rotulo: string; lista_codigo: string; estado: string | null; trabalhada: boolean }
  let { codigo, titulo, questoes, selecionada, proxima = null, hrefSair, hrefHoje, onabrir }: {
    codigo: string
    titulo: string
    questoes: QuestaoDaSessao[]
    selecionada: number | null
    proxima?: { codigo: string; data: string | null; titulo: string } | null
    hrefSair: string
    hrefHoje: string
    onabrir: (id: number) => void
  } = $props()

  const NOME: Record<string, string> = { ok: 'acertei', err: 'errei', dub: 'dúvida' }
  const feitas = $derived(questoes.filter((q) => q.trabalhada).length)
  const completa = $derived(questoes.length > 0 && feitas === questoes.length)
  const grupos = $derived.by(() => {
    const lista: { lista: string; questoes: QuestaoDaSessao[] }[] = []
    for (const q of questoes) {
      const g = lista.at(-1)
      if (g && g.lista === q.lista_codigo) g.questoes.push(q)
      else lista.push({ lista: q.lista_codigo, questoes: [q] })
    }
    return lista
  })
</script>

<section class="faixa" class:completa aria-label={`Sessão ${codigo}`}>
  <span class="nome"><b>{codigo}</b> {titulo}</span>
  <span class="numeros">
    {#each grupos as g, i (i)}
      <span class="grupo">
        <span class="suave lista">{g.lista}</span>
        {#each g.questoes as q (q.id)}
          <button class="numero {q.estado ?? ''}" class:resolvida={q.trabalhada && !q.estado} class:aberta={q.id === selecionada}
            aria-current={q.id === selecionada ? 'true' : undefined}
            aria-label={`${g.lista} #${q.rotulo}${q.estado ? `, ${NOME[q.estado]}` : q.trabalhada ? ', resolvida' : ''}`}
            onclick={() => onabrir(q.id)}>{q.rotulo}</button>
        {/each}
      </span>
    {/each}
  </span>
  <span class="placar" role="status">
    {#if completa}<span class="feita">Sessão feita</span>{:else}{feitas} de {questoes.length}{/if}
  </span>
  <a class="acao-texto sair" href={hrefSair} title="Ver a grade da unidade inteira">sair da sessão</a>
  {#if completa}
    <p class="fecho">
      {#if proxima}Próxima: <b>{proxima.codigo}</b> {proxima.titulo}{proxima.data ? ` · ${dataCurta(proxima.data)}` : ''}.{:else}Era a última sessão do plano.{/if}
      <a class="acao-forte" href={hrefHoje}>Voltar para Hoje</a>
    </p>
  {/if}
</section>

<style>
  .faixa { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.4rem 1.4rem; padding: 0.55rem 0 0.7rem; margin-bottom: 0.9rem; border-bottom: 1px solid var(--fio); }
  .nome { font-family: var(--fonte-titulo); font-size: 1.05rem; }
  .nome b { font-family: var(--fonte-texto); font-weight: 600; font-size: 0.9rem; color: var(--destaque-texto); margin-right: 0.3rem; }
  .numeros { display: inline-flex; flex-wrap: wrap; gap: 0.3rem 1.2rem; }
  .grupo { display: inline-flex; align-items: baseline; gap: 0.15rem 0.6rem; }
  .lista { font-size: 0.85rem; }
  .placar { margin-left: auto; font-size: 0.9rem; font-variant-numeric: tabular-nums; color: var(--suave); }
  .feita { color: var(--ok); font-weight: 500; }
  .sair { font-size: 0.85rem; }
  .fecho { flex-basis: 100%; margin: 0.3rem 0 0; display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.4rem 1.2rem; }
  .fecho .acao-forte { padding: 0.3rem 1rem; }

  /* os números da sessão: o mesmo gesto da grade e da tela Hoje */
  .numero { background: none; border: 0; border-bottom: 2px solid transparent; padding: 0 2px; min-width: 1.4rem; font: inherit; font-variant-numeric: tabular-nums; color: var(--texto); cursor: pointer; }
  .numero:hover { color: var(--destaque-texto); }
  .numero.ok { color: var(--ok); border-bottom-color: var(--ok); }
  .numero.err { color: var(--err); border-bottom: 3px double var(--err); }
  .numero.dub { color: var(--dub-texto); border-bottom: 2px dashed var(--dub); }
  .numero.resolvida:not(.ok):not(.err):not(.dub) { border-bottom: 2px dotted var(--suave); }
  .numero.aberta { font-weight: 700; outline: 1px solid var(--fio); outline-offset: 2px; border-radius: 3px; }
</style>
