<script lang="ts">
  import type { Evento, Sessao } from '../api/tipos'
  import { isoDe } from '../apresentacao'

  // Os próximos 7 dias lado a lado: aulas, estudos marcados e provas (em destaque)
  let { sessoes, eventos, hoje }: { sessoes: Sessao[]; eventos: Evento[]; hoje: Date } = $props()

  const ROTULO: Record<string, string> = {
    aula: 'Aula', prova: 'Prova', extra: 'Aula extra', feriado: 'Feriado', segunda_chamada: '2ª chamada', exame_final: 'Exame final',
  }
  const NOMES = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']

  const dias = $derived(
    Array.from({ length: 7 }, (_, i) => {
      const d = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() + i)
      const iso = isoDe(d)
      const itens = [
        ...eventos.filter((e) => e.data === iso).map((e) => ({ texto: ROTULO[e.tipo] ?? e.tipo, hora: e.hora_inicio, tipo: e.tipo, feito: false })),
        ...sessoes.filter((s) => s.data === iso).map((s) => ({ texto: `Estudo: ${s.codigo}`, hora: null, tipo: 'estudo', feito: s.feito })),
      ].sort((a, b) => (a.hora ?? '99').localeCompare(b.hora ?? '99'))
      return { iso, nome: i === 0 ? 'hoje' : NOMES[d.getDay()], dia: d.getDate(), itens }
    }),
  )
</script>

<section class="cartao bloco" aria-label="Semana">
  <div class="rotulo">Semana</div>
  <div class="dias">
    {#each dias as d (d.iso)}
      <div class="dia" class:hoje={d.nome === 'hoje'} data-dia={d.iso}>
        <div class="cabeca"><span class="nome">{d.nome}</span><span class="numero">{d.dia}</span></div>
        {#each d.itens as item, i (i)}
          <div class="item {item.tipo === 'prova' ? 'prova' : ''}" class:feito={item.feito}>
            {item.texto}{#if item.hora}<span class="hora">{item.hora}</span>{/if}
          </div>
        {/each}
      </div>
    {/each}
  </div>
</section>

<style>
  .dias { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 0.4rem; margin-top: 0.5rem; }
  .dia { min-height: 6.5rem; padding: 0.45rem; border-radius: 6px; background: color-mix(in srgb, var(--texto) 3%, transparent); display: grid; gap: 0.3rem; align-content: start; }
  .dia.hoje { box-shadow: inset 0 2px 0 var(--destaque); background: var(--realce); }
  .cabeca { display: flex; justify-content: space-between; align-items: baseline; }
  .nome { font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--suave); }
  .hoje .nome { color: var(--destaque); font-weight: 600; }
  .numero { font-family: var(--fonte-titulo); font-size: 1.15rem; }
  .item { font-size: 0.8rem; line-height: 1.3; padding: 0.2rem 0.35rem; border-radius: 4px; background: color-mix(in srgb, var(--texto) 6%, transparent); }
  .item.prova { background: var(--destaque); color: var(--texto-sobre-destaque); font-weight: 600; }
  .item.feito { text-decoration: line-through; color: var(--suave); }
  .hora { display: block; font-size: 0.72rem; opacity: 0.8; }
</style>
