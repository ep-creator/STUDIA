<script lang="ts">
  import { urlArquivo } from '../api/cliente'
  import type { Documento, SecaoVinculada, Topico } from '../api/tipos'
  import { documentoDoTopico } from '../apresentacao'
  import { pedido } from '../estado/pedido.svelte'

  // O próximo tópico a estudar, com atalhos para o resumo dele e a página do livro
  let { uid, topicos, documentos, vinculos, hrefDocumentos, hrefTopicos }: {
    uid: string
    topicos: Topico[]
    documentos: Documento[]
    vinculos: Record<string, SecaoVinculada[]>
    hrefDocumentos: string
    hrefTopicos: string
  } = $props()

  const topico = $derived(topicos.find((t) => t.status === 'proxima') ?? topicos.find((t) => t.status === 'pendente') ?? null)
  const resumo = $derived(topico ? documentoDoTopico(topico.titulo, documentos.filter((d) => d.tipo === 'resumo')) : null)
  const secao = $derived(topico ? (vinculos[String(topico.id)]?.[0] ?? null) : null)
</script>

<section class="cartao bloco" aria-label="Próximo passo">
  <div class="rotulo">Próximo passo</div>
  {#if !topico}
    <p class="suave">Todos os tópicos da unidade já foram vistos. Hora de revisar e refazer as listas.</p>
  {:else}
    <a class="titulo" href={hrefTopicos}>{topico.titulo}</a>
    <div class="atalhos">
      {#if resumo}
        <a class="botao" href={hrefDocumentos} onclick={() => (pedido.documento = resumo.id)}>Ler o resumo</a>
      {/if}
      {#if secao}
        <a class="botao" href={urlArquivo(uid, secao.caminho, secao.pagina_pdf_ini)} target="_blank" rel="noopener">
          Livro: seção {secao.codigo}, p. {secao.pagina_pdf_ini}
        </a>
      {/if}
      {#if !resumo && !secao}<span class="suave">Sem resumo nem seção do livro ligados a este tópico ainda.</span>{/if}
    </div>
  {/if}
</section>

<style>
  .titulo { display: block; font-family: var(--fonte-titulo); font-size: 1.35rem; line-height: 1.25; margin: 0.35rem 0 0.8rem; text-decoration: none; }
  .titulo:hover { color: var(--destaque); }
  .atalhos { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
  .atalhos .botao { text-decoration: none; }
  p { margin: 0.3rem 0 0; }
</style>
