<script lang="ts">
  import type { Painel } from '../api/tipos'
  import ContagemProva from '../componentes/ContagemProva.svelte'
  import DesempenhoListas from '../componentes/DesempenhoListas.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import ParaRevisar from '../componentes/ParaRevisar.svelte'
  import ProgressoTopicos from '../componentes/ProgressoTopicos.svelte'
  import ProximoPasso from '../componentes/ProximoPasso.svelte'
  import SemanaPainel from '../componentes/SemanaPainel.svelte'
  import { montarHash } from './rota'

  let { painel, hoje = new Date() }: { painel: Painel; hoje?: Date } = $props()

  const uid = $derived(painel.materia.uid)
  const unidade = $derived(painel.unidades.find((u) => u.numero === painel.unidade) ?? null)
  const prova = $derived.by(() => {
    if (!unidade) return null
    const evento = painel.eventos.find((e) => e.tipo === 'prova' && e.unidade_id === unidade.id)
    if (evento) return { data: evento.data, hora_inicio: evento.hora_inicio }
    return unidade.data_prova ? { data: unidade.data_prova, hora_inicio: null } : null
  })
  const hrefImportar = $derived(montarHash({ tela: 'importar', uid }))
  const area = (a: 'topicos' | 'listas' | 'documentos') => montarHash({ tela: 'materia', uid, unidade: unidade?.numero ?? null, area: a })
</script>

{#if !unidade}
  <EstadoVazio
    texto="Envie o programa da disciplina para criar as unidades e os tópicos."
    acao={{ rotulo: 'Importar arquivos', href: hrefImportar }}
  />
{:else}
  {#if painel.importacoes_pendentes > 0}
    <a class="pendencias" href={hrefImportar}>
      {painel.importacoes_pendentes} {painel.importacoes_pendentes === 1 ? 'importação esperando' : 'importações esperando'} revisão →
    </a>
  {/if}
  <div class="painel">
    <!-- Faixa da prova: a contagem e, ao lado, o que cai (tópicos da unidade com status) -->
    <div class="faixa cartao">
      <ContagemProva {prova} {hoje} {hrefImportar} />
      <ProgressoTopicos topicos={painel.topicos} hrefTopicos={area('topicos')} />
    </div>
    <ParaRevisar listas={painel.listas} marcacoes={painel.marcacoes} hrefListas={area('listas')} />
    <DesempenhoListas listas={painel.listas} marcacoes={painel.marcacoes} />
    <ProximoPasso
      {uid}
      topicos={painel.topicos}
      documentos={painel.documentos}
      vinculos={painel.vinculos.topicos}
      hrefDocumentos={area('documentos')}
      hrefTopicos={area('topicos')}
    />
    <SemanaPainel sessoes={painel.sessoes} eventos={painel.eventos} {hoje} />
  </div>
{/if}

<style>
  .painel { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 1.25rem; }
  .painel > :global(*) { min-width: 0; }
  .faixa { grid-column: 1 / -1; display: grid; grid-template-columns: minmax(13rem, 1fr) minmax(0, 2.6fr); gap: 2rem; align-items: start; }
  .faixa :global(.cartao) { border: 0; padding: 0; background: none; }
  .painel > :global(:nth-child(2)) { grid-column: span 7; }
  .painel > :global(:nth-child(3)) { grid-column: span 5; }
  .painel > :global(:nth-child(4)) { grid-column: span 5; }
  .painel > :global(:nth-child(5)) { grid-column: span 7; }
  @media (max-width: 1100px) { .painel > :global(*) { grid-column: 1 / -1 !important; } .faixa { grid-template-columns: 1fr; } }
  .pendencias {
    display: block; margin-bottom: 1rem; padding: 0.5rem 0.8rem; border-radius: 6px; text-decoration: none;
    background: var(--realce); color: var(--destaque); font-weight: 600; font-size: 0.92rem;
  }
</style>
