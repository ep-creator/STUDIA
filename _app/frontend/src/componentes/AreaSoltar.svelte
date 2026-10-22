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
  <p>{ocupado ? progresso || 'Enviando…' : 'Solte aqui os PDFs da disciplina: programa, calendário, informações da turma, livros, listas…'}</p>
  <!-- o campo fica sempre montado (só desabilitado durante o envio), para não perder a referência entre envios -->
  <label class="botao" class:desabilitado={ocupado}>
    Escolher arquivos
    <input
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
  </label>
  <p class="suave">Pode mandar tudo de uma vez: a ordem não importa.</p>
</div>

<style>
  .area { border: 1.5px dashed var(--borda); border-radius: var(--raio); padding: 1.25rem; text-align: center; }
  .area.sobre { border-color: var(--destaque); background: color-mix(in srgb, var(--destaque) 8%, transparent); }
  p { margin: 0.25rem 0; }
  label { display: inline-block; margin: 0.5rem 0; position: relative; }
  .desabilitado { opacity: 0.5; }
  input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
</style>
