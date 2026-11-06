<script lang="ts">
  import type { Painel } from '../api/tipos'
  import DetalheQuestao from '../componentes/DetalheQuestao.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import GradeQuestoes from '../componentes/GradeQuestoes.svelte'
  import { avisar } from '../estado/avisos.svelte'
  import { marcaDe, marcar, SIMBOLO, type Marca } from '../estado/marcacoes.svelte'
  import { consumirQuestao, pedido } from '../estado/pedido.svelte'
  import { citaSecao } from '../apresentacao'
  import { digitando } from '../estado/ajuda.svelte'
  import { montarHash } from './rota'

  let { painel, questao = null }: { painel: Painel; questao?: number | null } = $props()

  // Hoje (ou a busca) pode ter pedido uma questão específica; se for de outra unidade, ela chega quando o painel dela
  // carregar, então o pedido só é consumido quando a questão aparece aqui
  let selecionada = $state<number | null>(null)
  $effect(() => {
    const pedida = pedido.questao
    if (pedida !== null && painel.listas.some((l) => l.questoes.some((q) => q.id === pedida))) selecionada = consumirQuestao()
  })
  // a questão do endereço (#/…/listas/<id>): voltar, recarregar e favoritos reabrem a mesma
  $effect(() => {
    if (questao !== null) selecionada = questao
  })
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
  // e a questão aberta vai para o endereço (sem empilhar no histórico a cada seta), só quando já está nesta unidade
  $effect(() => {
    if (!achada || painel.unidade === null) return
    const alvo = montarHash({ tela: 'materia', uid, unidade: painel.unidade, area: 'listas', questao: achada.questao.id })
    if (location.hash !== alvo) history.replaceState(history.state, '', alvo)
  })

  // a ordem da grade: anterior e próxima andam por ela
  const ordem = $derived(painel.listas.flatMap((l) => l.questoes.map((q) => q.id)))
  const passo = (delta: number) => {
    const i = ordem.indexOf(selecionada ?? -1)
    const alvo = ordem[i + delta]
    if (alvo !== undefined) selecionada = alvo
  }
  // fórmulas da seção da lista aberta: pela seção ou pelo código "(15.4)" no título (a mesma regra do motor)
  const formulasDa = (codigo: string | undefined, secaoId: number | undefined) =>
    codigo === undefined ? [] : painel.formulas.filter((f) => f.secao_id === secaoId || citaSecao(f.titulo, codigo))

  // Teclas na tela toda (fora da grade, que tem as suas, e fora de campos de texto): 1/2/3/0 marcam a questão aberta;
  // N vai para a próxima ainda não trabalhada (sem marca), na ordem da grade, voltando ao começo se preciso
  const MARCA_TECLA: Record<string, Marca> = { '1': 'ok', '2': 'err', '3': 'dub', '0': null }
  function teclaPraticar(e: KeyboardEvent) {
    if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey || digitando(e.target)) return
    if (document.querySelector('[role="dialog"]')) return   // busca, ajuda ou IA abertas: as teclas são delas
    if (achada && e.key in MARCA_TECLA) {
      e.preventDefault()
      aoMarcar(achada.questao.id, MARCA_TECLA[e.key])
    } else if (e.key.toLowerCase() === 'n') {
      const i = ordem.indexOf(selecionada ?? -1)
      const seguinte = [...ordem.slice(i + 1), ...ordem.slice(0, i + 1)].find((id) => !painel.marcacoes[String(id)])
      if (seguinte !== undefined) {
        e.preventDefault()
        selecionada = seguinte
      }
    }
  }

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

<svelte:window onkeydown={teclaPraticar} />

{#if painel.listas.length === 0}
  <EstadoVazio texto="Nenhuma lista nesta unidade ainda." acao={{ rotulo: 'Importar listas', href: montarHash({ tela: 'importar', uid }) }} />
{:else}
  <h1 class="titulo-tela">Praticar <span class="suave">· {painel.unidade}ª unidade</span></h1>
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
        formulas={formulasDa(painel.vinculos.listas[String(achada.lista.id)]?.secao?.codigo, painel.vinculos.listas[String(achada.lista.id)]?.secao?.secao_id)}
        onmarcar={aoMarcar}
        onanterior={ordem.indexOf(achada.questao.id) > 0 ? () => passo(-1) : undefined}
        onproxima={ordem.indexOf(achada.questao.id) < ordem.length - 1 ? () => passo(1) : undefined}
      />
    {:else}
      <p class="dica">Escolha uma questão.</p>
      <p class="suave atalhos">No teclado: setas andam · 1 acertei · 2 errei · 3 dúvida · 0 limpa.</p>
    {/if}
    </div>
  </div>
{/if}

<style>
  /* As questões e o menu rolam cada um no seu espaço (a página fica parada), como em Documentos */
  /* a questão aberta é o lugar de trabalho: ganha a maior parte da largura */
  .listas { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(17rem, 0.8fr) minmax(0, 1.5fr); gap: 1.75rem; }
  .coluna { min-height: 0; overflow-y: auto; overflow-x: hidden; padding-right: 0.6rem; }
  /* a questão aberta fica separada da lista por um fio, sem cartão */
  .menu { border-left: 1px solid var(--fio); padding-left: 2rem; }
  .titulo-tela { font-size: 1.6rem; margin: 0 0 0.6rem; }
  .titulo-tela span { font-family: var(--fonte-texto); font-size: 1rem; }
  .dica { margin: 0 0 0.3rem; font-family: var(--fonte-titulo); font-size: 1.3rem; }
  .atalhos { margin: 0; font-size: 0.9rem; }
  @media print { .listas { display: block; } .coluna { overflow: visible; } .menu { display: none; } }
</style>
