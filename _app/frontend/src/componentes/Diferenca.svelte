<script lang="ts">
  import { diferencaLinhas } from '../diferenca'

  let { caminho, antes, depois }: { caminho: string; antes: string | null; depois: string | null } = $props()
  const linhas = $derived(diferencaLinhas(antes, depois))
</script>

<figure class="diferenca">
  <figcaption class="suave">{caminho}{antes === null ? ' · criado' : depois === null ? ' · apagado' : ''}</figcaption>
  <pre>{#each linhas as l, i (i)}<span class={l.tipo}>{l.tipo === 'adicionada' ? '+ ' : l.tipo === 'removida' ? '− ' : '  '}{l.texto}
</span>{/each}</pre>
</figure>

<style>
  .diferenca { margin: 0.5rem 0; }
  pre { max-height: 50vh; overflow: auto; background: var(--lateral); padding: 0.6rem; border-radius: 6px; font-size: 0.85rem; white-space: pre-wrap; }
  .adicionada { background: color-mix(in srgb, var(--ok) 25%, transparent); }
  .removida { background: color-mix(in srgb, var(--err) 25%, transparent); text-decoration: line-through; }
  .igual { opacity: 0.7; }
</style>
