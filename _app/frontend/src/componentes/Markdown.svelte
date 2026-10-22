<script lang="ts">
  import { renderizarMarkdown } from '../markdown'

  let { texto }: { texto: string } = $props()
  const html = $derived(renderizarMarkdown(texto))
</script>

<!-- html já sanitizado pelo DOMPurify em renderizarMarkdown -->
<div class="markdown">{@html html}</div>

<style>
  .markdown :global(p) { margin: 0 0 0.6rem; }
  .markdown :global(.katex-display) { overflow-x: auto; overflow-y: hidden; }
  .markdown :global(pre) { overflow-x: auto; background: var(--lateral); padding: 0.5rem; border-radius: 6px; }
</style>
