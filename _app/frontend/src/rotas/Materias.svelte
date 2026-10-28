<script lang="ts">
  import { requisitar } from '../api/cliente'
  import type { MateriaCriada, ResumoMateria } from '../api/tipos'
  import { dataPorExtenso, nomeUnidade, proximaProvaGeral, saudacao, textoContagem } from '../apresentacao'
  import Abertura, { deveAbrir } from '../componentes/Abertura.svelte'
  import CartaoMateria from '../componentes/CartaoMateria.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import Marca from '../componentes/Marca.svelte'
  import SeletorTema from '../componentes/SeletorTema.svelte'
  import { erro } from '../estado/avisos.svelte'
  import { montarHash } from './rota'

  let { materias }: { materias: ResumoMateria[] } = $props()

  const agora = new Date()
  let abrindo = $state(deveAbrir())
  let marca = $state<HTMLElement>()
  let criando = $state(false)
  let nome = $state('')

  const proxima = $derived(proximaProvaGeral(materias, agora))
  const quando = $derived.by(() => {
    const t = textoContagem(proxima?.proxima_prova ?? null, agora)
    return t === 'hoje' || t === 'amanhã' ? t : `em ${t}`
  })
  const pendentes =$derived(materias.reduce((t, m) => t + m.importacoes_pendentes, 0))

  async function criar(evento: SubmitEvent) {
    evento.preventDefault()
    try {
      const nova = await requisitar<MateriaCriada>('POST', '/api/materias', { nome: nome.trim() })
      location.hash = montarHash({ tela: 'importar', uid: nova.uid })
    } catch (e) {
      erro(e)
    }
  }
</script>

{#if abrindo}<Abertura alvo={() => marca?.querySelector('.marca')} onfim={() => (abrindo = false)} />{/if}

<div class="materias" class:revelado={!abrindo}>
  <nav class="barra">
    <span class="logo" class:escondido={abrindo} bind:this={marca}><Marca tamanho="grande" /></span>
    <SeletorTema posicao="topo" />
  </nav>

  <section class="boas-vindas">
    <p class="rotulo aparece" style="--i: 0">{dataPorExtenso(agora)}</p>
    <h1 class="aparece" style="--i: 1">{saudacao(agora)}.</h1>
    <p class="resumo aparece" style="--i: 2">
      {#if proxima?.proxima_prova}
        Próxima prova: <b>{proxima.nome}</b>{proxima.proxima_prova.unidade ? `, ${nomeUnidade(proxima.proxima_prova.unidade)}` : ''}
        — <span class="contagem">{quando}</span>.
      {:else if materias.length > 0}
        Nenhuma prova marcada por enquanto.
      {:else}
        Comece criando a primeira matéria.
      {/if}
      {#if pendentes > 0}<span class="pendentes">{pendentes} {pendentes === 1 ? 'arquivo esperando' : 'arquivos esperando'} revisão.</span>{/if}
    </p>
  </section>

  <header class="aparece" style="--i: 3">
    <h2>Suas matérias <span class="contador">{materias.length}</span></h2>
    <button class="acao-suave" onclick={() => (criando = true)}>＋ Nova matéria</button>
  </header>

  {#if criando}
    <form class="nova" onsubmit={criar}>
      <label>Nome <input bind:value={nome} required placeholder="Ex.: Cálculo 2" /></label>
      <button class="acao-forte" type="submit" disabled={!nome.trim()}>Criar</button>
      <button class="acao-texto" type="button" onclick={() => (criando = false)}>Cancelar</button>
      <p class="suave">Depois de criar, é só soltar os PDFs (programa, calendário, livros, listas) na importação.</p>
    </form>
  {/if}

  {#if materias.length === 0 && !criando}
    <EstadoVazio texto="Nenhuma matéria ainda. Crie a primeira: dê um nome e solte os PDFs." />
  {/if}
  <div class="grade">
    {#each materias as m, i (m.uid)}<div class="aparece" style="--i: {4 + i}"><CartaoMateria materia={m} /></div>{/each}
  </div>
</div>

<style>
  .materias { max-width: 62rem; margin: 0 auto; padding: 1.75rem 1.5rem 4rem; }
  .barra { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4.5rem; }
  .logo.escondido { visibility: hidden; }

  .boas-vindas { margin-bottom: 3.5rem; }
  .boas-vindas .rotulo { margin: 0 0 0.6rem; }
  h1 { font-size: clamp(2.4rem, 5vw, 3.6rem); line-height: 1.05; margin: 0 0 0.9rem; letter-spacing: -0.01em; }
  .resumo { margin: 0; font-size: 1.1rem; color: var(--suave); max-width: 40rem; }
  .resumo b { color: var(--texto); font-weight: 600; }
  .contagem { color: var(--destaque); font-weight: 600; }
  .pendentes { display: block; margin-top: 0.3rem; color: var(--destaque); font-size: 0.95rem; }

  header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
  h2 { font-size: 1.35rem; margin: 0; display: flex; align-items: center; gap: 0.6rem; }
  .contador {
    font-family: var(--fonte-texto); font-size: 0.75rem; font-weight: 600; color: var(--suave);
    border: 1px solid color-mix(in srgb, var(--borda) 50%, transparent); border-radius: 999px; padding: 0.05rem 0.5rem;
  }
  .nova { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; margin-bottom: 1.5rem; }
  .nova input { margin-left: 0.5rem; padding: 0.3rem 0.5rem; border: 1px solid var(--borda); border-radius: 6px; background: var(--fundo); }
  .nova p { flex-basis: 100%; margin: 0; }
  .grade { display: grid; grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr)); gap: 1.6rem 3rem; }
  .grade > div { display: grid; }

  /* Entrada: cada bloco sobe um pouco e aparece, um depois do outro (depois da abertura, quando houver) */
  .materias:not(.revelado) .aparece { opacity: 0; }
  .revelado .aparece { animation: subir 560ms cubic-bezier(0.2, 0.7, 0.2, 1) both; animation-delay: calc(var(--i) * 70ms); }
  @keyframes subir { from { opacity: 0; transform: translateY(10px); } }
  @media (prefers-reduced-motion: reduce) { .revelado .aparece { animation: none; } }
</style>
