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
  <div class="linha linha-acoes">
    <span class="quando"><b>{hora}</b> <span class="suave">{dia}</span></span>
    <span class="descricao">{ehDesfazer ? `↩ ${grupo.descricao}` : grupo.descricao}{#if grupo.desfeito_em}<span class="suave"> · desfeito</span>{/if}</span>
    <span class="acoes-linha" class:fixas={aberto}><button class="acao-texto" onclick={verDiferenca} aria-expanded={aberto}>{aberto ? 'fechar' : 'detalhes'}</button></span>
    {#if ultimo}<button class="acao-texto desfazer" onclick={ondesfazer}>↶ desfazer</button>{/if}
  </div>
  {#if aberto && detalhe}
    {#each detalhe.arquivos as a (a.caminho)}<Diferenca caminho={a.caminho} antes={a.antes} depois={a.depois} />{/each}
    {#if detalhe.mudancas.length}
      <p class="suave">{detalhe.mudancas.length} {detalhe.mudancas.length === 1 ? 'registro alterado' : 'registros alterados'} no banco ({[...new Set(detalhe.mudancas.map((m) => m.tabela))].join(', ')}).</p>
    {/if}
  {/if}
</li>

<style>
  li { border-bottom: 1px solid var(--fio); padding: 0.55rem 0.4rem; }
  .linha { display: flex; align-items: baseline; gap: 1rem; }
  .quando { width: 6rem; flex: none; font-size: 0.85rem; }
  .quando b { font-weight: 500; }
  .descricao { flex: 1; }
  .acoes-linha { font-size: 0.85rem; }
  .acoes-linha.fixas { opacity: 1; }
  .desfazer { color: var(--destaque); font-size: 0.85rem; }
  .desfeito .descricao { text-decoration: line-through; color: var(--suave); }
  .ehDesfazer .descricao { color: var(--suave); }
</style>
