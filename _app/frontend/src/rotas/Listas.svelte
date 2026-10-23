<script lang="ts">
  import type { Painel } from '../api/tipos'
  import DetalheQuestao from '../componentes/DetalheQuestao.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import GradeQuestoes from '../componentes/GradeQuestoes.svelte'
  import { avisar } from '../estado/avisos.svelte'
  import { marcaDe, marcar, SIMBOLO, type Marca } from '../estado/marcacoes.svelte'
  import { consumirQuestao } from '../estado/pedido.svelte'
  import { montarHash } from './rota'

  let { painel }: { painel: Painel } = $props()

  // o painel pode ter pedido uma questão específica ("Para revisar")
  let selecionada = $state<number | null>(consumirQuestao())
  let menu = $state<HTMLElement>()

  // outra questão aberta: o menu volta ao topo dela
  $effect(() => {
    void selecionada
    menu?.scrollTo?.({ top: 0 })
  })

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
    <div class="coluna questoes">
    <GradeQuestoes listas={painel.listas} marcacoes={painel.marcacoes} {selecionada} onmarcar={aoMarcar} onselecionar={(id) => (selecionada = id)} />
    </div>
    <div class="coluna menu" bind:this={menu}>
    {#if achada}
      <DetalheQuestao
        {uid}
        lista={achada.lista}
        questao={achada.questao}
        marca={marcaDe(achada.questao.id)}
        secao={painel.vinculos.listas[String(achada.lista.id)]?.secao ?? null}
        resolucao={painel.documentos.find((d) => d.tipo === 'resolucao' && d.questao_id === achada.questao.id) ?? null}
        onmarcar={aoMarcar}
      />
    {:else}
      <p class="suave dica">Clique numa questão para abrir os detalhes, marcar e ver a resolução (quando houver). No teclado: setas para andar, 1 ✓, 2 ✗, 3 ?, 0 limpa.</p>
    {/if}
    </div>
  </div>
{/if}

<style>
  /* As questões e o menu rolam cada um no seu espaço (a página fica parada), como em Documentos */
  .listas { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(22rem, 1fr); gap: 1.75rem; }
  .coluna { min-height: 0; overflow-y: auto; padding-right: 0.6rem; }
  .dica { margin: 0; }
  @media print { .listas { display: block; } .coluna { overflow: visible; } .menu { display: none; } }
</style>
