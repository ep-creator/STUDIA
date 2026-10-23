<script lang="ts">
  import type { Painel } from '../api/tipos'
  import AgendaCurta from '../componentes/AgendaCurta.svelte'
  import ContagemProva from '../componentes/ContagemProva.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import ProgressoTopicos from '../componentes/ProgressoTopicos.svelte'
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
</script>

{#if !unidade}
  <EstadoVazio
    texto="Envie o programa da disciplina para criar as unidades e os tópicos."
    acao={{ rotulo: 'Importar arquivos', href: hrefImportar }}
  />
{:else}
  <div class="grade">
    <ContagemProva {prova} {hoje} {hrefImportar} />
    <ProgressoTopicos
      topicos={painel.topicos}
      hrefTopicos={montarHash({ tela: 'materia', uid, unidade: unidade.numero, area: 'topicos' })}
    />
    <AgendaCurta sessoes={painel.sessoes} eventos={painel.eventos} {hoje} />
    {#if painel.importacoes_pendentes > 0}
      <section class="cartao">
        <div class="rotulo">Importação</div>
        <a href={hrefImportar}>
          {painel.importacoes_pendentes} {painel.importacoes_pendentes === 1 ? 'importação esperando' : 'importações esperando'} revisão
        </a>
      </section>
    {/if}
  </div>
{/if}

<style>
  .grade { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 1rem; }
</style>
