<script lang="ts">
  // A questão aberta em Praticar: o enunciado primeiro, depois a marcação e o passo para a próxima; embaixo, uma só
  // área de ajuda em abas (IA, resposta do livro, resolução, fórmulas). O enunciado original do livro vem junto. A resolução continua escondida até a aba ser aberta.
  import { requisitar, urlArquivo } from '../api/cliente'
  import type { Documento, DocumentoComCorpo, ExercicioLivro, Formula, ListaComQuestoes, Questao, SecaoVinculada } from '../api/tipos'
  import { erro } from '../estado/avisos.svelte'
  import { SIMBOLO, type Marca } from '../estado/marcacoes.svelte'
  import { renderizarFormula } from '../markdown'
  import PainelIA from './PainelIA.svelte'
  import Markdown from './Markdown.svelte'

  let { uid, lista, questao, marca, secao, resolucao = null, formulas = [], onmarcar, onproxima, onanterior }: {
    uid: string
    lista: ListaComQuestoes
    questao: Questao
    marca: Marca
    secao: SecaoVinculada | null
    resolucao?: Documento | null
    formulas?: Formula[]
    onmarcar: (questaoId: number, marca: Marca) => void
    onproxima?: () => void
    onanterior?: () => void
  } = $props()

  const NOMES: Record<string, string> = { ok: 'Acertei', err: 'Errei', dub: 'Dúvida' }
  type Aba = 'ajuda' | 'resposta' | 'resolucao' | 'formulas'
  let aba = $state<Aba>('ajuda')

  // trocar de questão volta para a ajuda e esconde de novo a resolução
  let corpo = $state<string | null>(null)
  $effect(() => {
    void questao.id
    aba = 'ajuda'
    corpo = null
  })

  // Lista "14.1" questão "22" é o exercício 22 da seção 14.1 do livro: o índice tem o enunciado original e a resposta
  let doLivro = $state<ExercicioLivro | null>(null)
  let procurandoLivro = $state(false)   // enquanto procura, uma linha já ocupa o lugar (a tela não pula)
  $effect(() => {
    const q = questao, s = secao, codigo = lista.codigo
    doLivro = null
    procurandoLivro = false
    if (!s || s.codigo !== codigo || !/^\d+$/.test(q.rotulo)) return
    procurandoLivro = true
    requisitar<ExercicioLivro>('GET', `/api/materias/${uid}/secoes/${s.secao_id}/exercicios/${q.rotulo}`)
      .then((e) => { if (questao.id === q.id) doLivro = e }, () => {}) // 404: não está no índice
      .finally(() => { if (questao.id === q.id) procurandoLivro = false })
  })

  async function abrir(nova: Aba) {
    aba = nova
    if (nova !== 'resolucao' || corpo !== null || !resolucao) return
    try {
      corpo = (await requisitar<DocumentoComCorpo>('GET', `/api/materias/${uid}/documentos/${resolucao.id}`)).corpo
    } catch (e) {
      aba = 'ajuda'
      erro(e)
    }
  }

  const abas = $derived.by(() => {
    const lista: [Aba, string][] = [['ajuda', 'Ajuda da IA']]
    if (doLivro?.resposta) lista.push(['resposta', 'Resposta do livro'])
    if (resolucao) lista.push(['resolucao', 'Resolução'])
    if (formulas.length) lista.push(['formulas', `Fórmulas (${formulas.length})`])
    return lista
  })
</script>

<aside class="detalhe" aria-label="Questão selecionada">
  <header class="cabeca">
    <h2>{lista.codigo} #{questao.rotulo}</h2>
    <span class="suave">{lista.titulo}{questao.linha === 2 ? ' · linha 2' : ''}</span>
    {#if onanterior || onproxima}
      <span class="passos">
        {#if onanterior}<button class="acao-texto" onclick={onanterior}>‹ Anterior</button>{/if}
        {#if onproxima}<button class="acao-texto" onclick={onproxima}>Próxima ›</button>{/if}
      </span>
    {/if}
  </header>

  <div class="enunciado">
    {#if questao.enunciado_md}
      <Markdown texto={questao.enunciado_md} />
    {:else if !doLivro && !procurandoLivro}
      <p class="suave">Exercício do livro{secao ? `: seção ${secao.codigo}` : ''}.</p>
    {/if}
    {#if doLivro}
      <div class="do-livro">
        <span class="rotulo">No livro{doLivro.exercicio.pagina ? ` · p. ${doLivro.exercicio.pagina}` : ''}</span>
        <p>{doLivro.exercicio.trecho}</p>
        {#if doLivro.exercicio.pagina && secao}
          <a class="acao-texto" href={urlArquivo(uid, secao.caminho, doLivro.exercicio.pagina)} target="_blank" rel="noopener">
            Abrir no livro na p. {doLivro.exercicio.pagina}
          </a>
        {/if}
      </div>
    {:else if procurandoLivro}
      <p class="suave procurando">Procurando o enunciado no livro…</p>
    {/if}
  </div>

  <div class="marcas" role="group" aria-label="Marcar questão">
    {#each ['ok', 'err', 'dub'] as m (m)}
      <button class="marca {m}" aria-pressed={marca === m} onclick={() => onmarcar(questao.id, marca === m ? null : (m as Marca))}>
        {SIMBOLO[m]} {NOMES[m]}
      </button>
    {/each}
  </div>

  <div class="abas" role="tablist" aria-label="Ajuda para a questão">
    {#each abas as [a, nome] (a)}
      <button role="tab" id={`aba-${a}`} aria-selected={aba === a} aria-controls={`painel-${a}`} class:ativa={aba === a}
        onclick={() => void abrir(a)}>{nome}</button>
    {/each}
  </div>

  <!-- a IA fica montada (escondida) para uma resposta em andamento não ser cortada ao trocar de aba -->
  <div role="tabpanel" id="painel-ajuda" aria-labelledby="aba-ajuda" hidden={aba !== 'ajuda'}>
    <PainelIA {uid} alvo={`questao:${questao.id}`} papel="tutor" atalhos={['N1', 'N2', 'N3', 'N4']} />
  </div>
  {#if aba === 'resposta' && doLivro?.resposta}
    <div role="tabpanel" id="painel-resposta" aria-labelledby="aba-resposta" class="texto livro">
      <p>{doLivro.resposta.trecho}</p>
    </div>
  {:else if aba === 'resolucao' && resolucao}
    <div role="tabpanel" id="painel-resolucao" aria-labelledby="aba-resolucao" class="texto">
      {#if corpo === null}<p class="suave">Carregando…</p>{:else}<Markdown texto={corpo} contas />{/if}
    </div>
  {:else if aba === 'formulas'}
    <div role="tabpanel" id="painel-formulas" aria-labelledby="aba-formulas" class="texto formulas">
      {#each formulas as f (f.id)}
        <div class="formula">
          <h3>{f.titulo}</h3>
          <div class="tex">{@html renderizarFormula(f.corpo_tex)}</div>
          {#if f.notas_md}<div class="suave"><Markdown texto={f.notas_md} /></div>{/if}
        </div>
      {/each}
    </div>
  {/if}
</aside>

<style>
  .detalhe { display: grid; grid-template-columns: minmax(0, 1fr); gap: 1rem; align-content: start; min-width: 0; }
  .cabeca { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.2rem 1rem; }
  h2 { font-size: 1.6rem; margin: 0; font-variant-numeric: tabular-nums; }
  .passos { margin-left: auto; display: flex; gap: 1.2rem; font-size: 0.92rem; }
  /* o enunciado é o que se lê primeiro: um passo acima do texto da página */
  .enunciado { font-size: 1.12rem; line-height: 1.6; max-width: 46rem; }
  .enunciado :global(p:last-child) { margin-bottom: 0; }

  /* Marcação em texto: a marcada fica na cor da marca e sublinhada; clicar de novo desmarca */
  .marcas { display: flex; flex-wrap: wrap; gap: 1.4rem; }
  .marca { background: none; border: 0; padding: 0 0 2px; font: inherit; color: var(--suave); cursor: pointer; border-bottom: 1.5px solid transparent; }
  .marca:hover { color: var(--texto); }
  .marca[aria-pressed='true'] { font-weight: 500; }
  .marca[aria-pressed='true'].ok { color: var(--ok); border-bottom-color: var(--ok); }
  .marca[aria-pressed='true'].err { color: var(--err); border-bottom-color: var(--err); }
  .marca[aria-pressed='true'].dub { color: var(--dub-texto); border-bottom-color: var(--dub); }

  .abas { display: flex; flex-wrap: wrap; gap: 0.4rem 1.4rem; padding-top: 0.9rem; border-top: 1px solid var(--fio); }
  .abas button { background: none; border: 0; padding: 0 0 2px; font: inherit; font-size: 0.95rem; color: var(--suave); border-bottom: 1.5px solid transparent; cursor: pointer; }
  .abas button:hover:not(:disabled) { color: var(--texto); }
  .abas button.ativa { color: var(--texto); border-bottom-color: var(--destaque); }

  .texto { line-height: 1.6; min-width: 0; overflow-wrap: anywhere; }
  /* títulos das resoluções antigas vêm grandes (# …): aqui ficam no tamanho do texto */
  .texto :global(h1) { font-size: 1.15rem; margin: 0 0 0.5rem; }
  .texto :global(h2), .texto :global(h3) { font-size: 1rem; margin: 0.9rem 0 0.35rem; }
  .livro { display: grid; gap: 0.6rem; white-space: pre-line; }
  /* o enunciado original do livro, logo abaixo do resumo da questão */
  .do-livro { display: grid; gap: 0.3rem; margin-top: 0.8rem; padding-left: 0.9rem; border-left: 1px solid var(--fio); font-size: 1rem; white-space: pre-line; }
  .do-livro p { margin: 0; }
  .do-livro .acao-texto { justify-self: start; font-size: 0.88rem; }
  .procurando { margin: 0.8rem 0 0; font-size: 0.9rem; }
  .livro p { margin: 0; }
  .formula { padding: 0.5rem 0; border-top: 1px solid var(--fio); }
  .formula:first-child { border-top: 0; padding-top: 0; }
  .formula h3 { margin: 0 0 0.3rem; font-family: var(--fonte-texto); font-weight: 500; font-size: 0.95rem; }
  .tex { overflow-x: auto; }
  a.acao-texto { justify-self: start; }
</style>
