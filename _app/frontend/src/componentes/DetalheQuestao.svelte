<script lang="ts">
  import { requisitar, urlArquivo } from '../api/cliente'
  import type { Documento, DocumentoComCorpo, ExercicioLivro, ListaComQuestoes, Questao, SecaoVinculada } from '../api/tipos'
  import { erro } from '../estado/avisos.svelte'
  import { SIMBOLO, type Marca } from '../estado/marcacoes.svelte'
  import PainelIA from './PainelIA.svelte'
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

  // A resolução fica escondida (para não estragar a tentativa) até pedir; trocar de questão esconde de novo
  let verResolucao = $state(false)
  let corpo = $state<string | null>(null)
  $effect(() => {
    void questao.id
    verResolucao = false
    corpo = null
  })
  // Lista "14.1" questão "22" é o exercício 22 da seção 14.1 do livro: o índice tem o enunciado original e a resposta
  let doLivro = $state<ExercicioLivro | null>(null)
  let procurandoLivro = $state(false)   // enquanto procura, o botão já ocupa o lugar (a tela não pula)
  let verLivro = $state(false)
  $effect(() => {
    const q = questao, s = secao, codigo = lista.codigo
    doLivro = null
    verLivro = false
    procurandoLivro = false
    if (!s || s.codigo !== codigo || !/^\d+$/.test(q.rotulo)) return
    procurandoLivro = true
    requisitar<ExercicioLivro>('GET', `/api/materias/${uid}/secoes/${s.secao_id}/exercicios/${q.rotulo}`)
      .then((e) => { if (questao.id === q.id) doLivro = e }, () => {}) // 404: não está no índice, o botão some
      .finally(() => { if (questao.id === q.id) procurandoLivro = false })
  })

  async function mostrarResolucao() {
    verResolucao = !verResolucao
    if (!verResolucao || corpo !== null || !resolucao) return
    try {
      corpo = (await requisitar<DocumentoComCorpo>('GET', `/api/materias/${uid}/documentos/${resolucao.id}`)).corpo
    } catch (e) {
      verResolucao = false
      erro(e)
    }
  }
</script>

<aside class="detalhe" aria-label="Questão selecionada">
  <h3>{lista.codigo} #{questao.rotulo}</h3>
  <p class="suave">{lista.titulo}{questao.linha === 2 ? ' · linha 2' : ''}</p>

  <div class="marcas" role="group" aria-label="Marcar questão">
    {#each ['ok', 'err', 'dub'] as m (m)}
      <button class="marca {m}" aria-pressed={marca === m} onclick={() => onmarcar(questao.id, marca === m ? null : (m as Marca))}>
        {SIMBOLO[m]} {NOMES[m]}
      </button>
    {/each}
  </div>

  {#if questao.enunciado_md}
    <Markdown texto={questao.enunciado_md} />
  {:else}
    <p class="suave">Exercício do livro{secao ? `: seção ${secao.codigo}` : ''}.</p>
  {/if}

  {#if (doLivro && secao) || procurandoLivro || resolucao}
    <div class="botoes">
      {#if procurandoLivro && !doLivro}
        <button class="acao-suave" disabled>Ver no livro</button>
      {:else if doLivro && secao}
        <button class="acao-suave" aria-expanded={verLivro} onclick={() => (verLivro = !verLivro)}>
          {verLivro ? 'Esconder o enunciado do livro' : 'Ver no livro'}
        </button>
      {/if}
      {#if resolucao}
        <button class="acao-suave" aria-expanded={verResolucao} onclick={() => void mostrarResolucao()}>
          {verResolucao ? 'Esconder resolução' : 'Ver resolução'}
        </button>
      {/if}
    </div>
  {/if}
  {#if doLivro && secao && verLivro}
    <div class="texto livro">
      <p>{doLivro.exercicio.trecho}</p>
      {#if doLivro.resposta}<p class="suave"><strong>Resposta do livro:</strong> {doLivro.resposta.trecho}</p>{/if}
      {#if doLivro.exercicio.pagina}
        <a class="acao-texto" href={urlArquivo(uid, secao.caminho, doLivro.exercicio.pagina)} target="_blank" rel="noopener">
          Abrir no livro na p. {doLivro.exercicio.pagina}
        </a>
      {/if}
    </div>
  {/if}
  {#if resolucao && verResolucao}
    {#if corpo === null}<p class="suave">Carregando…</p>{:else}<div class="texto"><Markdown texto={corpo} contas /></div>{/if}
  {/if}

  <PainelIA {uid} alvo={`questao:${questao.id}`} papel="tutor" atalhos={['N1', 'N2', 'N3', 'N4']} />
</aside>

<style>
  .detalhe { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.75rem; align-content: start; min-width: 0; }
  .botoes { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .texto { border-top: 1px solid var(--fio); padding-top: 0.8rem; line-height: 1.6; min-width: 0; overflow-wrap: anywhere; }
  /* títulos das resoluções antigas vêm grandes (# …): no menu eles ficam no tamanho do texto */
  .texto :global(h1) { font-size: 1.15rem; margin: 0 0 0.5rem; }
  .texto :global(h2), .texto :global(h3) { font-size: 1rem; margin: 0.9rem 0 0.35rem; }
  h3, p { margin: 0; }
  .livro { display: grid; gap: 0.6rem; white-space: pre-line; }
  h3 { font-size: 1.45rem; }
  /* Marcação em texto: a marcada fica na cor da marca e sublinhada; clicar de novo desmarca */
  .marcas { display: flex; flex-wrap: wrap; gap: 1.1rem; }
  .marca { background: none; border: 0; padding: 0 0 2px; font: inherit; color: var(--suave); cursor: pointer; border-bottom: 1.5px solid transparent; }
  .marca:hover { color: var(--texto); }
  .marca[aria-pressed='true'] { font-weight: 500; }
  .marca[aria-pressed='true'].ok { color: var(--ok); border-bottom-color: var(--ok); }
  .marca[aria-pressed='true'].err { color: var(--err); border-bottom-color: var(--err); }
  .marca[aria-pressed='true'].dub { color: var(--dub); border-bottom-color: var(--dub); }
  a.acao-texto { justify-self: start; }
</style>
