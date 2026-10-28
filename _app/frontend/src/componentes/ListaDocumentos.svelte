<script lang="ts">
  import type { Documento, FonteResumo } from '../api/tipos'
  import { compararNomes } from '../apresentacao'
  import { recolhidos } from '../estado/recolhidos.svelte'

  export type Selecao = { tipo: 'documento' | 'fonte'; id: number } | null

  let { documentos, fontes, selecao, onselecionar }: {
    documentos: Documento[]
    fontes: FonteResumo[]
    selecao: Selecao
    onselecionar: (s: Selecao) => void
  } = $props()

  type Item = { tipo: 'documento' | 'fonte'; id: number; titulo: string; ia: boolean }
  type Grupo = { chave: string; nome: string; itens: Item[] }

  // Resumos, resoluções e planos seguem a ordem do livro (posição da seção ligada); os sem seção vão para o fim.
  // Anotações e contexto, a ordem dos nomes
  const GRUPOS_DOC: [string, string, boolean][] = [
    ['resumo', 'Resumos', true], ['resolucao', 'Resoluções', true], ['plano', 'Planos', true], ['anotacao', 'Anotações', false], ['contexto', 'Contexto', false],
  ]
  const GRUPOS_FONTE: [string, string][] = [
    ['programa', 'Programa'], ['calendario', 'Calendário'], ['prova', 'Provas'], ['lista', 'Listas'], ['slides', 'Slides'], ['livro', 'Livros'],
  ]

  const nomeFonte = (f: FonteResumo) => f.titulo || (f.caminho.split('/').pop() ?? '')
  const doDoc = (d: Documento): Item => ({ tipo: 'documento', id: d.id, titulo: d.titulo, ia: d.origem === 'agente' })
  const daFonte = (f: FonteResumo): Item => ({ tipo: 'fonte', id: f.id, titulo: nomeFonte(f), ia: false })

  const estudo = $derived.by((): Grupo[] => {
    const grupos = GRUPOS_DOC.map(([tipo, nome, porAssunto]) => {
      const docs = documentos.filter((d) => d.tipo === tipo)
      const ordem = docs.sort((a, b) =>
        (porAssunto ? (a.secao_posicao ?? Infinity) - (b.secao_posicao ?? Infinity) : 0) || compararNomes(a.titulo, b.titulo))
      return { chave: tipo, nome, itens: ordem.map(doDoc) }
    })
    const outros = documentos.filter((d) => !GRUPOS_DOC.some(([t]) => t === d.tipo)).sort((a, b) => compararNomes(a.titulo, b.titulo))
    return [...grupos, { chave: 'outro-texto', nome: 'Outros textos', itens: outros.map(doDoc) }].filter((g) => g.itens.length)
  })

  const disciplina = $derived.by((): Grupo[] => {
    const ordenadas = [...fontes].sort((a, b) => compararNomes(nomeFonte(a), nomeFonte(b)))
    const grupos = GRUPOS_FONTE.map(([tipo, nome]) => ({ chave: `pdf-${tipo}`, nome, itens: ordenadas.filter((f) => f.tipo === tipo).map(daFonte) }))
    const outros = ordenadas.filter((f) => !GRUPOS_FONTE.some(([t]) => t === f.tipo))
    return [...grupos, { chave: 'pdf-outro', nome: 'Outros PDFs', itens: outros.map(daFonte) }].filter((g) => g.itens.length)
  })

  const recolhiveis = recolhidos('studia.documentos.fechados')

  const ativo = (i: Item) => selecao?.tipo === i.tipo && selecao.id === i.id
</script>

{#snippet secao(titulo: string, grupos: Grupo[])}
  {#if grupos.length}
    <section class="secao" aria-label={titulo}>
      <h3>{titulo}</h3>
      {#each grupos as g (g.chave)}
        {@const aberto = recolhiveis.aberto(g.chave)}
        <button class="grupo" aria-expanded={aberto} onclick={() => recolhiveis.alternar(g.chave)}>
          <svg class="seta" class:aberto viewBox="0 0 12 12" aria-hidden="true"><path d="M4.5 3 7.5 6 4.5 9" /></svg>
          <span class="rotulo">{g.nome}</span>
          <span class="conta">{g.itens.length}</span>
        </button>
        {#if aberto}
          <ul>
            {#each g.itens as i (`${i.tipo}-${i.id}`)}
              <li>
                <button class="item" class:ativo={ativo(i)} onclick={() => onselecionar({ tipo: i.tipo, id: i.id })}>
                  {i.titulo}{#if i.ia}<span class="ia" title="Criado pela IA">IA</span>{/if}
                </button>
              </li>
            {/each}
          </ul>
        {/if}
      {/each}
    </section>
  {/if}
{/snippet}

<nav class="lista" aria-label="Documentos e arquivos">
  {@render secao('Materiais de estudo', estudo)}
  {@render secao('Da disciplina', disciplina)}
</nav>

<style>
  .lista { display: grid; gap: 1.1rem; align-content: start; }
  .secao { display: grid; gap: 0.1rem; }
  h3 {
    font-size: 0.95rem; margin: 0 0 0.25rem; padding-bottom: 0.3rem;
    border-bottom: 1px solid color-mix(in srgb, var(--borda) 60%, transparent);
  }
  ul { list-style: none; margin: 0 0 0.3rem; padding: 0 0 0 1.05rem; }
  button { background: none; border: 0; text-align: left; width: 100%; cursor: pointer; border-radius: 6px; }

  .grupo { display: flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0.2rem; margin-top: 0.15rem; }
  .grupo .rotulo { margin: 0; }
  .grupo:hover .rotulo, .grupo:hover .seta { color: var(--destaque); }
  .seta { width: 0.75rem; height: 0.75rem; flex: none; fill: none; stroke: currentColor; stroke-width: 1.6; color: var(--suave); transition: transform var(--transicao), color var(--transicao); }
  .seta.aberto { transform: rotate(90deg); }
  .conta { margin-left: auto; font-size: 0.72rem; color: var(--suave); }

  .item { padding: 0.2rem 0.4rem; }
  .item.ativo { font-weight: 600; }
  .item:hover:not(.ativo) { background: var(--realce); color: var(--destaque); }
  .item.ativo { background: transparent; border-left: 2px solid var(--destaque); border-radius: 0; }
  .ia {
    display: inline-block; margin-left: 0.4rem; padding: 0 0.3rem; border-radius: 4px; vertical-align: 0.1em;
    font-size: 0.62rem; font-weight: 600; letter-spacing: 0.06em; color: var(--destaque);
    border: 1px solid color-mix(in srgb, var(--destaque) 55%, transparent);
  }
</style>
