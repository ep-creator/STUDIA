<script lang="ts">
  // Página de um tópico: o resumo para ler no centro; ao lado, as fórmulas, as questões (com as marcações) e as
  // resoluções gravadas. Tudo ligado por regras no motor (seção do tópico, listas do tópico, código no título).
  import { requisitar } from '../api/cliente'
  import type { DocumentoComCorpo, SecaoVinculada, TopicoPagina } from '../api/tipos'
  import { nomeUnidade } from '../apresentacao'
  import Markdown from '../componentes/Markdown.svelte'
  import { erro } from '../estado/avisos.svelte'
  import { pedido } from '../estado/pedido.svelte'
  import { renderizarFormula } from '../markdown'
  import { montarHash, type Area } from './rota'

  let { uid, topico, versao }: { uid: string; topico: number; versao: unknown } = $props()

  let dados = $state<TopicoPagina | null>(null)
  let aberto = $state<number | null>(null)          // resumo em leitura
  let corpo = $state<DocumentoComCorpo | null>(null)

  // relê quando o tópico muda ou o painel é recarregado depois de uma escrita (versao)
  $effect(() => {
    void versao
    requisitar<TopicoPagina>('GET', `/api/materias/${encodeURIComponent(uid)}/topicos/${topico}/pagina`).then((d) => {
      dados = d
      if (!d.resumos.some((r) => r.id === aberto)) aberto = d.resumos[0]?.id ?? null
    }, erro)
  })
  $effect(() => {
    const id = aberto
    corpo = null
    if (id === null) return
    requisitar<DocumentoComCorpo>('GET', `/api/materias/${encodeURIComponent(uid)}/documentos/${id}`).then((d) => {
      if (aberto === id) corpo = d
    }, erro)
  })

  const NOME_MARCA: Record<string, string> = { ok: 'acertei', err: 'errei', dub: 'dúvida' }
  const href = (area: Area, unidade: number) => montarHash({ tela: 'materia', uid, unidade, area })

  function abrirQuestao(id: number, unidade: number) {
    pedido.questao = id
    location.hash = href('listas', unidade)
  }
  function abrirSecao(s: SecaoVinculada) {
    pedido.fonte = { id: s.fonte_id, pagina: s.pagina_pdf_ini }
    location.hash = href('documentos', dados?.unidade ?? 1)
  }
  function abrirDocumento(id: number) {
    pedido.documento = id
    location.hash = href('documentos', dados?.unidade ?? 1)
  }

  const t = $derived(dados?.topico ?? null)
  const erros = $derived((t?.err ?? 0) + (t?.dub ?? 0))
</script>

{#if dados && t}
  <article class="topico">
    <header class="cabeca">
      <a class="acao-texto voltar" href={href('topicos', dados.unidade)}>← Tópicos da {nomeUnidade(dados.unidade)}</a>
      <h1>{t.titulo}</h1>
      <p class="meta">
        <span class="estado {t.estado === 'a seguir' ? 'seguir' : t.estado}">{t.estado}</span>
        {#if t.total}<span class="suave">{t.trabalhadas} de {t.total} questões trabalhadas</span>{/if}
        {#if erros}<span class="erros">{erros} para revisar</span>{/if}
        {#each dados.secoes as s (s.secao_id)}
          <button class="acao-texto" aria-label={`${s.codigo} no livro, página ${s.pagina_pdf_ini}`} onclick={() => abrirSecao(s)}>
            {s.codigo} no livro · p. {s.pagina_pdf_ini}
          </button>
        {/each}
      </p>
    </header>

    <div class="colunas">
      <section class="leitura" aria-label="Resumo">
        {#if dados.resumos.length > 1}
          <div class="abas" role="tablist" aria-label="Resumos do tópico">
            {#each dados.resumos as r (r.id)}
              <button role="tab" aria-selected={aberto === r.id} class:ativa={aberto === r.id} onclick={() => (aberto = r.id)}>{r.titulo}</button>
            {/each}
          </div>
        {/if}
        {#if corpo}
          <Markdown texto={corpo.corpo} />
          <button class="acao-texto editar" onclick={() => abrirDocumento(corpo!.id)}>Abrir na Biblioteca</button>
        {:else if aberto === null}
          <p class="sem-resumo">Este tópico ainda não tem resumo.</p>
          <p class="suave">Escreva um na Biblioteca ou peça à IA (Resumir a seção).</p>
          <a class="acao-texto" href={href('documentos', dados.unidade)}>Abrir a Biblioteca</a>
        {:else}
          <p class="suave">Carregando o resumo…</p>
        {/if}
      </section>

      <aside class="apoio">
        {#if dados.listas.length}
          <section aria-label="Questões">
            <h2 class="rotulo">Questões</h2>
            {#each dados.listas as l (l.id)}
              <div class="lista">
                <span class="nome-lista">{l.titulo}</span>
                {#if l.unidade !== dados.unidade}<span class="suave">{nomeUnidade(l.unidade)}</span>{/if}
                <span class="numeros">
                  {#each l.questoes as q (q.id)}
                    <button class="numero {q.estado ?? ''}" class:resolvida={q.resolucao_id}
                      aria-label={`${l.codigo} #${q.rotulo}${q.estado ? `, ${NOME_MARCA[q.estado]}` : ''}${q.resolucao_id ? ', resolução gravada' : ''}`}
                      onclick={() => abrirQuestao(q.id, l.unidade)}>{q.rotulo}</button>
                  {/each}
                </span>
              </div>
            {/each}
          </section>
        {/if}

        {#if dados.formulas.length}
          <section aria-label="Fórmulas">
            <h2 class="rotulo">Fórmulas</h2>
            {#each dados.formulas as f (f.id)}
              <div class="formula">
                <h3>{f.titulo}</h3>
                <div class="tex">{@html renderizarFormula(f.corpo_tex)}</div>
                {#if f.notas_md}<div class="suave notas"><Markdown texto={f.notas_md} /></div>{/if}
              </div>
            {/each}
          </section>
        {/if}

        {#if dados.resolucoes.length}
          <section aria-label="Resoluções gravadas">
            <h2 class="rotulo">Resoluções gravadas</h2>
            <ul class="resolucoes">
              {#each dados.resolucoes as r (r.id)}
                <li><button class="acao-texto" onclick={() => abrirDocumento(r.id)}>{r.rotulo}</button></li>
              {/each}
            </ul>
          </section>
        {/if}
      </aside>
    </div>
  </article>
{:else}
  <p class="suave">Carregando…</p>
{/if}

<style>
  .topico { display: grid; gap: 1.6rem; max-width: 80rem; }
  .cabeca { display: grid; gap: 0.5rem; }
  .voltar { justify-self: start; font-size: 0.9rem; }
  h1 { font-size: 2.2rem; line-height: 1.15; margin: 0; }
  .meta { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.3rem 1.4rem; margin: 0; font-size: 0.95rem; }
  .meta .acao-texto { color: var(--texto); }
  .estado { color: var(--suave); }
  .estado.hoje { color: var(--destaque-texto); font-weight: 500; }
  .estado.visto { color: var(--ok); }
  .erros { color: var(--err); }

  .colunas { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(18rem, 1fr); gap: 2rem 4rem; align-items: start; padding-top: 1.2rem; border-top: 1px solid var(--fio); }
  .leitura { max-width: 42rem; line-height: 1.65; font-size: 1.02rem; min-width: 0; }
  .abas { display: flex; flex-wrap: wrap; gap: 0.4rem 1.2rem; margin-bottom: 1rem; }
  .abas button { background: none; border: 0; padding: 0 0 2px; font: inherit; font-family: var(--fonte-titulo); color: var(--suave); border-bottom: 1.5px solid transparent; cursor: pointer; }
  .abas button.ativa { color: var(--texto); border-bottom-color: var(--destaque); }
  .editar { margin-top: 0.6rem; font-size: 0.9rem; }
  .sem-resumo { margin: 0 0 0.3rem; font-family: var(--fonte-titulo); font-size: 1.25rem; }

  .apoio { display: grid; grid-template-columns: minmax(0, 1fr); gap: 2rem; min-width: 0; }
  section { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.6rem; align-content: start; min-width: 0; }
  h2.rotulo { margin: 0; font-family: var(--fonte-texto); font-weight: 400; }
  .lista { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.3rem 0.8rem; padding: 0.35rem 0; border-top: 1px solid var(--fio); }
  .lista:first-of-type { border-top: 0; }
  .nome-lista { font-family: var(--fonte-titulo); flex-basis: 100%; }
  .numeros { display: inline-flex; flex-wrap: wrap; gap: 0.2rem 0.7rem; }
  .numero { background: none; border: 0; border-bottom: 2px solid transparent; padding: 0 2px; min-width: 1.4rem; font: inherit; font-variant-numeric: tabular-nums; color: var(--suave); cursor: pointer; }
  .numero:hover { color: var(--destaque-texto); }
  .numero.ok { color: var(--ok); border-bottom-color: var(--ok); }
  .numero.err { color: var(--err); border-bottom-color: var(--err); }
  .numero.dub { color: var(--dub-texto); border-bottom-color: var(--dub); }
  .numero.resolvida:not(.ok):not(.err):not(.dub) { color: var(--texto); border-bottom: 2px dotted var(--suave); }

  .formula { padding: 0.5rem 0; border-top: 1px solid var(--fio); }
  .formula:first-of-type { border-top: 0; }
  .formula h3 { margin: 0 0 0.3rem; font-family: var(--fonte-texto); font-weight: 500; font-size: 0.92rem; }
  .tex { overflow-x: auto; }
  .notas { font-size: 0.9rem; }
  .resolucoes { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 0.3rem 1.2rem; }

  @media (max-width: 1100px) { .colunas { grid-template-columns: 1fr; } }
</style>
