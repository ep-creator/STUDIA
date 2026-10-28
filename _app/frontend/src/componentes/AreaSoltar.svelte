<script lang="ts">
  let { onarquivos, ocupado = false, progresso = '' }: {
    onarquivos: (arquivos: File[]) => void
    ocupado?: boolean
    progresso?: string
  } = $props()

  let sobre = $state(false)

  function soltar(e: DragEvent) {
    e.preventDefault()
    sobre = false
    const arquivos = [...(e.dataTransfer?.files ?? [])]
    if (arquivos.length && !ocupado) onarquivos(arquivos)
  }
</script>

<div
  class="area"
  class:sobre
  role="region"
  aria-label="Soltar arquivos para importar"
  aria-busy={ocupado}
  ondragover={(e) => { e.preventDefault(); sobre = true }}
  ondragleave={() => (sobre = false)}
  ondrop={soltar}
>
  {#if ocupado}<p>{progresso || 'Enviando…'}</p>{/if}
  <!-- o campo fica sempre montado (só desabilitado durante o envio), para não perder a referência entre envios -->
  <p class:oculto={ocupado}>Solte os PDFs aqui ou <label class="escolher" class:desabilitado={ocupado}>
    escolha arquivos
    <input
      aria-label="Escolher arquivos"
      type="file"
      accept="application/pdf,.pdf"
      multiple
      disabled={ocupado}
      onchange={(e) => {
        const arquivos = [...(e.currentTarget.files ?? [])]
        e.currentTarget.value = ''
        if (arquivos.length) onarquivos(arquivos)
      }}
    />
  </label></p>
</div>

<style>
  /* área grande: é o alvo principal da tela */
  .area {
    min-height: 14rem; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.4rem;
    border: 1px dashed color-mix(in srgb, var(--texto) 25%, transparent); border-radius: 6px; padding: 1.4rem; text-align: center; color: var(--suave);
  }
  .area.sobre { border-color: var(--destaque); background: var(--realce); }
  p { margin: 0; }
  .oculto { display: none; }
  .escolher { position: relative; color: var(--texto); text-decoration: underline; text-decoration-color: var(--destaque); text-underline-offset: 3px; cursor: pointer; }
  .desabilitado { opacity: 0.5; }
  input { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; }
</style>
