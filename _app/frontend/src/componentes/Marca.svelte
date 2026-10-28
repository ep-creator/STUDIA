<script lang="ts">
  let { tamanho = 'normal' }: { tamanho?: 'normal' | 'grande' } = $props()
</script>

<span class="marca {tamanho}">STUDIA</span>

<style>
  .marca { font-family: var(--fonte-titulo); font-weight: 600; letter-spacing: 0.28em; color: var(--texto); }
  .normal { font-size: 0.95rem; }
  .grande { font-size: 1.4rem; }
  .marca { font-weight: 500; }
</style>
