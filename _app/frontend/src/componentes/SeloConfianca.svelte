<script lang="ts">
  import { corDoSelo, numeroPt } from '../confianca'

  let { item, porque }: {
    item: { confianca?: number; revisar?: boolean; numero?: number | null; fonte_id?: number | null; por?: string | null }
    porque?: string
  } = $props()

  const cor = $derived(corDoSelo(item))
  const TEXTO = { certo: 'ok', revisar: 'revisar', 'sem-palpite': 'sem palpite' }
  let aberto = $state(false)
  // motivo do vínculo quando os embeddings contaram (por palavras é o normal e não precisa de etiqueta)
  const MOTIVO: Record<string, string> = { sentido: 'pelo sentido', ambos: 'pelos dois' }
</script>

<span class="selo {cor}" title={item.confianca !== undefined ? `confiança ${numeroPt(item.confianca)}` : undefined}>
  {TEXTO[cor]}{#if item.confianca !== undefined && cor !== 'sem-palpite'} · {numeroPt(item.confianca)}{/if}
</span>
{#if item.por && MOTIVO[item.por]}<span class="motivo">{MOTIVO[item.por]}</span>{/if}
{#if porque}
  <button class="porque" aria-expanded={aberto} onclick={() => (aberto = !aberto)}>por quê?</button>
  {#if aberto}<span class="explicacao">{porque}</span>{/if}
{/if}

<style>
  .selo { font-size: 0.75rem; border-radius: 999px; padding: 0 0.5rem; white-space: nowrap; }
  .certo { background: color-mix(in srgb, var(--ok) 22%, transparent); }
  .revisar { background: var(--dub); color: #000; }
  .sem-palpite { background: var(--err); color: #fff; }
  .motivo { font-size: 0.72rem; margin-left: 0.3rem; color: var(--destaque); }
  .porque { background: none; border: 0; padding: 0 0.3rem; text-decoration: underline; cursor: pointer; font-size: 0.8rem; color: var(--suave); }
  .explicacao { display: block; font-size: 0.85rem; color: var(--suave); margin-top: 0.2rem; }
</style>
