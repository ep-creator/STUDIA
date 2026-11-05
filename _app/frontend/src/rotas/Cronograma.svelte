<script lang="ts">
  import { requisitar } from '../api/cliente'
  import type { Painel, Sessao, SessaoProgresso } from '../api/tipos'
  import { nomeUnidade } from '../apresentacao'
  import EditorSessao from '../componentes/EditorSessao.svelte'
  import LinhaDoTempo from '../componentes/LinhaDoTempo.svelte'
  import { montarLinhaDoTempo } from '../cronograma'
  import { erro } from '../estado/avisos.svelte'
  import { recarregar } from '../estado/materia.svelte'

  let { painel }: { painel: Painel } = $props()

  let editando = $state<Partial<Sessao> | null>(null)
  const unidade = $derived(painel.unidades.find((u) => u.numero === painel.unidade)!)
  const base = $derived(`/api/materias/${painel.materia.uid}/sessoes`)
  const itens = $derived(montarLinhaDoTempo(painel.sessoes, painel.eventos))

  // o estado de cada sessão vem derivado do motor (questões marcadas ou resolvidas), igual à tela Hoje
  let progresso = $state<Record<number, SessaoProgresso>>({})
  $effect(() => {
    void painel
    requisitar<SessaoProgresso[]>('GET', `/api/materias/${painel.materia.uid}/sessoes/progresso?unidade=${unidade.numero}`).then(
      (lista) => (progresso = Object.fromEntries(lista.map((s) => [s.id, s]))),
      () => (progresso = {}),
    )
  })

  async function executar(acao: () => Promise<unknown>) {
    try {
      await acao()
      await recarregar()
    } catch (e) {
      erro(e)
    }
  }

  function salvar(dados: { codigo: string; data: string | null; foco_md: string }) {
    const atual = editando
    void executar(async () => {
      if (atual?.id) await requisitar('PATCH', `${base}/${atual.id}`, dados)
      else await requisitar('POST', base, { unidade_id: unidade.id, ...dados })
      editando = null
    })
  }
</script>

<header class="cabecalho">
  <h1>Plano da {nomeUnidade(unidade.numero)}</h1>
  <button class="acao-texto" onclick={() => (editando = {})}>+ sessão</button>
</header>

{#if editando}
  {#key editando}
    <EditorSessao sessao={editando} onsalvar={salvar} oncancelar={() => (editando = null)} />
  {/key}
{/if}

{#if itens.length === 0}
  <p class="suave">Nada no cronograma ainda.</p>
{:else}
  <LinhaDoTempo
    {itens}
    {progresso}
    onfeito={(s) => void executar(() => requisitar('PATCH', `${base}/${s.id}`, { feito: !s.feito }))}
    oneditar={(s) => (editando = s)}
  />
{/if}

<style>
  .cabecalho { display: flex; align-items: baseline; gap: 1.2rem; }
  h1 { font-size: 2.2rem; margin: 0 0 0.6rem; }
</style>
