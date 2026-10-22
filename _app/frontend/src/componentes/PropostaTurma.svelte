<script lang="ts">
  import type { PropostaTurma } from '../api/proposta'
  import SeloConfianca from './SeloConfianca.svelte'

  let { proposta }: { proposta: PropostaTurma } = $props()

  const DIAS = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
</script>

<dl>
  <dt>Professor</dt><dd>{proposta.professor ?? 'não encontrado'}{proposta.email ? ` · ${proposta.email}` : ''}</dd>
  <dt>Horários</dt>
  <dd>{proposta.horarios.length ? proposta.horarios.map(([d, i, f]) => `${DIAS[d]} ${i}–${f}`).join(' · ') : 'não encontrados'}</dd>
</dl>
{#if proposta.criterios.length}
  <h4>Critérios de correção</h4>
  <ol>{#each proposta.criterios as c (c)}<li>{c}</li>{/each}</ol>
{/if}
{#if proposta.referencias.length}
  <h4>Bibliografia</h4>
  <ul>
    {#each proposta.referencias as r (r.texto)}
      <li>{r.texto} <span class="suave">({r.papel})</span> <SeloConfianca item={r} /></li>
    {/each}
  </ul>
{/if}

<style>
  dl { display: grid; grid-template-columns: 7rem 1fr; gap: 0.25rem 0.75rem; }
  dt { color: var(--suave); }
  dd { margin: 0; }
  h4 { margin: 1rem 0 0.3rem; font-family: var(--fonte-titulo); font-weight: 500; }
</style>
