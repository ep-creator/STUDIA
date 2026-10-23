<script lang="ts">
  // Lugar reservado da IA. Na Fase 6 este componente vira o painel de verdade, sem mexer nas telas que o usam.
  let { contexto, compacto = false }: { contexto: string; compacto?: boolean } = $props()
</script>

<aside class="ia" class:compacto data-contexto={contexto} aria-label="Assistente (em breve)">
  <span class="rotulo">IA</span>
  <p>Chega na Fase 6</p>
</aside>

<style>
  .ia { border: 1px dashed var(--borda); border-radius: var(--raio); padding: 0.75rem; color: var(--suave); opacity: 0.8; }
  .ia p { margin: 0.25rem 0 0; font-size: 0.85rem; }
  .compacto { padding: 0.4rem 0.6rem; display: inline-flex; gap: 0.5rem; align-items: center; }
  .compacto p { margin: 0; }
</style>
