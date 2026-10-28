<script lang="ts">
  import type { Painel } from '../api/tipos'
  import ContagemProva from '../componentes/ContagemProva.svelte'
  import DesempenhoListas from '../componentes/DesempenhoListas.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import ParaRevisar from '../componentes/ParaRevisar.svelte'
  import ProgressoTopicos from '../componentes/ProgressoTopicos.svelte'
  import ProximaAula from '../componentes/ProximaAula.svelte'
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
    <a class="acao-texto pendencias" href={hrefImportar}>
      {painel.importacoes_pendentes} {painel.importacoes_pendentes === 1 ? 'importação esperando' : 'importações esperando'} revisão →
    </a>
  {/if}
  <div class="painel">
    <!-- Faixa de cima: a prova, a próxima aula e os tópicos que caem -->
    <div class="faixa topo">
      <ContagemProva {prova} {hoje} {hrefImportar} />
      <ProximaAula
        topicos={painel.topicos}
        documentos={painel.documentos}
        vinculos={painel.vinculos.topicos}
        hrefDocumentos={area('documentos')}
        hrefTopicos={area('topicos')}
      />
      <ProgressoTopicos topicos={painel.topicos} hrefTopicos={area('topicos')} />
    </div>
    <div class="faixa">
      <ParaRevisar listas={painel.listas} marcacoes={painel.marcacoes} hrefListas={area('listas')} />
      <DesempenhoListas listas={painel.listas} marcacoes={painel.marcacoes} />
    </div>
  </div>
{/if}

<style>
  .painel { display: grid; gap: 1.2rem; }
  .faixa { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 3rem; align-items: start; padding-top: 1.1rem; border-top: 1px solid var(--fio); }
  .faixa.topo { grid-template-columns: 11rem 17rem minmax(0, 1fr); border-top: 0; padding-top: 0.4rem; }
  /* os tópicos ficam sempre na 3ª coluna: sem próxima aula (prova já feita), o layout não muda */
  .faixa.topo > :global(section[aria-label='Tópicos vistos']) { grid-column: 3; }
  .faixa > :global(*) { min-width: 0; }
  @media (max-width: 1100px) {
    .faixa, .faixa.topo { grid-template-columns: 1fr; gap: 1.6rem; }
    .faixa.topo > :global(section[aria-label='Tópicos vistos']) { grid-column: auto; }
  }
  .pendencias { display: inline-block; margin-bottom: 0.8rem; color: var(--destaque); }
</style>
