<script lang="ts">
  import type { Painel } from '../api/tipos'
  import DetalheQuestao from '../componentes/DetalheQuestao.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import GradeQuestoes from '../componentes/GradeQuestoes.svelte'
  import { avisar } from '../estado/avisos.svelte'
  import { marcaDe, marcar, SIMBOLO, type Marca } from '../estado/marcacoes.svelte'
  import { montarHash } from './rota'

  let { painel }: { painel: Painel } = $props()

  let selecionada = $state<number | null>(null)

  const uid = $derived(painel.materia.uid)
  const achada = $derived.by(() => {
    for (const l of painel.listas) {
      const q = l.questoes.find((x) => x.id === selecionada)
      if (q) return { lista: l, questao: q }
    }
    return null
  })

  function aoMarcar(questaoId: number, marca: Marca) {
    const anterior = marcaDe(questaoId)
    const alvo = painel.listas.flatMap((l) => l.questoes.map((q) => ({ l, q }))).find((x) => x.q.id === questaoId)
    void marcar(questaoId, marca)
    if (alvo) {
      const texto = marca ? `marcada ${SIMBOLO[marca]}` : 'sem marcação'
      avisar(`Questão ${alvo.l.codigo} #${alvo.q.rotulo} ${texto}`, { rotulo: 'Desfazer', executar: () => void marcar(questaoId, anterior) })
    }
  }
</script>

{#if painel.listas.length === 0}
  <EstadoVazio texto="Nenhuma lista nesta unidade ainda." acao={{ rotulo: 'Importar listas', href: montarHash({ tela: 'importar', uid }) }} />
{:else}
  <div class="listas">
    <GradeQuestoes listas={painel.listas} marcacoes={painel.marcacoes} {selecionada} onmarcar={aoMarcar} onselecionar={(id) => (selecionada = id)} />
    {#if achada}
      <DetalheQuestao
        {uid}
        lista={achada.lista}
        questao={achada.questao}
        marca={marcaDe(achada.questao.id)}
        secao={painel.vinculos.listas[String(achada.lista.id)]?.secao ?? null}
        onmarcar={aoMarcar}
      />
    {:else}
      <p class="suave dica">Clique numa questão para marcar (✓ → ✗ → ? → vazio) e ver os detalhes. No teclado: setas para andar, 1 ✓, 2 ✗, 3 ?, 0 limpa.</p>
    {/if}
  </div>
{/if}

<style>
  .listas { display: grid; grid-template-columns: minmax(0, 1fr) 20rem; gap: 1.5rem; align-items: start; }
  .dica { position: sticky; top: 1rem; }
</style>
