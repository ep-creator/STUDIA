<script lang="ts">
  // Tópicos: o mapa da unidade (cada tópico abre sua página) ou a página de um tópico.
  import type { Painel } from '../api/tipos'
  import { nomeUnidade } from '../apresentacao'
  import ArvoreTopicos from '../componentes/ArvoreTopicos.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import { recarregar } from '../estado/materia.svelte'
  import { montarHash } from './rota'
  import TopicoPagina from './TopicoPagina.svelte'

  let { painel, topico = null }: { painel: Painel; topico?: number | null } = $props()

  const unidade = $derived(painel.unidades.find((u) => u.numero === painel.unidade)!)
</script>

{#if topico}
  <TopicoPagina uid={painel.materia.uid} {topico} versao={painel} />
{:else}
  <h1>Tópicos da {nomeUnidade(unidade.numero)}</h1>
  {#if painel.topicos.length === 0}
    <EstadoVazio
      texto="Nenhum tópico nesta unidade. Importe o programa da disciplina ou adicione abaixo."
      acao={{ rotulo: 'Importar o programa', href: montarHash({ tela: 'importar', uid: painel.materia.uid }) }}
    />
  {/if}
  <ArvoreTopicos
    uid={painel.materia.uid}
    unidade={unidade.numero}
    unidadeId={unidade.id}
    topicos={painel.topicos}
    onmudou={() => void recarregar()}
  />
{/if}

<style>
  h1 { font-size: 2.2rem; margin: 0 0 0.6rem; }
</style>
