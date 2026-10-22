<script lang="ts">
  import type { EventoProposto, PropostaCalendario } from '../api/proposta'
  import { dataCurta } from '../apresentacao'

  let { proposta }: { proposta: PropostaCalendario } = $props()

  const NOME: Record<string, string> = { segunda_chamada: 'Segunda chamada', exame_final: 'Exame final' }
  const contar = (aulas: EventoProposto[], tipo: string) => aulas.filter((a) => a.tipo === tipo).length
</script>

<p>Ano: <b>{proposta.ano ?? 'não encontrado'}</b></p>
{#each proposta.unidades as u (u.numero)}
  <section>
    <h4>{u.numero}ª unidade</h4>
    <p>
      {contar(u.aulas, 'aula')} aulas{#if contar(u.aulas, 'extra')} · {contar(u.aulas, 'extra')} extras{/if}{#if contar(u.aulas, 'feriado')} · {contar(u.aulas, 'feriado')} feriados{/if}
      · prova: <b>{u.prova ? dataCurta(u.prova.data, u.prova.hora_inicio) : 'não encontrada'}</b>
    </p>
    {#each u.aulas.filter((a) => a.revisar) as a (a.data)}
      <p class="duvida">⚠ {dataCurta(a.data)}: “{a.descricao}” — confira se é aula normal.</p>
    {/each}
  </section>
{/each}
{#if proposta.eventos.length}
  <section>
    <h4>Gerais</h4>
    {#each proposta.eventos as e (e.tipo + e.data)}<p>{NOME[e.tipo] ?? e.tipo}: {dataCurta(e.data, e.hora_inicio)}</p>{/each}
  </section>
{/if}

<style>
  section { border-top: 1px solid color-mix(in srgb, var(--borda) 30%, transparent); padding: 0.5rem 0; }
  h4 { margin: 0 0 0.25rem; font-family: var(--fonte-titulo); font-weight: 500; }
  p { margin: 0.2rem 0; }
  .duvida { background: color-mix(in srgb, var(--dub) 30%, transparent); padding: 0 0.3rem; }
</style>
