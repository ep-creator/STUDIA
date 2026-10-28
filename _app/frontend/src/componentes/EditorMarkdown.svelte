<script lang="ts">
  import { ErroApi, requisitar } from '../api/cliente'
  import type { DocumentoComCorpo } from '../api/tipos'
  import { erro } from '../estado/avisos.svelte'
  import { marcarAlteracoes } from '../estado/saida'
  import Markdown from './Markdown.svelte'

  let { uid, documento, onsalvo, oncancelar }: {
    uid: string
    documento: DocumentoComCorpo
    onsalvo: () => void
    oncancelar: () => void
  } = $props()

  // svelte-ignore state_referenced_locally
  let corpo = $state(documento.corpo)
  let salvando = $state(false)
  let conflito = $state(false)
  let versaoAtual = $state<DocumentoComCorpo | null>(null)

  // Texto diferente do aberto conta como não salvo (trocar de tela pergunta antes); ao sair do editor, deixa de contar
  $effect(() => marcarAlteracoes('editor', corpo !== documento.corpo))
  $effect(() => () => marcarAlteracoes('editor', false))

  const nomeArquivo = $derived(documento.caminho.split('/').pop() ?? `${documento.id}.md`)

  async function salvar(sobrescrever = false) {
    salvando = true
    try {
      await requisitar('PUT', `/api/materias/${uid}/documentos`, {
        tipo: documento.tipo, nome_arquivo: nomeArquivo, titulo: documento.titulo, corpo,
        unidade_id: documento.unidade_id, secao_id: documento.secao_id, questao_id: documento.questao_id,
        versao_esperada: sobrescrever ? null : (versaoAtual?.versao ?? documento.versao),
      })
      marcarAlteracoes('editor', false)
      onsalvo()
    } catch (e) {
      if (e instanceof ErroApi && e.status === 409) conflito = true
      else erro(e)
    } finally {
      salvando = false
    }
  }

  async function verAtual() {
    try {
      versaoAtual = await requisitar<DocumentoComCorpo>('GET', `/api/materias/${uid}/documentos/${documento.id}`)
    } catch (e) {
      erro(e)
    }
  }
</script>

<div class="editor">
  <label class="campo">
    <span class="rotulo">Markdown</span>
    <textarea aria-label="Texto do documento" bind:value={corpo} spellcheck="true"></textarea>
  </label>
  <div class="previa">
    <span class="rotulo">Prévia</span>
    <Markdown texto={corpo} />
  </div>
</div>

{#if conflito}
  <div class="conflito" role="alert">
    <p>Este documento mudou desde que você abriu (em outro programa ou em outra aba). O seu texto continua aqui.</p>
    {#if !versaoAtual}
      <button class="acao-texto" onclick={verAtual}>Ver versão atual</button>
    {:else}
      <div class="atual"><span class="rotulo">Versão atual</span><Markdown texto={versaoAtual.corpo} /></div>
      <button class="acao-texto" onclick={() => { corpo = versaoAtual!.corpo; conflito = false }}>Usar a versão atual</button>
      <button class="acao-suave" onclick={() => salvar(true)}>Manter o meu e salvar por cima</button>
    {/if}
  </div>
{/if}

<div class="botoes">
  <button class="acao-forte" onclick={() => salvar()} disabled={salvando}>Salvar</button>
  <button class="acao-texto" onclick={oncancelar}>Cancelar</button>
</div>

<style>
  .editor { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; min-height: 60vh; }
  .campo { display: flex; flex-direction: column; gap: 0.25rem; }
  textarea { flex: 1; min-height: 50vh; font-family: ui-monospace, monospace; font-size: 0.9rem; border: 1px solid var(--borda); border-radius: 6px; padding: 0.6rem; background: var(--fundo); resize: vertical; }
  .previa { overflow: auto; max-height: 70vh; }
  .conflito { margin: 1rem 0; display: grid; gap: 0.5rem; justify-items: start; }
  .atual { max-height: 30vh; overflow: auto; width: 100%; }
  .botoes { display: flex; gap: 0.5rem; margin-top: 1rem; }
</style>
