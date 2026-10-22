<script lang="ts">
  import { urlArquivo } from '../api/cliente'
  import type { ListaComQuestoes, Questao, SecaoVinculada } from '../api/tipos'
  import { SIMBOLO, type Marca } from '../estado/marcacoes.svelte'
  import EspacoIA from './EspacoIA.svelte'
  import Markdown from './Markdown.svelte'

  let { uid, lista, questao, marca, secao, onmarcar }: {
    uid: string
    lista: ListaComQuestoes
    questao: Questao
    marca: Marca
    secao: SecaoVinculada | null
    onmarcar: (questaoId: number, marca: Marca) => void
  } = $props()

  const NOMES: Record<string, string> = { ok: 'Acertei', err: 'Errei', dub: 'Dúvida' }
  const pagina = $derived(questao.pagina_pdf ?? secao?.pagina_pdf_ini ?? null)
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

  <EspacoIA contexto="tutor" />
</aside>

<style>
  .detalhe { display: grid; gap: 0.75rem; align-content: start; position: sticky; top: 1rem; }
  h3, p { margin: 0; }
  .marcas { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .botao[aria-pressed='true'].ok { background: var(--ok); color: #fff; border-color: var(--ok); }
  .botao[aria-pressed='true'].err { background: var(--err); color: #fff; border-color: var(--err); }
  .botao[aria-pressed='true'].dub { background: var(--dub); color: #000; border-color: var(--dub); }
  a.botao { text-decoration: none; justify-self: start; }
</style>
