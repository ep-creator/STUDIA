<script lang="ts">
  import type { ResumoMateria } from '../api/tipos'
  import { nomeUnidade, textoContagem } from '../apresentacao'
  import { montarHash } from '../rotas/rota'

  let { materia, hoje = new Date() }: { materia: ResumoMateria; hoje?: Date } = $props()
</script>

<a class="cartao materia" href={montarHash({ tela: 'materia', uid: materia.uid, unidade: null, area: 'painel' })}>
  <h2>{materia.nome}</h2>
  <p class="suave">
    {materia.unidades} {materia.unidades === 1 ? 'unidade' : 'unidades'}{materia.periodo ? ` · ${materia.periodo}` : ''}
  </p>
  {#if materia.proxima_prova}
    <p>
      Prova{materia.proxima_prova.unidade ? ` da ${nomeUnidade(materia.proxima_prova.unidade)}` : ''}:
      <b>{textoContagem(materia.proxima_prova, hoje)}</b>
    </p>
  {/if}
  {#if materia.importacoes_pendentes > 0}
    <p class="pendente">{materia.importacoes_pendentes} importação(ões) esperando revisão</p>
  {/if}
</a>

<style>
  .materia { display: block; text-decoration: none; }
  .materia:hover { outline: 2px solid var(--destaque); }
  p { margin: 0.25rem 0; }
  .pendente { color: var(--destaque); }
</style>
