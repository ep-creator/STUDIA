<script lang="ts">
  import type { ListaComQuestoes, Sessao } from '../api/tipos'

  let { sessao, listas = [], onsalvar, oncancelar }: {
    sessao: Partial<Sessao> | null
    listas?: ListaComQuestoes[]
    onsalvar: (dados: { codigo: string; data: string | null; foco_md: string; questao_ids: number[] }) => void
    oncancelar: () => void
  } = $props()

  // svelte-ignore state_referenced_locally
  let codigo = $state(sessao?.codigo ?? '')
  // svelte-ignore state_referenced_locally
  let data = $state(sessao?.data ?? '')
  // svelte-ignore state_referenced_locally
  let foco = $state(sessao?.foco_md ?? '')
  // as questões da sessão: é delas que a tela Hoje tira "Começar pelas questões" e o placar
  // svelte-ignore state_referenced_locally
  let escolhidas = $state<number[]>([...(sessao?.questao_ids ?? [])])
  const alternar = (id: number) => (escolhidas = escolhidas.includes(id) ? escolhidas.filter((x) => x !== id) : [...escolhidas, id])
</script>

<form
  class="editor"
  onsubmit={(e) => { e.preventDefault(); onsalvar({ codigo: codigo.trim(), data: data || null, foco_md: foco, questao_ids: escolhidas }) }}
>
  <label>Nome da sessão <input bind:value={codigo} required placeholder="Ex.: P1, Revisão 14.3" /></label>
  <label>Data <input type="date" bind:value={data} /></label>
  <label class="largo">Foco <textarea rows="2" bind:value={foco} placeholder="O que estudar (aceita Markdown e $fórmulas$)"></textarea></label>
  {#if listas.length}
    <fieldset class="largo questoes">
      <legend>Questões da sessão <span class="suave">· {escolhidas.length === 1 ? '1 escolhida' : `${escolhidas.length} escolhidas`}</span></legend>
      {#each listas as l (l.id)}
        <div class="lista">
          <span class="suave codigo">{l.codigo}</span>
          {#each l.questoes as q (q.id)}
            <button type="button" class="num" aria-pressed={escolhidas.includes(q.id)} aria-label={`${l.codigo} #${q.rotulo}`}
              onclick={() => alternar(q.id)}>{q.rotulo}</button>
          {/each}
        </div>
      {/each}
    </fieldset>
  {/if}
  <div class="botoes">
    <button class="acao-forte" type="submit" disabled={!codigo.trim()}>Salvar sessão</button>
    <button class="acao-texto" type="button" onclick={oncancelar}>Cancelar</button>
  </div>
</form>

<style>
  .editor { display: grid; grid-template-columns: 1fr 12rem; gap: 0.75rem; margin: 1rem 0; }
  label { display: grid; gap: 0.25rem; font-size: 0.85rem; }
  .largo, .botoes { grid-column: 1 / -1; }
  .botoes { display: flex; gap: 0.5rem; }
  input, textarea { border: 1px solid var(--borda); border-radius: 6px; padding: 0.3rem 0.5rem; background: var(--fundo); }
  .questoes { border: 0; padding: 0; margin: 0; display: grid; gap: 0.35rem; font-size: 0.9rem; }
  legend { font-size: 0.85rem; padding: 0; margin-bottom: 0.3rem; }
  .lista { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.15rem 0.5rem; }
  .codigo { min-width: 3rem; font-size: 0.85rem; font-variant-numeric: tabular-nums; }
  .num { background: none; border: 0; border-bottom: 2px solid transparent; padding: 0 2px; min-width: 1.4rem; font: inherit; font-variant-numeric: tabular-nums; color: var(--suave); cursor: pointer; }
  .num:hover { color: var(--texto); }
  .num[aria-pressed='true'] { color: var(--texto); font-weight: 600; border-bottom-color: var(--destaque); }
</style>
