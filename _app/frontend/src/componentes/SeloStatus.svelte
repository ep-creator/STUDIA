<script lang="ts">
  import { rotuloStatus } from '../apresentacao'

  let { status, onclick }: { status: string; onclick: () => void } = $props()
</script>

<button class="selo {status}" {onclick} title="Clique para mudar o status">{rotuloStatus(status)}</button>

<style>
  .selo { border: 1.3px solid var(--borda); border-radius: 999px; padding: 0 0.6rem; background: transparent; cursor: pointer; font-size: 0.8rem; }
  .proxima { border-color: var(--destaque); color: var(--destaque); }
  .visto { background: var(--texto); color: var(--fundo); border-color: var(--texto); }
</style>
