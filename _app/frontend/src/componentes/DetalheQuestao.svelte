<script lang="ts">
  import { requisitar, urlArquivo } from '../api/cliente'
  import type { Documento, DocumentoComCorpo, ListaComQuestoes, Questao, SecaoVinculada } from '../api/tipos'
  import { erro } from '../estado/avisos.svelte'
  import { ia } from '../estado/ia.svelte'
  import { SIMBOLO, type Marca } from '../estado/marcacoes.svelte'
  import EspacoIA from './EspacoIA.svelte'
  import Markdown from './Markdown.svelte'

  let { uid, lista, questao, marca, secao, resolucao = null, onmarcar }: {
    uid: string
    lista: ListaComQuestoes
    questao: Questao
    marca: Marca
    secao: SecaoVinculada | null
    resolucao?: Documento | null
    onmarcar: (questaoId: number, marca: Marca) => void
  } = $props()

  const NOMES: Record<string, string> = { ok: 'Acertei', err: 'Errei', dub: 'Dúvida' }
  const pagina = $derived(questao.pagina_pdf ?? secao?.pagina_pdf_ini ?? null)

  // A resolução fica escondida (para não estragar a tentativa) até pedir; trocar de questão esconde de novo
  let verResolucao = $state(false)
  let corpo = $state<string | null>(null)
  $effect(() => {
    void questao.id
    verResolucao = false
    corpo = null
  })
  async function mostrarResolucao() {
    verResolucao = !verResolucao
    if (verResolucao) ia.aberta = false // a resolução precisa de espaço: a área de IA se recolhe
    if (!verResolucao || corpo !== null || !resolucao) return
    try {
      corpo = (await requisitar<DocumentoComCorpo>('GET', `/api/materias/${uid}/documentos/${resolucao.id}`)).corpo
    } catch (e) {
      verResolucao = false
      erro(e)
    }
  }
</script>

<aside class="detalhe cartao" aria-label="Questão selecionada">
  <h3>{lista.codigo} #{questao.rotulo}</h3>
  <p class="suave">{lista.titulo}{questao.linha === 2 ? ' · linha 2' : ''}</p>

  <div class="marcas" role="group" aria-label="Marcar questão">
    {#each ['ok', 'err', 'dub'] as m (m)}
      <button class="botao {m}" aria-pressed={marca === m} onclick={() => onmarcar(questao.id, m as Marca)}>
        {SIMBOLO[m]} {NOMES[m]}
      </button>
    {/each}
    <button class="botao" disabled={marca === null} onclick={() => onmarcar(questao.id, null)}>Limpar</button>
  </div>

  {#if questao.enunciado_md}
    <Markdown texto={questao.enunciado_md} />
  {:else}
    <p class="suave">Exercício do livro{secao ? `: seção ${secao.codigo}` : ''}.</p>
  {/if}

  {#if secao && pagina}
    <a class="botao" href={urlArquivo(uid, secao.caminho, pagina)} target="_blank" rel="noopener">📖 Abrir o livro na p. {pagina}</a>
  {/if}

  {#if resolucao}
    <section class="resolucao">
      <button class="botao" aria-expanded={verResolucao} onclick={() => void mostrarResolucao()}>
        {verResolucao ? 'Esconder resolução' : 'Ver resolução'}
      </button>
      {#if verResolucao}
        {#if corpo === null}<p class="suave">Carregando…</p>{:else}<div class="texto"><Markdown texto={corpo} contas /></div>{/if}
      {/if}
    </section>
  {/if}

  <EspacoIA contexto="tutor" />
</aside>

<style>
  .detalhe { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.75rem; align-content: start; min-width: 0; }
  .resolucao { display: grid; gap: 0.6rem; }
  .resolucao .botao { justify-self: start; }
  .texto { border-top: 1px solid color-mix(in srgb, var(--borda) 60%, transparent); padding-top: 0.8rem; line-height: 1.6; min-width: 0; overflow-wrap: anywhere; }
  /* títulos das resoluções antigas vêm grandes (# …): no menu eles ficam no tamanho do texto */
  .texto :global(h1) { font-size: 1.15rem; margin: 0 0 0.5rem; }
  .texto :global(h2), .texto :global(h3) { font-size: 1rem; margin: 0.9rem 0 0.35rem; }
  h3, p { margin: 0; }
  .marcas { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .botao[aria-pressed='true'].ok { background: var(--ok); color: #fff; border-color: var(--ok); }
  .botao[aria-pressed='true'].err { background: var(--err); color: #fff; border-color: var(--err); }
  .botao[aria-pressed='true'].dub { background: var(--dub); color: #000; border-color: var(--dub); }
  a.botao { text-decoration: none; justify-self: start; }
</style>
