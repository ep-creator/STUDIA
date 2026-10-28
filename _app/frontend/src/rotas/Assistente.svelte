<script lang="ts">
  // Página do Assistente: as conversas da matéria à esquerda (Geral, Questões, Seções) e a conversa aberta à direita.
  // Chegando pela gaveta ("abrir em página"), abre a conversa que estava lá.
  import { untrack } from 'svelte'
  import { requisitar } from '../api/cliente'
  import type { ConversaResumo } from '../api/tipos'
  import PainelIA from '../componentes/PainelIA.svelte'
  import { atalhosDoPapel, ia } from '../estado/ia.svelte'

  let { uid, hoje = new Date() }: { uid: string; hoje?: Date } = $props()

  let conversas = $state<ConversaResumo[]>([])
  // o pedido da gaveta vale uma vez e só nesta matéria; sem ele, abre a conversa usada por último
  const pedido = untrack(() => (ia.paraPagina?.uid === uid ? ia.paraPagina : null))
  ia.paraPagina = null
  let aberta = $state<{ alvo: string; papel: string }>(pedido ?? { alvo: 'geral', papel: 'estrategista' })

  const GRUPOS: { nome: string; de: (alvo: string) => boolean }[] = [
    { nome: 'Geral', de: (a) => a === 'geral' },
    { nome: 'Questões', de: (a) => a.startsWith('questao:') },
    { nome: 'Seções', de: (a) => a.startsWith('secao:') },
  ]

  $effect(() => {
    requisitar<ConversaResumo[]>('GET', `/api/materias/${uid}/agente/conversas`).then((cs) => {
      conversas = cs
      if (!pedido && cs.length) aberta = { alvo: cs[0].alvo, papel: cs[0].papel }
    }, () => (conversas = []))
  })

  function quando(iso: string): string {
    const dia = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    const ontem = new Date(hoje)
    ontem.setDate(ontem.getDate() - 1)
    if (iso.startsWith(dia(hoje))) return 'hoje'
    if (iso.startsWith(dia(ontem))) return 'ontem'
    return `${iso.slice(8, 10)}/${iso.slice(5, 7)}`
  }

  const ehAberta = (c: ConversaResumo) => c.alvo === aberta.alvo && c.papel === aberta.papel
</script>

<div class="assistente">
  <nav class="conversas" aria-label="Conversas">
    {#each GRUPOS as g (g.nome)}
      {@const doGrupo = conversas.filter((c) => g.de(c.alvo))}
      {#if doGrupo.length}
        <div class="rotulo">{g.nome}</div>
        {#each doGrupo as c (c.id)}
          <button class:ativa={ehAberta(c)} aria-current={ehAberta(c) ? 'true' : undefined}
            onclick={() => (aberta = { alvo: c.alvo, papel: c.papel })}>
            <span class="nome">{c.rotulo}</span><span class="quando">{quando(c.atualizada_em)}</span>
          </button>
        {/each}
      {/if}
    {/each}
  </nav>
  <section class="chat">
    {#key `${aberta.alvo}|${aberta.papel}`}
      <PainelIA {uid} alvo={aberta.alvo} papel={aberta.papel} atalhos={atalhosDoPapel(aberta.papel)} />
    {/key}
  </section>
</div>

<style>
  .assistente { display: grid; grid-template-columns: 16rem minmax(0, 1fr); gap: 2.4rem; min-height: 70vh; }
  .conversas { display: grid; align-content: start; gap: 0.15rem; border-right: 1px solid var(--fio); padding-right: 1rem; }
  .rotulo { padding: 0.8rem 0.6rem 0.3rem; }
  .rotulo:first-child { padding-top: 0; }
  .conversas button {
    display: flex; justify-content: space-between; gap: 0.5rem; width: 100%; text-align: left; background: none; border: 0;
    border-left: 2px solid transparent; padding: 0.35rem 0.6rem; font: inherit; font-size: 0.92rem; color: var(--texto); cursor: pointer;
  }
  .conversas button:hover:not(.ativa) { border-left-color: color-mix(in srgb, var(--destaque) 45%, transparent); }
  .conversas button.ativa { border-left-color: var(--destaque); font-weight: 600; }
  .nome { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .quando { flex: none; color: var(--suave); font-size: 0.78rem; font-weight: 400; }
  .chat { max-width: 52rem; min-width: 0; }
</style>
