<script lang="ts">
  import type { Documento, SecaoVinculada, Topico } from '../api/tipos'
  import { pedido } from '../estado/pedido.svelte'

  // A próxima aula: o tópico marcado como próximo (senão o primeiro pendente), com o resumo dele quando houver.
  // Sem tópico pendente, não mostra nada.
  let { topicos, documentos, vinculos, hrefDocumentos, hrefTopicos }: {
    topicos: Topico[]
    documentos: Documento[]
    vinculos: Record<string, SecaoVinculada[]>
    hrefDocumentos: string
    hrefTopicos: string
  } = $props()

  const topico = $derived(topicos.find((t) => t.status === 'proxima') ?? topicos.find((t) => t.status === 'pendente') ?? null)
  const secoesDoTopico = $derived(topico ? (vinculos[String(topico.id)] ?? []) : [])
  // o resumo do tópico é o que está ligado a uma das seções do tópico (tópico → seção → documento)
  const resumo = $derived(documentos.find((d) => d.tipo === 'resumo' && secoesDoTopico.some((s) => s.secao_id === d.secao_id)) ?? null)
</script>

{#if topico}
  <section class="aula" aria-label="Próxima aula">
    <div class="rotulo">Próxima aula</div>
    <a class="titulo" href={hrefTopicos}>{topico.titulo}</a>
    {#if resumo}
      <a class="acao-texto" href={hrefDocumentos} onclick={() => (pedido.documento = resumo.id)}>ler o resumo</a>
    {/if}
  </section>
{/if}

<style>
  .aula { display: grid; gap: 0.35rem; align-content: start; }
  .titulo { font-family: var(--fonte-titulo); font-size: 1.25rem; line-height: 1.25; text-decoration: none; margin-top: 0.3rem; }
  .titulo:hover { color: var(--destaque); }
  .acao-texto { justify-self: start; font-size: 0.85rem; text-decoration: underline; text-decoration-color: color-mix(in srgb, var(--destaque) 55%, transparent); }
</style>
