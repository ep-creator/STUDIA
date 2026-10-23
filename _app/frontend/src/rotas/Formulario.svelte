<script lang="ts">
  import { requisitar } from '../api/cliente'
  import type { Formula, Painel } from '../api/tipos'
  import { nomeUnidade } from '../apresentacao'
  import CartaoFormula from '../componentes/CartaoFormula.svelte'
  import EditorFormula from '../componentes/EditorFormula.svelte'
  import { agruparFormulas } from '../cronograma'
  import { erro } from '../estado/avisos.svelte'
  import { recarregar } from '../estado/materia.svelte'

  let { painel }: { painel: Painel } = $props()

  let editando = $state<Partial<Formula> | null>(null)
  const unidade = $derived(painel.unidades.find((u) => u.numero === painel.unidade)!)
  const base = $derived(`/api/materias/${painel.materia.uid}/formulas`)
  const grupos = $derived(agruparFormulas(painel.formulas, painel.topicos, painel.vinculos.topicos))

  async function executar(acao: () => Promise<unknown>) {
    try {
      await acao()
      await recarregar()
    } catch (e) {
      erro(e)
    }
  }

  function salvar(dados: { titulo: string; corpo_tex: string; notas_md: string }) {
    const atual = editando
    void executar(async () => {
      if (atual?.id) await requisitar('PATCH', `${base}/${atual.id}`, dados)
      else await requisitar('POST', base, { unidade_id: unidade.id, ...dados })
      editando = null
    })
  }

  function apagar(f: Formula) {
    if (confirm(`Apagar a fórmula "${f.titulo}"? (dá para desfazer)`)) void executar(() => requisitar('DELETE', `${base}/${f.id}`))
  }
</script>

<header class="cabecalho">
  <h2>Formulário · {nomeUnidade(unidade.numero)}</h2>
  <div class="nao-imprimir">
    <button class="botao" onclick={() => (editando = {})}>＋ Fórmula</button>
    <button class="botao" onclick={() => window.print()} disabled={painel.formulas.length === 0}>🖨 Folha para imprimir</button>
  </div>
</header>

{#if editando}
  {#key editando}
    <EditorFormula formula={editando} onsalvar={salvar} oncancelar={() => (editando = null)} />
  {/key}
{/if}

{#if grupos.length === 0}
  <p class="suave">Nenhuma fórmula nesta unidade. Adicione as essenciais para revisar antes da prova.</p>
{/if}
{#each grupos as [topico, formulas] (topico)}
  <section class="grupo">
    <h3>{topico}</h3>
    {#each formulas as f (f.id)}
      <CartaoFormula formula={f} oneditar={() => (editando = f)} onapagar={() => apagar(f)} />
    {/each}
  </section>
{/each}

<style>
  .cabecalho { display: flex; align-items: center; justify-content: space-between; }
  .cabecalho div { display: flex; gap: 0.5rem; }
  .grupo { margin-top: 1.25rem; }
  @media print {
    .grupo { columns: 2; column-gap: 2rem; }
  }
</style>
