<script lang="ts">
  import { rotuloStatus } from '../apresentacao'

  let { status, onclick }: { status: string; onclick: () => void } = $props()
</script>

<button class="selo {status}" {onclick} title="Clique para mudar o status">{rotuloStatus(status)}</button>

<style>
  /* selo como texto colorido: próxima em laranja, vista em verde, pendente em cinza */
  .selo { background: none; border: 0; padding: 0; cursor: pointer; font: inherit; font-size: 0.78rem; color: var(--suave); min-width: 4.8rem; text-align: left; }
  .selo:hover { text-decoration: underline; text-underline-offset: 3px; }
  .proxima { color: var(--destaque); }
  .visto { color: var(--ok); }
</style>
