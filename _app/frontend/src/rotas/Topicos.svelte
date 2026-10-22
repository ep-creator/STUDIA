<script lang="ts">
  import type { Painel } from '../api/tipos'
  import { nomeUnidade } from '../apresentacao'
  import ArvoreTopicos from '../componentes/ArvoreTopicos.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import { recarregar } from '../estado/materia.svelte'
  import { montarHash } from './rota'

  let { painel }: { painel: Painel } = $props()

  const unidade = $derived(painel.unidades.find((u) => u.numero === painel.unidade)!)
  const listasDoTopico = $derived.by(() => {
    const mapa: Record<string, string[]> = {}
    for (const l of painel.listas) {
      for (const t of painel.vinculos.listas[String(l.id)]?.topicos ?? []) (mapa[String(t)] ??= []).push(l.codigo)
    }
    return mapa
  })
</script>

<h2>Tópicos · {nomeUnidade(unidade.numero)}</h2>
{#if painel.topicos.length === 0}
  <EstadoVazio
    texto="Nenhum tópico nesta unidade. Importe o programa da disciplina ou adicione abaixo."
    acao={{ rotulo: 'Importar o programa', href: montarHash({ tela: 'importar', uid: painel.materia.uid }) }}
  />
{/if}
<ArvoreTopicos
  uid={painel.materia.uid}
  unidadeId={unidade.id}
  topicos={painel.topicos}
  vinculos={painel.vinculos.topicos}
  {listasDoTopico}
  onmudou={() => void recarregar()}
/>
