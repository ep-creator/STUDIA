<script lang="ts">
  import type { Evento, Sessao } from '../api/tipos'
  import { dataCurta, isoDe } from '../apresentacao'

  let { sessoes, eventos, hoje, dias = 7 }: { sessoes: Sessao[]; eventos: Evento[]; hoje: Date; dias?: number } = $props()

  const ROTULO: Record<string, string> = {
    aula: 'Aula', prova: 'Prova', extra: 'Aula extra', feriado: 'Feriado', segunda_chamada: 'Segunda chamada',
    exame_final: 'Exame final',
  }

  const itens = $derived.by(() => {
    const ini = isoDe(hoje)
    const fim = isoDe(new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() + dias))
    const dentro = (d: string | null) => d !== null && d >= ini && d <= fim
    return [
      ...sessoes.filter((s) => dentro(s.data)).map((s) => ({ data: s.data!, hora: null, texto: `Estudo: ${s.codigo}`, feito: s.feito })),
      ...eventos.filter((e) => dentro(e.data)).map((e) => ({ data: e.data, hora: e.hora_inicio, texto: ROTULO[e.tipo] ?? e.tipo, feito: false })),
    ].sort((a, b) => (a.data + (a.hora ?? '')).localeCompare(b.data + (b.hora ?? '')))
  })
</script>

<section class="cartao">
  <div class="rotulo">Hoje e próximos dias</div>
  {#if itens.length === 0}
    <p class="suave">Nada marcado para os próximos {dias} dias.</p>
  {:else}
    <ul>
      {#each itens as item (item.data + item.texto)}
        <li class:feito={item.feito}><b>{dataCurta(item.data, item.hora)}</b> · {item.texto}</li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  ul { list-style: none; padding: 0; margin: 0.5rem 0 0; }
  li { padding: 0.2rem 0; border-top: 1px solid color-mix(in srgb, var(--borda) 30%, transparent); }
  .feito { text-decoration: line-through; color: var(--suave); }
</style>
