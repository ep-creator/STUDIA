<script lang="ts">
  import { requisitar } from '../api/cliente'
  import { tick } from 'svelte'
  import { consumirAncora, consumirDocumento, consumirFonte, pedido } from '../estado/pedido.svelte'
  import type { DocumentoComCorpo, FonteResumo, Painel, SecaoLivro } from '../api/tipos'
  import EditorMarkdown from '../componentes/EditorMarkdown.svelte'
  import ListaDocumentos, { type Selecao } from '../componentes/ListaDocumentos.svelte'
  import Markdown from '../componentes/Markdown.svelte'
  import VisualizadorPdf from '../componentes/VisualizadorPdf.svelte'
  import Seletor from '../componentes/Seletor.svelte'
  import { avisar, erro } from '../estado/avisos.svelte'
  import { recarregar } from '../estado/materia.svelte'
  import { desfazer } from '../estado/desfazer'
  import { podeSair } from '../estado/saida'
  import { abrirNoPainel } from '../estado/ia.svelte'
  import { nomeLegivel, semTituloRepetido } from '../apresentacao'
  import { montarHash } from './rota'

  let { painel, documento: documentoDaRota = null }: { painel: Painel; documento?: number | null } = $props()

  const uid = $derived(painel.materia.uid)

  let fontes = $state<FonteResumo[]>([])
  let selecao = $state<Selecao>(null)
  let documento = $state<DocumentoComCorpo | null>(null)
  let editando = $state(false)
  let leitor = $state<HTMLElement>()

  // abrir outro documento começa do topo dele (o texto rola dentro do leitor, não na página)
  $effect(() => {
    void selecao
    leitor?.scrollTo?.({ top: 0 })
  })

  // Pedidos de outras telas (o painel pede um resumo; a busca pede um PDF na página ou um texto num bloco).
  // Lidos por efeito: chegam também com Documentos já aberto.
  let paginaInicial = $state(1)
  let ancora: string | null = null
  $effect(() => {
    if (pedido.documento !== null) {
      const id = consumirDocumento()!
      ancora = consumirAncora()
      selecionar({ tipo: 'documento', id })
    } else if (pedido.fonte !== null) {
      const f = consumirFonte()!
      paginaInicial = f.pagina ?? 1
      selecionar({ tipo: 'fonte', id: f.id })
    }
  })
  // o texto do endereço (#/…/documentos/<id>): voltar, recarregar e favoritos reabrem o mesmo
  $effect(() => {
    const id = documentoDaRota
    if (id !== null && !(selecao?.tipo === 'documento' && selecao.id === id)) selecionar({ tipo: 'documento', id })
  })
  // e o texto aberto vai para o endereço (sem empilhar no histórico); PDF e nada aberto ficam no endereço da área
  $effect(() => {
    if (painel.unidade === null) return
    const id = selecao?.tipo === 'documento' ? selecao.id : null
    const alvo = montarHash({ tela: 'materia', uid, unidade: painel.unidade, area: 'documentos', documento: id })
    if (location.hash !== alvo) history.replaceState(history.state, '', alvo)
  })

  // com o texto na tela, rola até o bloco pedido
  $effect(() => {
    if (!documento || !ancora) return
    const alvo = ancora
    ancora = null
    void tick().then(() => leitor?.querySelector(`#${CSS.escape(alvo)}`)?.scrollIntoView?.({ block: 'start' }))
  })

  $effect(() => {
    requisitar<FonteResumo[]>('GET', `/api/materias/${uid}/fontes`).then((f) => (fontes = f), erro)
  })

  // Ligação documento ↔ seção do livro: ao abrir a tela, o motor liga os documentos que faltam (só os confiantes).
  // É uma escrita: quando liga algo, diz quantos e deixa desfazer ali mesmo (fica no Histórico como qualquer ação)
  $effect(() => {
    void requisitar<{ ligados: number }>('POST', `/api/materias/${uid}/documentos/ligar-secoes`)
      .then((r) => {
        if (r.ligados === 0) return
        avisar(r.ligados === 1 ? '1 texto ligado à seção do livro' : `${r.ligados} textos ligados às seções do livro`,
          { rotulo: 'Desfazer', executar: () => void desfazer() })
        void recarregar()
      }, () => {})
  })

  // seções de todos os livros, para o seletor "Seção do livro" do cabeçalho
  let secoes = $state<{ secao: SecaoLivro; livro: string }[]>([])
  $effect(() => {
    const livros = fontes.filter((f) => f.tipo === 'livro')
    void Promise.all(livros.map((l) => requisitar<SecaoLivro[]>('GET', `/api/materias/${uid}/fontes/${l.id}/secoes`)
      .then((ss) => ss.map((secao) => ({ secao, livro: nomeLegivel(l) })), () => [])))
      .then((porLivro) => (secoes = porLivro.flat()))
  })
  const opcoesSecao = $derived([
    { valor: '', rotulo: 'Sem seção' },
    ...secoes.map(({ secao, livro }) => ({ valor: String(secao.id), rotulo: `${secao.codigo} ${secao.titulo}`, detalhe: livro })),
  ])
  const TIPOS_COM_SECAO = ['resumo', 'resolucao', 'plano']
  let trocandoSecao = $state(false)
  $effect(() => {
    void documento?.id
    trocandoSecao = false
  })

  // documento ainda sem seção (e sem decisão): mostra a sugestão do motor, que só é gravada com "Sim"
  type Sugestao = { secao_id: number; codigo: string; titulo: string; confianca: number; por: string }
  let sugestao = $state<Sugestao | null>(null)
  let seletorSecao = $state<HTMLElement>()
  $effect(() => {
    const d = documento
    sugestao = null
    if (!d || d.secao_id !== null || d.secao_decidida || !TIPOS_COM_SECAO.includes(d.tipo)) return
    void requisitar<Sugestao | null>('GET', `/api/materias/${uid}/documentos/${d.id}/sugestao-secao`)
      .then((s) => { if (documento?.id === d.id) sugestao = s }, () => {})
  })

  async function escolherSecao(secaoId: number | null) {
    if (!documento) return
    try {
      await requisitar('PUT', `/api/materias/${uid}/documentos/${documento.id}/secao`, { secao_id: secaoId })
      sugestao = null
      await recarregar()
      await abrirDocumento(documento.id)
    } catch (e) {
      erro(e)
    }
  }

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

  async function aoSalvar() {
    avisar('Documento salvo')
    editando = false
    await recarregar()
    if (selecao?.tipo === 'documento') await abrirDocumento(selecao.id)
  }

  const fonte = $derived(selecao?.tipo === 'fonte' ? fontes.find((f) => f.id === selecao!.id) ?? null : null)
</script>

<h1 class="titulo-tela">Biblioteca</h1>
<div class="documentos">
  <aside>
    <ListaDocumentos documentos={painel.documentos} {fontes} {selecao} onselecionar={(s) => { paginaInicial = 1; selecionar(s) }} />
  </aside>

  <section class="leitor" bind:this={leitor}>
    {#if documento}
      <header>
        <h2>{documento.titulo}</h2>
        <div class="acoes">
          {#if documento.secao_id !== null && !editando}
            <button class="acao-suave" onclick={() => abrirNoPainel(`secao:${documento!.secao_id}`, 'resumidor', 'resumir')}>Resumir a seção</button>
          {/if}
          {#if !editando}<button class="acao-texto" onclick={() => (editando = true)}>editar</button>{/if}
        </div>
      </header>
      <!-- editando, não: trocar a seção regrava o .md e recriaria o editor, perdendo o rascunho -->
      {#if TIPOS_COM_SECAO.includes(documento.tipo) && !editando}
        <div class="secao" bind:this={seletorSecao}>
          {#if documento.secao_id !== null && !trocandoSecao}
            <!-- ler não muda nada: a seção aparece como texto, e trocar é pedido de propósito -->
            <span class="rotulo">Seção do livro</span>
            <span>{opcoesSecao.find((o) => o.valor === String(documento!.secao_id))?.rotulo ?? documento.secao_codigo}</span>
            <button class="acao-texto" onclick={() => { trocandoSecao = true; void tick().then(() => seletorSecao?.querySelector<HTMLButtonElement>('.gatilho')?.click()) }}>trocar</button>
          {:else}
            <Seletor rotulo="Seção do livro" variante="compacto" mostrarRotulo vazio="sem seção ligada"
              valor={documento.secao_id !== null ? String(documento.secao_id) : documento.secao_decidida ? '' : null}
              opcoes={opcoesSecao} onmudar={(v) => { trocandoSecao = false; void escolherSecao(v ? Number(v) : null) }} />
          {/if}
        </div>
        {#if sugestao}
          <div class="sugestao" role="status">
            <span>Ligar à seção {sugestao.codigo} — {sugestao.titulo}?</span>
            <button class="acao-suave" onclick={() => void escolherSecao(sugestao!.secao_id)}>Sim</button>
            <button class="acao-texto" onclick={() => seletorSecao?.querySelector<HTMLButtonElement>('.gatilho')?.click()}>Escolher outra</button>
          </div>
        {/if}
      {/if}
      {#if editando}
        {#key documento.versao}
          <EditorMarkdown {uid} {documento} onsalvo={aoSalvar} oncancelar={() => { if (podeSair()) editando = false }} />
        {/key}
      {:else}
        <div class="leitura-medida"><Markdown texto={semTituloRepetido(documento.corpo, documento.titulo)} contas={documento.tipo === 'resolucao'} rebaixar={1} /></div>
      {/if}
    {:else if fonte}
      <h2>{nomeLegivel(fonte)}</h2>
      {#key `${fonte.id}:${paginaInicial}`}<VisualizadorPdf {uid} {fonte} {paginaInicial} />{/key}
    {:else}
      <p class="suave">Escolha um resumo, anotação, livro ou PDF à esquerda.</p>
    {/if}
  </section>
</div>

<style>
  /* As duas colunas rolam por dentro: a lista não é cortada e o texto não arrasta a página junto */
  .documentos { flex: 1; min-height: 0; display: grid; grid-template-columns: 16rem minmax(0, 1fr); gap: 1.5rem; }
  aside { display: flex; flex-direction: column; gap: 0.5rem; min-height: 0; overflow-y: auto; padding-right: 0.4rem; }
  .titulo-tela { font-size: 2.2rem; margin: 0 0 0.5rem; }
  .leitor { min-height: 0; overflow-y: auto; padding-right: 0.75rem; }
  @media print { .documentos { display: block; } aside { display: none; } .leitor { overflow: visible; } }
  header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
  .secao { max-width: 26rem; margin: 0.2rem 0 0.6rem; }
  .sugestao {
    display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem 1rem; margin: 0 0 0.9rem; padding: 0.5rem 0;
    border-top: 1px solid var(--fio); border-bottom: 1px solid var(--fio);
  }
  .sugestao span { margin-right: auto; }
</style>
