<script lang="ts">
  import './temas/temas.css'
  import { untrack } from 'svelte'
  import { requisitar } from './api/cliente'
  import type { ResumoMateria } from './api/tipos'
  import Avisos from './componentes/Avisos.svelte'
  import BarraLateral from './componentes/BarraLateral.svelte'
  import GavetaIA from './componentes/GavetaIA.svelte'
  import FaixaMotor from './componentes/FaixaMotor.svelte'
  import { ia } from './estado/ia.svelte'
  import Topo from './componentes/Topo.svelte'
  import BuscaMateria from './componentes/BuscaMateria.svelte'
  import { busca } from './estado/busca.svelte'
  import { erro } from './estado/avisos.svelte'
  import { aoReconectar } from './estado/conexao.svelte'
  import { atalhoDesfazer, desfazer } from './estado/desfazer'
  import { carregarPainel, estadoMateria, painelACarregar } from './estado/materia.svelte'
  import { haAlteracoes, podeSair } from './estado/saida'
  import { acompanharSistema, aplicarTema } from './estado/tema.svelte'
  import Cronograma from './rotas/Cronograma.svelte'
  import Documentos from './rotas/Documentos.svelte'
  import Formulario from './rotas/Formulario.svelte'
  import Historico from './rotas/Historico.svelte'
  import Importacao from './rotas/Importacao.svelte'
  import Listas from './rotas/Listas.svelte'
  import Materias from './rotas/Materias.svelte'
  import Hoje from './rotas/Hoje.svelte'
  import Topicos from './rotas/Topicos.svelte'
  import { analisarRota, type Rota, precisaListaDeMaterias } from './rotas/rota'

  let rota = $state<Rota>(analisarRota(location.hash))
  let materias = $state<ResumoMateria[]>([])

  aplicarTema()

  function teclado(e: KeyboardEvent) {
    // Ctrl K (ou ⌘K) abre a busca na matéria, em qualquer tela da matéria
    if (rota.tela === 'materia' && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault()
      busca.aberta = true
      return
    }
    if (rota.tela !== 'materias' && atalhoDesfazer(e)) {
      e.preventDefault()
      void desfazer()
    }
  }
  $effect(() => acompanharSistema())

  // Mudar de tela com texto não salvo pergunta antes; se o usuário ficar, o endereço volta ao anterior
  let hashAtual = location.hash
  $effect(() => {
    const atualizar = () => {
      if (location.hash !== hashAtual && !podeSair()) {
        history.replaceState(null, '', hashAtual || '#/')
        return
      }
      hashAtual = location.hash
      rota = analisarRota(location.hash)
    }
    const antesDeFechar = (e: BeforeUnloadEvent) => { if (haAlteracoes()) e.preventDefault() }
    window.addEventListener('hashchange', atualizar)
    window.addEventListener('beforeunload', antesDeFechar)
    return () => {
      window.removeEventListener('hashchange', atualizar)
      window.removeEventListener('beforeunload', antesDeFechar)
    }
  })

  // Motor voltou depois de cair: recarrega o que pode ter falhado enquanto estava fora
  $effect(() => aoReconectar(() => {
    void carregarMaterias()
    if (rota.tela !== 'materias') void carregarPainel(rota.uid, rota.tela === 'materia' ? rota.unidade : null)
  }))

  async function carregarMaterias() {
    try {
      materias = await requisitar<ResumoMateria[]>('GET', '/api/materias')
    } catch (e) {
      erro(e)
    }
  }

  // Lista de matérias: na tela inicial e para o seletor da barra lateral; relida quando a matéria aberta não está nela
  // (a recém-criada), uma vez por matéria. Só a rota dispara: a lista é lida sem rastrear, senão cada leitura (que troca
  // o array) dispararia outra, sem fim.
  let listaPedidaPara: string | null = null
  $effect(() => {
    if (!precisaListaDeMaterias(rota, untrack(() => materias), listaPedidaPara)) return
    if (rota.tela !== 'materias') listaPedidaPara = rota.uid
    void carregarMaterias()
  })

  // Painel da matéria/unidade da rota (só recarrega quando muda a matéria ou a unidade pedida).
  $effect(() => {
    const alvo = painelACarregar(rota, {
      uid: estadoMateria.uid, unidade: estadoMateria.unidade, unidades: estadoMateria.painel?.unidades.map((u) => u.numero) ?? null,
    })
    if (alvo) void carregarPainel(alvo.uid, alvo.unidade)
  })

  const painel = $derived(rota.tela !== 'materias' && estadoMateria.uid === rota.uid ? estadoMateria.painel : null)

  // título da aba diz onde se está (leitor de tela e histórico do navegador)
  const NOME_TELA: Record<string, string> = {
    painel: 'Hoje', topicos: 'Tópicos', listas: 'Praticar', cronograma: 'Plano completo', documentos: 'Biblioteca', formulario: 'Folha de fórmulas',
    importar: 'Adicionar material', historico: 'Histórico',
  }
  $effect(() => {
    if (rota.tela === 'materias') document.title = 'STUDIA'
    else {
      const tela = NOME_TELA[rota.tela === 'materia' ? rota.area : rota.tela]
      document.title = painel ? `${tela} · ${painel.materia.nome} — STUDIA` : 'STUDIA'
    }
  })
</script>

<svelte:window onkeydown={teclado} />

<FaixaMotor />

{#if rota.tela === 'materias'}
  <Materias {materias} onmudou={() => void carregarMaterias()} />
{:else}
  <a class="pular" href="#conteudo" onclick={(e) => { e.preventDefault(); document.getElementById('conteudo')?.focus() }}>Pular para o conteúdo</a>
  <div class="app">
    <BarraLateral {rota} {materias} unidade={painel?.unidade ?? null} pendencias={painel?.importacoes_pendentes ?? 0} />
    <main id="conteudo" tabindex="-1" class:ajustada={rota.tela === 'materia' && (rota.area === 'documentos' || rota.area === 'listas')}>
      {#if painel}
        {#if rota.tela === 'materia'}
          <BuscaMateria uid={painel.materia.uid} unidade={painel.unidade} aberta={busca.aberta} onfechar={() => (busca.aberta = false)} />
          <Topo {painel} area={rota.area}>
            {#snippet acoes()}
              <button class="acao-texto" onclick={() => void desfazer()} title="Desfazer a última ação (Ctrl+Z)">↶ Desfazer</button>
              <button class="acao-texto" onclick={() => (ia.aberta = !ia.aberta)} aria-expanded={ia.aberta}>IA ›</button>
            {/snippet}
          </Topo>
          <div class="area" class:ajustada={rota.area === 'documentos' || rota.area === 'listas'}>
            {#if rota.area === 'painel' || !painel.unidade}
              <Hoje {painel} />
            {:else if rota.area === 'listas'}
              <Listas {painel} questao={rota.questao ?? null} />
            {:else if rota.area === 'topicos'}
              <Topicos {painel} topico={rota.topico ?? null} />
            {:else if rota.area === 'cronograma'}
              <Cronograma {painel} />
            {:else if rota.area === 'documentos'}
              <Documentos {painel} />
            {:else if rota.area === 'formulario'}
              <Formulario {painel} />
            {:else}
              <p class="suave">Esta área chega nas próximas etapas.</p>
            {/if}
          </div>
        {:else if rota.tela === 'importar'}
          <Importacao {painel} />
        {:else if rota.tela === 'historico'}
          <Historico uid={rota.uid} />
        {:else}
          <p class="suave">Esta área chega nas próximas etapas.</p>
        {/if}
      {:else}
        <p class="suave">Carregando…</p>
      {/if}
    </main>
    {#if ia.aberta}
      <GavetaIA uid={rota.uid} onfechar={() => (ia.aberta = false)} />
    {/if}
  </div>
{/if}

<Avisos />

<style>
  .app { display: flex; min-height: 100vh; }
  main:focus { outline: none; }
  /* aparece só com o foco do teclado, no canto, por cima de tudo */
  .pular { position: absolute; left: 0.75rem; top: -3rem; z-index: 70; padding: 0.4rem 0.9rem; border-radius: 999px; background: var(--texto); color: var(--fundo); text-decoration: none; }
  .pular:focus { top: 0.75rem; }
  main { flex: 1; min-width: 0; padding: 0.5rem 2rem 3rem; }
  /* Documentos e Listas ocupam exatamente a altura da tela: a lista e o texto rolam cada um no seu espaço, a página fica parada */
  main.ajustada { height: 100vh; display: flex; flex-direction: column; padding-bottom: 1.25rem; }
  .area { display: flex; flex-direction: column; gap: 1.2rem; padding-top: 0.6rem; }
  .area.ajustada { flex: 1; min-height: 0; }
  @media print { main.ajustada, .area.ajustada { height: auto; display: block; } }
</style>
