<script lang="ts">
  import { renderizarMarkdown } from '../markdown'

  // contas: texto de matemática do app antigo (blocos ``` viram fórmulas; `trechos` e tabelas ganham cara de conta)
  let { texto, contas = false }: { texto: string; contas?: boolean } = $props()
  const html = $derived(renderizarMarkdown(texto, { contasEmCodigo: contas }))
</script>

<!-- html já sanitizado pelo DOMPurify em renderizarMarkdown -->
<div class="markdown" class:contas>{@html html}</div>

<style>
  .markdown :global(p) { margin: 0 0 0.6rem; }
  .markdown :global(.katex-display) { overflow-x: auto; overflow-y: hidden; }
  .markdown :global(pre) { overflow-x: auto; background: var(--lateral); padding: 0.5rem; border-radius: 6px; }
  .markdown :global(table) { border-collapse: collapse; margin: 0.4rem 0 0.8rem; width: 100%; font-size: 0.95em; }
  .markdown :global(th) { text-align: left; font-weight: 600; color: var(--suave); font-size: 0.8em; letter-spacing: 0.06em; text-transform: uppercase; }
  .markdown :global(th), .markdown :global(td) { padding: 0.35rem 0.6rem 0.35rem 0; border-bottom: 1px solid color-mix(in srgb, var(--borda) 45%, transparent); vertical-align: top; }
  .contas :global(code) { font-family: KaTeX_Main, 'Times New Roman', serif; font-size: 1.08em; background: none; padding: 0; white-space: nowrap; }
  .contas :global(strong) { color: var(--texto); }
</style>
