<script lang="ts">
  import type { Documento, FonteResumo } from '../api/tipos'

  export type Selecao = { tipo: 'documento' | 'fonte'; id: number } | null

  let { documentos, fontes, selecao, onselecionar }: {
    documentos: Documento[]
    fontes: FonteResumo[]
    selecao: Selecao
    onselecionar: (s: Selecao) => void
  } = $props()

  const GRUPOS_DOC: [string, string][] = [
    ['resumo', 'Resumos'], ['resolucao', 'Resoluções'], ['anotacao', 'Anotações'], ['plano', 'Planos'], ['contexto', 'Contexto'],
  ]
  const GRUPOS_FONTE: [string, string][] = [['livro', 'Livros'], ['lista', 'Listas (PDF)'], ['slides', 'Slides'], ['prova', 'Provas']]
  const outrasFontes = $derived(fontes.filter((f) => !GRUPOS_FONTE.some(([t]) => t === f.tipo)))
  const ativo = (tipo: 'documento' | 'fonte', id: number) => selecao?.tipo === tipo && selecao.id === id
</script>

<nav class="lista" aria-label="Documentos e arquivos">
  {#each GRUPOS_DOC as [tipo, nome] (tipo)}
    {@const itens = documentos.filter((d) => d.tipo === tipo)}
    {#if itens.length}
      <div class="rotulo">{nome}</div>
      <ul>
        {#each itens as d (d.id)}
          <li><button class:ativo={ativo('documento', d.id)} onclick={() => onselecionar({ tipo: 'documento', id: d.id })}>{d.titulo}</button></li>
        {/each}
      </ul>
    {/if}
  {/each}
  {#each [...GRUPOS_FONTE, ['outro', 'Outros PDFs'] as [string, string]] as [tipo, nome] (tipo)}
    {@const itens = tipo === 'outro' ? outrasFontes : fontes.filter((f) => f.tipo === tipo)}
    {#if itens.length}
      <div class="rotulo">{nome}</div>
      <ul>
        {#each itens as f (f.id)}
          <li><button class:ativo={ativo('fonte', f.id)} onclick={() => onselecionar({ tipo: 'fonte', id: f.id })}>{f.titulo || f.caminho.split('/').pop()}</button></li>
        {/each}
      </ul>
    {/if}
  {/each}
</nav>

<style>
  .lista { display: grid; gap: 0.2rem; align-content: start; max-height: 80vh; overflow: auto; }
  .rotulo { margin-top: 0.6rem; }
  ul { list-style: none; margin: 0; padding: 0; }
  button { background: none; border: 0; text-align: left; width: 100%; padding: 0.2rem 0.4rem; border-radius: 6px; cursor: pointer; }
  button.ativo { background: var(--cartao); font-weight: 600; }
  :global(:root[data-tema^='editorial']) button.ativo { background: transparent; border-left: 2px solid var(--destaque); border-radius: 0; }
</style>
