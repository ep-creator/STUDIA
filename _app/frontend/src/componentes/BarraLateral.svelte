<script lang="ts">
  import type { ResumoMateria } from '../api/tipos'
  import { montarHash, type Area, type Rota } from '../rotas/rota'
  import Marca from './Marca.svelte'
  import SeletorTema from './SeletorTema.svelte'

  let { rota, materias, unidade, pendencias }: {
    rota: Exclude<Rota, { tela: 'materias' }>
    materias: ResumoMateria[]
    unidade: number | null
    pendencias: number
  } = $props()

  const AREAS: [Area, string][] = [
    ['painel', 'Painel'], ['topicos', 'Tópicos'], ['listas', 'Listas'], ['cronograma', 'Cronograma'],
    ['documentos', 'Documentos'], ['formulario', 'Formulário'],
  ]
  const ativa = $derived(rota.tela === 'materia' ? rota.area : null)
</script>

<nav class="lateral nao-imprimir" aria-label="Áreas da matéria">
  <a class="inicio" href="#/" title="Todas as matérias"><Marca /></a>
  <select
    aria-label="Matéria"
    value={rota.uid}
    onchange={(e) => (location.hash = montarHash({ tela: 'materia', uid: e.currentTarget.value, unidade: null, area: 'painel' }))}
  >
    {#each materias as m (m.uid)}<option value={m.uid}>{m.nome}</option>{/each}
  </select>

  <ul>
    {#each AREAS as [area, nome] (area)}
      <li>
        <a
          class:ativa={ativa === area}
          aria-current={ativa === area ? 'page' : undefined}
          href={montarHash({ tela: 'materia', uid: rota.uid, unidade: area === 'painel' && unidade === null ? null : unidade, area })}
        >{nome}</a>
      </li>
    {/each}
  </ul>
  <hr />
  <ul>
    <li>
      <a class:ativa={rota.tela === 'importar'} href={montarHash({ tela: 'importar', uid: rota.uid })}>
        Importar {#if pendencias > 0}<span class="selo" aria-label={`${pendencias} pendentes`}>{pendencias}</span>{/if}
      </a>
    </li>
    <li><a class:ativa={rota.tela === 'historico'} href={montarHash({ tela: 'historico', uid: rota.uid })}>Histórico</a></li>
  </ul>

  <div class="rodape"><SeletorTema /></div>
</nav>

<style>
  .lateral { width: 13rem; flex: none; background: var(--lateral); padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; height: 100vh; position: sticky; top: 0; overflow-y: auto; }
  .inicio { text-decoration: none; padding: 0.1rem 0.5rem 0.4rem; }
  select { font-family: var(--fonte-titulo); font-weight: 600; background: transparent; border: 0; font-size: 1.05rem; padding: 0; }
  ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.15rem; }
  a { display: block; text-decoration: none; padding: 0.25rem 0.5rem; border-radius: 6px; }
  a.ativa { background: var(--cartao); font-weight: 600; }
  :global(:root[data-tema^='editorial']) a.ativa { background: transparent; border-left: 2px solid var(--destaque); border-radius: 0; }
  hr { border: 0; border-top: 1px solid var(--borda); opacity: 0.4; width: 100%; }
  .selo { background: var(--dub); color: #000; border-radius: 999px; padding: 0 0.45rem; font-size: 0.75rem; margin-left: 0.25rem; }
  .rodape { margin-top: auto; }
</style>
