<script lang="ts">
  import { requisitar } from '../api/cliente'
  import type { DocumentoComCorpo, FonteResumo, Painel } from '../api/tipos'
  import EditorMarkdown from '../componentes/EditorMarkdown.svelte'
  import ListaDocumentos, { type Selecao } from '../componentes/ListaDocumentos.svelte'
  import Markdown from '../componentes/Markdown.svelte'
  import VisualizadorPdf from '../componentes/VisualizadorPdf.svelte'
  import { criarDocumento } from '../documentos'
  import { avisar, erro } from '../estado/avisos.svelte'
  import { recarregar } from '../estado/materia.svelte'
  import { podeSair } from '../estado/saida'

  let { painel }: { painel: Painel } = $props()

  const uid = $derived(painel.materia.uid)
  const unidade = $derived(painel.unidades.find((u) => u.numero === painel.unidade)!)

  let fontes = $state<FonteResumo[]>([])
  let selecao = $state<Selecao>(null)
  let documento = $state<DocumentoComCorpo | null>(null)
  let editando = $state(false)
  let criando = $state(false)
  let novoTitulo = $state('')
  let novoTipo = $state('resumo')

  $effect(() => {
    requisitar<FonteResumo[]>('GET', `/api/materias/${uid}/fontes`).then((f) => (fontes = f), erro)
  })

  async function abrirDocumento(id: number) {
    try {
      documento = await requisitar<DocumentoComCorpo>('GET', `/api/materias/${uid}/documentos/${id}`)
    } catch (e) {
      erro(e)
    }
  }

  function selecionar(s: Selecao) {
    if (!podeSair()) return
    selecao = s
    editando = false
    documento = null
    if (s?.tipo === 'documento') void abrirDocumento(s.id)
  }

  async function criar(e: SubmitEvent) {
    e.preventDefault()
    try {
      const id = await criarDocumento(uid, { tipo: novoTipo, titulo: novoTitulo, unidade_id: unidade.id })
      criando = false
      novoTitulo = ''
      await recarregar()
      selecionar({ tipo: 'documento', id })
      editando = true
    } catch (err) {
      erro(err)
    }
  }

  async function aoSalvar() {
    avisar('Documento salvo')
    editando = false
    await recarregar()
    if (selecao?.tipo === 'documento') await abrirDocumento(selecao.id)
  }

  const fonte = $derived(selecao?.tipo === 'fonte' ? fontes.find((f) => f.id === selecao!.id) ?? null : null)
</script>

<div class="documentos">
  <aside>
    <button class="botao" onclick={() => (criando = !criando)}>＋ Novo documento</button>
    {#if criando}
      <form class="novo" onsubmit={criar}>
        <input aria-label="Título do documento" placeholder="Título" bind:value={novoTitulo} required />
        <select aria-label="Tipo do documento" bind:value={novoTipo}>
          <option value="resumo">Resumo</option><option value="anotacao">Anotação</option>
          <option value="resolucao">Resolução</option><option value="plano">Plano</option>
        </select>
        <button class="botao primario" type="submit" disabled={!novoTitulo.trim()}>Criar</button>
      </form>
    {/if}
    <ListaDocumentos documentos={painel.documentos} {fontes} {selecao} onselecionar={selecionar} />
  </aside>

  <section class="leitor">
    {#if documento}
      <header>
        <h2>{documento.titulo}</h2>
        {#if !editando}<button class="botao" onclick={() => (editando = true)}>✎ Editar</button>{/if}
      </header>
      {#if editando}
        {#key documento.versao}
          <EditorMarkdown {uid} {documento} onsalvo={aoSalvar} oncancelar={() => { if (podeSair()) editando = false }} />
        {/key}
      {:else}
        <Markdown texto={documento.corpo} />
      {/if}
    {:else if fonte}
      <h2>{fonte.titulo || fonte.caminho.split('/').pop()}</h2>
      <VisualizadorPdf {uid} {fonte} />
    {:else}
      <p class="suave">Escolha um resumo, anotação, livro ou PDF à esquerda.</p>
    {/if}
  </section>
</div>

<style>
  .documentos { display: grid; grid-template-columns: 16rem minmax(0, 1fr); gap: 1.5rem; align-items: start; }
  aside { display: grid; gap: 0.5rem; position: sticky; top: 1rem; }
  .novo { display: grid; gap: 0.4rem; }
  .novo input, .novo select { border: 1px solid var(--borda); border-radius: 6px; padding: 0.25rem 0.4rem; background: var(--fundo); }
  header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
</style>
