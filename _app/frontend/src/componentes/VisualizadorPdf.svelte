<script lang="ts">
  import { requisitar, urlArquivo } from '../api/cliente'
  import type { FonteResumo, SecaoLivro } from '../api/tipos'
  import { erro } from '../estado/avisos.svelte'
  import Seletor from './Seletor.svelte'

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
    <div class="sumario">
      <span class="rotulo">Seção</span>
      <Seletor rotulo="Seção do livro" valor={String(pagina)} onmudar={(v) => (pagina = Number(v))}
        opcoes={[{ valor: '1', rotulo: 'Início do livro' }, ...secoes.map((s) => ({ valor: String(s.pagina_pdf_ini), rotulo: `${' '.repeat(Math.max(0, s.nivel - 1))}${s.codigo} ${s.titulo}`, detalhe: `p. ${s.pagina_pdf_ini}` }))]} />
    </div>
  {/if}
  <a class="suave" href={urlArquivo(uid, fonte.caminho, pagina)} target="_blank" rel="noopener">Abrir em outra aba ↗</a>
  {#key pagina}
    <iframe title={`PDF: ${fonte.titulo || fonte.caminho}`} src={urlArquivo(uid, fonte.caminho, pagina)}></iframe>
  {/key}
</div>

<style>
  .pdf { display: grid; gap: 0.5rem; }
  .sumario { display: flex; gap: 0.5rem; align-items: center; }
  iframe { width: 100%; height: 78vh; border: 1px solid var(--borda); border-radius: var(--raio); background: #fff; }
</style>
