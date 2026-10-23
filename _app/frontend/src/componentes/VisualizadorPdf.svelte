<script lang="ts">
  import { requisitar, urlArquivo } from '../api/cliente'
  import type { FonteResumo, SecaoLivro } from '../api/tipos'
  import { erro } from '../estado/avisos.svelte'

  let { uid, fonte, paginaInicial = 1 }: { uid: string; fonte: FonteResumo; paginaInicial?: number } = $props()

  let secoes = $state<SecaoLivro[]>([])
  // svelte-ignore state_referenced_locally
  let pagina = $state(paginaInicial)

  $effect(() => {
    secoes = []
    if (fonte.tipo !== 'livro') return
    requisitar<SecaoLivro[]>('GET', `/api/materias/${uid}/fontes/${fonte.id}/secoes`).then((s) => (secoes = s), erro)
  })
</script>

<div class="pdf">
  {#if secoes.length}
    <label class="sumario">
      <span class="rotulo">Seção</span>
      <select onchange={(e) => (pagina = Number(e.currentTarget.value))}>
        <option value={1}>Início do livro</option>
        {#each secoes as s (s.id)}
          <option value={s.pagina_pdf_ini}>{'  '.repeat(Math.max(0, s.nivel - 1))}{s.codigo} {s.titulo} (p. {s.pagina_pdf_ini})</option>
        {/each}
      </select>
    </label>
  {/if}
  <a class="suave" href={urlArquivo(uid, fonte.caminho, pagina)} target="_blank" rel="noopener">Abrir em outra aba ↗</a>
  {#key pagina}
    <iframe title={`PDF: ${fonte.titulo || fonte.caminho}`} src={urlArquivo(uid, fonte.caminho, pagina)}></iframe>
  {/key}
</div>

<style>
  .pdf { display: grid; gap: 0.5rem; }
  .sumario { display: flex; gap: 0.5rem; align-items: center; }
  select { max-width: 100%; background: var(--cartao); border: 1px solid var(--borda); border-radius: 6px; padding: 0.2rem; }
  iframe { width: 100%; height: 78vh; border: 1px solid var(--borda); border-radius: var(--raio); background: #fff; }
</style>
