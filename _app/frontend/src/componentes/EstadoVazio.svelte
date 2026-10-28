<script lang="ts">
  let { texto, acao }: { texto: string; acao?: { rotulo: string; href: string } } = $props()
</script>

<div class="vazio">
  <p>{texto}</p>
  {#if acao}<a class="acao-suave" href={acao.href}>{acao.rotulo}</a>{/if}
</div>

<style>
  .vazio { padding: 2rem; text-align: center; color: var(--suave); }
  .vazio p { margin: 0 0 1rem; }
  a { text-decoration: none; display: inline-block; }
</style>
