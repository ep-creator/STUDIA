<script lang="ts">
  import { requisitar } from '../api/cliente'
  import type { DetalheHistorico, GrupoHistorico } from '../api/tipos'
  import { erro } from '../estado/avisos.svelte'
  import Diferenca from './Diferenca.svelte'

  let { uid, grupo, ultimo, ondesfazer }: { uid: string; grupo: GrupoHistorico; ultimo: boolean; ondesfazer: () => void } = $props()

  let detalhe = $state<DetalheHistorico | null>(null)
  let aberto = $state(false)
  const hora = $derived(grupo.momento.slice(11, 16))
  const dia = $derived(grupo.momento.slice(0, 10).split('-').reverse().slice(0, 2).join('/'))
  const ehDesfazer = $derived(grupo.desfaz_grupo !== null)

  async function verDiferenca() {
    aberto = !aberto
    if (aberto && !detalhe) {
      try {
        detalhe = await requisitar<DetalheHistorico>('GET', `/api/materias/${uid}/historico/${grupo.id}`)
      } catch (e) {
        erro(e)
      }
    }
  }
</script>

<li class:desfeito={grupo.desfeito_em} class:ehDesfazer>
  <div class="linha">
    <span class="quando"><b>{hora}</b> <span class="suave">{dia}</span></span>
    <span class="descricao">{ehDesfazer ? `↩ ${grupo.descricao}` : grupo.descricao}{#if grupo.desfeito_em}<span class="suave"> · desfeito</span>{/if}</span>
    <button class="botao" onclick={verDiferenca} aria-expanded={aberto}>{aberto ? 'Fechar' : 'Ver diferença'}</button>
    {#if ultimo}<button class="botao primario" onclick={ondesfazer}>↩ Desfazer</button>{/if}
  </div>
  {#if aberto && detalhe}
    {#each detalhe.arquivos as a (a.caminho)}<Diferenca caminho={a.caminho} antes={a.antes} depois={a.depois} />{/each}
    {#if detalhe.mudancas.length}
      <p class="suave">{detalhe.mudancas.length} {detalhe.mudancas.length === 1 ? 'registro alterado' : 'registros alterados'} no banco ({[...new Set(detalhe.mudancas.map((m) => m.tabela))].join(', ')}).</p>
    {/if}
  {/if}
</li>

<style>
  li { border-top: 1px solid color-mix(in srgb, var(--borda) 25%, transparent); padding: 0.5rem 0; }
  .linha { display: flex; align-items: center; gap: 0.75rem; }
  .quando { width: 6.5rem; flex: none; }
  .descricao { flex: 1; }
  .desfeito .descricao { text-decoration: line-through; color: var(--suave); }
  .ehDesfazer .descricao { color: var(--suave); }
</style>
