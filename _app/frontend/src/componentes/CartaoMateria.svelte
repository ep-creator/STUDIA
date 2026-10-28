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
    <p class="pendente">{materia.importacoes_pendentes} {materia.importacoes_pendentes === 1 ? 'arquivo esperando' : 'arquivos esperando'} revisão</p>
  {/if}
  <span class="abrir" aria-hidden="true">Abrir →</span>
</a>

<style>
  /* respiro em volta do texto, compensado na margem: fora do hover o texto fica alinhado com o título da seção */
  .materia { position: relative; display: block; text-decoration: none; min-height: 9rem; padding: 1rem 1.2rem 2.6rem; margin: -1rem -1.2rem 0; border-radius: 2px; }
  p { margin: 0.25rem 0; }
  h2 { transition: color var(--transicao); }
  .pendente { color: var(--destaque); }
  .abrir {
    position: absolute; right: 1.2rem; bottom: 1rem; font-size: 0.85rem; color: var(--destaque);
    opacity: 0; transform: translateX(-6px); transition: opacity var(--transicao), transform var(--transicao);
  }
  .materia:hover h2, .materia:focus-visible h2 { color: var(--destaque); }
  .materia:hover .abrir, .materia:focus-visible .abrir { opacity: 1; transform: none; }

  /* a linha do topo vira laranja, da esquerda para a direita */
  .materia::before {
    content: ''; position: absolute; left: 0; top: -1.5px; height: 1.5px; width: 0; background: var(--destaque);
    transition: width 280ms ease;
  }
  .materia:hover::before, .materia:focus-visible::before { width: 100%; }
  .materia:hover { background: var(--realce); }

  .materia:focus-visible { outline: none; }
</style>
