<script lang="ts">
  import type { ResumoMateria } from '../api/tipos'
  import { montarHash, type Area, type Rota } from '../rotas/rota'
  import Marca from './Marca.svelte'
  import Seletor from './Seletor.svelte'
  import SeletorTema from './SeletorTema.svelte'
  import { ajuda } from '../estado/ajuda.svelte'

  let { rota, materias, unidade, pendencias }: {
    rota: Exclude<Rota, { tela: 'materias' }>
    materias: ResumoMateria[]
    unidade: number | null
    pendencias: number
  } = $props()

  // As quatro áreas do estudo; abaixo, o que se usa de vez em quando (plano inteiro, folha, material, histórico)
  const AREAS: [Area, string][] = [['painel', 'Hoje'], ['topicos', 'Tópicos'], ['listas', 'Praticar'], ['documentos', 'Biblioteca']]
  const APOIO: [Area, string][] = [['cronograma', 'Plano completo'], ['formulario', 'Folha de fórmulas']]
  const ativa = $derived(rota.tela === 'materia' ? rota.area : null)
  const hrefArea = (area: Area) =>
    montarHash({ tela: 'materia', uid: rota.uid, unidade: area === 'painel' && unidade === null ? null : unidade, area })
</script>

<nav class="lateral nao-imprimir" aria-label="Áreas da matéria">
  <a class="inicio" href="#/" title="Todas as matérias"><Marca /></a>
  <Seletor
    rotulo="Matéria"
    variante="titulo"
    opcoes={materias.map((m) => ({ valor: m.uid, rotulo: m.nome }))}
    valor={rota.uid}
    onmudar={(uid) => (location.hash = montarHash({ tela: 'materia', uid, unidade: null, area: 'painel' }))}
  />

  <ul class="principais">
    {#each AREAS as [area, nome] (area)}
      <li>
        {#if unidade === null && area !== 'painel'}
          <span class="vazia" aria-disabled="true" title="Adicione material primeiro">{nome}</span>
        {:else}
          <a class:ativa={ativa === area} aria-current={ativa === area ? 'page' : undefined} href={hrefArea(area)}>{nome}</a>
        {/if}
      </li>
    {/each}
  </ul>
  <hr />
  <ul class="apoio">
    {#each APOIO as [area, nome] (area)}
      <li>
        {#if unidade === null}
          <span class="vazia" aria-disabled="true" title="Adicione material primeiro">{nome}</span>
        {:else}
          <a class:ativa={ativa === area} aria-current={ativa === area ? 'page' : undefined} href={hrefArea(area)}>{nome}</a>
        {/if}
      </li>
    {/each}
    <li>
      <a class:ativa={rota.tela === 'importar'} aria-current={rota.tela === 'importar' ? 'page' : undefined} href={montarHash({ tela: 'importar', uid: rota.uid })}>
        ＋ Material{#if pendencias > 0}<span class="selo" aria-label={`, ${pendencias} para conferir`}>{pendencias}</span>{/if}
      </a>
    </li>
    <li><a class:ativa={rota.tela === 'historico'} aria-current={rota.tela === 'historico' ? 'page' : undefined} href={montarHash({ tela: 'historico', uid: rota.uid })}>Histórico</a></li>
  </ul>

  <div class="rodape">
    <button class="acao-texto ajuda" onclick={() => (ajuda.aberta = true)} title="Atalhos e ajuda (?)">Atalhos e ajuda <kbd>?</kbd></button>
    <SeletorTema />
  </div>
</nav>

<style>
  .lateral { width: 13rem; flex: none; background: var(--lateral); padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; height: 100vh; position: sticky; top: 0; overflow-y: auto; overflow-x: hidden; }
  .inicio { text-decoration: none; padding: 0.1rem 0.5rem 0.4rem; }
  ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.15rem; }
  a { display: block; text-decoration: none; padding: 0.25rem 0.5rem; border-radius: 6px; }
  a.ativa { background: var(--cartao); font-weight: 600; }
  ul a:hover:not(.ativa) { background: var(--realce); color: var(--destaque-texto); }
  ul a { border-left: 2px solid transparent; border-radius: 0; }
  ul a:hover:not(.ativa) { background: transparent; border-left-color: color-mix(in srgb, var(--destaque) 45%, transparent); }
  a.ativa { background: transparent; border-left: 2px solid var(--destaque); border-radius: 0; }
  hr { border: 0; border-top: 1px solid var(--borda); opacity: 0.4; width: 100%; }
  .principais a { font-size: 1.02rem; padding-top: 0.32rem; padding-bottom: 0.32rem; }
  .apoio a { color: var(--suave); font-size: 0.92rem; }
  .apoio a:hover, .apoio a.ativa { color: var(--texto); }
  /* número de pendências: texto na brasa, sem pílula (o amarelo é da dúvida) */
  .selo { color: var(--destaque-texto); font-weight: 600; font-size: 0.85rem; margin-left: 0.45rem; font-variant-numeric: tabular-nums; }
  .vazia { display: block; padding: 0.25rem 0.5rem; border-left: 2px solid transparent; color: var(--suave); opacity: 0.6; cursor: default; }
  .rodape { margin-top: auto; display: grid; gap: 0.8rem; }
  .ajuda { justify-self: start; font-size: 0.9rem; padding: 0 0.5rem; }
  .ajuda kbd { font-family: var(--fonte-texto); font-size: 0.8rem; margin-left: 0.3rem; padding: 0 0.35rem; border-radius: 4px; background: var(--leve); }
</style>
