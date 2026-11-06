<script lang="ts">
  // Casa da matéria: a sessão do plano em foco, com o material a um clique; depois o que revisar (todas as unidades),
  // os próximos 7 dias e os tópicos com o progresso derivado no motor (spec 2026-11-05-redesenho-hoje-design).
  import { requisitar } from '../api/cliente'
  import type { Hoje, Painel, SecaoVinculada } from '../api/tipos'
  import { dataCurta, dataPorExtenso, nomeUnidade, ordinal } from '../apresentacao'
  import PrimeirosPassos from '../componentes/PrimeirosPassos.svelte'
  import { erro } from '../estado/avisos.svelte'
  import { pedido } from '../estado/pedido.svelte'
  import { montarHash, type Area } from './rota'

  let { painel, hoje = new Date() }: { painel: Painel; hoje?: Date } = $props()

  const uid = $derived(painel.materia.uid)
  let dados = $state<Hoje | null>(null)

  // o painel é relido depois de toda escrita (marcar, gravar…): a tela Hoje acompanha
  $effect(() => {
    void painel
    requisitar<Hoje>('GET', `/api/materias/${encodeURIComponent(uid)}/hoje`).then((d) => (dados = d), erro)
  })

  const NOME_MARCA: Record<string, string> = { ok: 'acertei', err: 'errei', dub: 'dúvida' }
  const CLASSE_ESTADO: Record<string, string> = { hoje: 'hoje', visto: 'visto', 'começado': 'comecado', 'a seguir': 'seguir' }
  const ESTADO_SESSAO: Record<string, string> = { feita: 'feita', passou: 'passou', hoje: 'hoje', futura: '' }
  const TIPO_EVENTO: Record<string, string> = {
    prova: 'Prova', aula: 'Aula', segunda_chamada: 'Segunda chamada', exame_final: 'Exame final', extra: 'Aula extra', feriado: 'Feriado',
  }

  const href = (area: Area, unidade: number | null = painel.unidade) => montarHash({ tela: 'materia', uid, unidade, area })
  const rotuloQuestao = (lista: string, rotulo: string, estado: string | null, resolvida = false) =>
    `${lista} #${rotulo}${estado ? `, ${NOME_MARCA[estado]}` : ''}${resolvida ? ', resolução gravada' : ''}`

  function abrirQuestao(id: number, unidade: number) {
    location.hash = montarHash({ tela: 'materia', uid, unidade, area: 'listas', questao: id })
  }
  function abrirSecao(s: SecaoVinculada, unidade: number) {
    pedido.fonte = { id: s.fonte_id, pagina: s.pagina_pdf_ini }
    location.hash = href('documentos', unidade)
  }
  function abrirResumo(id: number, unidade: number) {
    pedido.documento = id
    location.hash = href('documentos', unidade)
  }

  const sessao = $derived(dados?.sessao ?? null)
  const deHoje = $derived(sessao?.data === dados?.data)
  // questões da sessão agrupadas por lista, na ordem em que vieram
  const gruposSessao = $derived.by(() => {
    const grupos: { lista: string; questoes: NonNullable<typeof sessao>['questoes'] }[] = []
    for (const q of sessao?.questoes ?? []) {
      const g = grupos.at(-1)
      if (g && g.lista === q.lista_codigo) g.questoes.push(q)
      else grupos.push({ lista: q.lista_codigo, questoes: [q] })
    }
    return grupos
  })
  const primeira = $derived(sessao?.questoes.find((q) => !q.estado && !q.resolucao_id) ?? null)
  const primeiraRevisar = $derived(dados?.revisar[0] ? { id: dados.revisar[0].questoes[0].id, unidade: dados.revisar[0].unidade } : null)
  // a ação forte segue o estado: na reta final, revisar os erros; senão, a próxima questão da sessão; feita a sessão,
  // revisar os erros (ou nada, se não houver)
  const acao = $derived.by(() => {
    const revisar = primeiraRevisar && {
      rotulo: `Revisar ${plural(totalRevisar, 'questão marcada', 'questões marcadas')}`, ...primeiraRevisar,
    }
    if (dados?.reta_final && revisar) return revisar
    if (primeira) return { rotulo: sessao && sessao.trabalhadas > 0 ? 'Continuar pelas questões' : 'Começar pelas questões', id: primeira.id, unidade: primeira.unidade }
    return revisar
  })
  const codigosSessao = $derived(sessao?.secoes.map((s) => s.codigo).join(', ') ?? '')

  const totalRevisar = $derived(dados?.revisar.reduce((t, g) => t + g.questoes.length, 0) ?? 0)
  // na reta final, os tópicos com mais erros e dúvidas primeiro
  const fracos = $derived(
    [...(dados?.topicos ?? [])].filter((t) => t.err + t.dub > 0).sort((a, b) => b.err + b.dub - (a.err + a.dub)).slice(0, 3),
  )

  const prova = $derived(dados?.prova ?? null)
  const textoProva = $derived.by(() => {
    if (!prova) return null
    const unidade = nomeUnidade(prova.unidade)
    if (prova.dias === 0) return 'Prova hoje. Boa prova.'
    if (prova.dias === 1) return `Prova da ${unidade} amanhã`
    return `Prova da ${unidade} em ${prova.dias} dias · ${dataCurta(prova.data, prova.hora_inicio)}`
  })
  const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`
</script>

<div class="hoje">
  <header class="cabeca">
    <h1>Hoje</h1>
    <span class="suave data">{dataPorExtenso(hoje)}</span>
    {#if textoProva}<span class="prova" class:perto={dados?.reta_final}>{textoProva}</span>{/if}
  </header>

  {#if !dados}
    <p class="suave">Carregando…</p>
  {:else if !painel.unidade && !dados.sessao}
    <PrimeirosPassos hrefImportar={montarHash({ tela: 'importar', uid })} />
  {:else}
    {#if dados.reta_final && prova}
      <section class="reta" aria-label="Reta final">
        <h2 class="rotulo">Reta final</h2>
        <p class="reta-linha">
          <span class="dias">{plural(prova.dias, 'dia', 'dias')}</span>
          <span>{plural(totalRevisar, 'questão para revisar', 'questões para revisar')}</span>
          {#if fracos.length}<span class="suave">mais erros em {fracos.map((t) => t.titulo).join(', ')}</span>{/if}
          <a class="acao-texto" href={href('formulario')}>Folha de fórmulas</a>
        </p>
      </section>
    {/if}

    <div class="colunas">
      <div class="principal">
        {#if sessao}
          <section class="sessao" aria-label={deHoje ? 'Sessão de hoje' : 'Próxima sessão'}>
            <h2 class="rotulo">
              {deHoje ? 'Sessão de hoje' : `Próxima sessão · ${dataCurta(sessao.data ?? '')}`} · {sessao.codigo}
              {#if sessao.estado === 'feita'}<span class="feita">feita</span>{/if}
            </h2>
            <h3 class="titulo">{sessao.titulo}</h3>
            {#if sessao.detalhe}<p class="suave detalhe">{sessao.detalhe}</p>{/if}
            {#if sessao.estado !== 'feita' && sessao.trabalhadas > 0}
              <p class="progresso-sessao">{sessao.trabalhadas} de {sessao.total} questões já trabalhadas</p>
            {/if}

            <dl class="material">
              {#each sessao.secoes as s (s.secao_id)}
                <dt>Livro</dt>
                <dd>
                  <button class="acao-texto" aria-label={`${s.codigo} no livro, página ${s.pagina_pdf_ini}`} onclick={() => abrirSecao(s, sessao.unidade)}>
                    {s.codigo} {s.titulo} · p. {s.pagina_pdf_ini}
                  </button>
                </dd>
              {/each}
              {#each sessao.resumos as r (r.id)}
                <dt>Resumo</dt>
                <dd><button class="acao-texto" aria-label={`Resumo: ${r.titulo}`} onclick={() => abrirResumo(r.id, sessao.unidade)}>{r.titulo}</button></dd>
              {/each}
              {#if sessao.formulas.length}
                <dt>Fórmulas</dt>
                <dd>
                  <a class="acao-texto" href={href('formulario', sessao.unidade)}>
                    {plural(sessao.formulas.length, 'fórmula', 'fórmulas')}{codigosSessao ? ` da ${codigosSessao}` : ''}
                  </a>
                </dd>
              {/if}
              {#if gruposSessao.length}
                <dt>Questões</dt>
                <dd class="questoes">
                  {#each gruposSessao as g, i (i)}
                    <span class="grupo">
                      <span class="suave lista">{g.lista}</span>
                      {#each g.questoes as q (q.id)}
                        <button class="numero {q.estado ?? ''}" class:resolvida={q.resolucao_id}
                          aria-label={rotuloQuestao(g.lista, q.rotulo, q.estado, !!q.resolucao_id)}
                          title={q.resolucao_id ? 'resolução gravada' : undefined}
                          onclick={() => abrirQuestao(q.id, q.unidade)}>{q.rotulo}</button>
                      {/each}
                    </span>
                  {/each}
                </dd>
              {/if}
            </dl>

            {#if acao}
              <button class="acao-forte comecar" onclick={() => abrirQuestao(acao.id, acao.unidade)}>{acao.rotulo}</button>
            {/if}
          </section>
        {:else}
          <section class="sessao" aria-label="Sessão">
            <p class="sem-sessao">Nenhuma sessão marcada no plano daqui para a frente.</p>
            <p class="suave">Crie as sessões no plano (data, foco e questões) e esta tela passa a mostrar a do dia.</p>
            <a class="acao-texto" href={href('cronograma')}>Abrir o plano</a>
          </section>
        {/if}

        <section class="revisar" aria-label="Para revisar">
          <h2 class="rotulo">Para revisar</h2>
          {#if dados.revisar.length}
            {#each dados.revisar as g (g.lista_id)}
              <div class="linha-revisar">
                <span class="nome">{g.lista_titulo}</span>
                {#if g.unidade !== dados.unidade}<span class="suave unidade">{nomeUnidade(g.unidade)}</span>{/if}
                <span class="numeros">
                  {#each g.questoes as q (q.id)}
                    <button class="numero {q.estado}" aria-label={rotuloQuestao(g.lista_codigo, q.rotulo, q.estado)}
                      onclick={() => abrirQuestao(q.id, g.unidade)}>{q.rotulo}</button>
                  {/each}
                </span>
              </div>
            {/each}
          {:else}
            <p class="suave">Nada para revisar.</p>
          {/if}
        </section>
      </div>

      <div class="lateral-hoje">
        <section aria-label="Próximos 7 dias">
          <h2 class="rotulo">Próximos 7 dias</h2>
          {#if dados.proximos.length}
            <ul class="proximos">
              {#each dados.proximos as item, i (i)}
                <li class:evento={item.tipo !== 'sessao'} class:prova-item={item.tipo === 'prova'}>
                  <span class="suave quando">{item.data === dados.data ? 'hoje' : dataCurta(item.data)}</span>
                  {#if item.tipo === 'sessao'}
                    <span class="codigo">{item.codigo}</span>
                    <span class="texto">{item.titulo}</span>
                    {#if item.estado !== 'feita' && item.trabalhadas > 0}<span class="estado" title="questões trabalhadas / questões da sessão">{item.trabalhadas}/{item.total}</span>
                    {:else if ESTADO_SESSAO[item.estado ?? '']}<span class="estado {item.estado}">{ESTADO_SESSAO[item.estado ?? '']}</span>{/if}
                  {:else}
                    <span class="codigo">{TIPO_EVENTO[item.tipo] ?? item.tipo}</span>
                    <span class="texto suave">{item.hora_inicio ?? ''} {item.titulo}</span>
                  {/if}
                </li>
              {/each}
            </ul>
          {:else}
            <p class="suave">Nada nos próximos dias.</p>
          {/if}
          <a class="acao-texto mais" href={href('cronograma')}>Plano completo →</a>
        </section>

        {#if dados.unidade}
          <section aria-label={`Tópicos da ${ordinal(dados.unidade)} unidade`}>
            <h2 class="rotulo">Tópicos da {ordinal(dados.unidade)} unidade</h2>
            <ul class="topicos">
              {#each dados.topicos as t (t.id)}
                <li>
                  <a class="nome-topico" href={montarHash({ tela: 'materia', uid, unidade: dados.unidade, area: 'topicos', topico: t.id })}>{t.titulo}</a>
                  <span class="estado-topico {CLASSE_ESTADO[t.estado] ?? ''}">{t.estado}</span>
                  {#if t.total}
                    <span class="placar suave" title="questões trabalhadas (marcadas ou com resolução) / questões ligadas">{t.trabalhadas}/{t.total}</span>
                    <span class="fio" aria-hidden="true">
                      <span class="feito" style:width={`${(100 * t.trabalhadas) / t.total}%`}></span>
                      {#if t.err + t.dub}<span class="erros" style:width={`${(100 * (t.err + t.dub)) / t.total}%`}></span>{/if}
                    </span>
                  {/if}
                </li>
              {/each}
            </ul>
          </section>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .hoje { display: grid; gap: 2rem; max-width: 76rem; }
  .cabeca { display: flex; align-items: baseline; flex-wrap: wrap; gap: 0.4rem 1.2rem; }
  h1 { font-size: 2.2rem; margin: 0; }
  .data { font-size: 0.95rem; }
  .prova { margin-left: auto; font-size: 0.95rem; }
  .prova.perto { color: var(--destaque-texto); font-weight: 500; }

  .colunas { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(17rem, 1fr); gap: 2.5rem 4rem; align-items: start; }
  .principal, .lateral-hoje { display: grid; grid-template-columns: minmax(0, 1fr); gap: 2.4rem; align-content: start; min-width: 0; }
  section { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0.6rem; align-content: start; min-width: 0; }
  h2.rotulo { margin: 0; font-family: var(--fonte-texto); font-weight: 400; display: flex; gap: 0.6rem; align-items: baseline; }
  .feita { color: var(--ok); letter-spacing: 0.12em; }
  .progresso-sessao { margin: 0; font-size: 0.95rem; }

  /* a sessão: o único bloco com peso de título */
  .sessao { gap: 0.5rem; }
  .titulo { font-size: 2rem; line-height: 1.15; margin: 0.15rem 0 0; font-weight: 500; }
  .detalhe { margin: 0; font-size: 1.02rem; }
  .material { display: grid; grid-template-columns: 6.5rem minmax(0, 1fr); gap: 0.55rem 1rem; margin: 1rem 0 0.4rem; padding-top: 1rem; border-top: 1px solid var(--fio); }
  dt { font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--suave); padding-top: 0.15rem; }
  dd { margin: 0; min-width: 0; }
  dd .acao-texto { color: var(--texto); text-align: left; }
  .questoes { display: flex; flex-wrap: wrap; gap: 0.4rem 1.6rem; }
  .grupo { display: inline-flex; flex-wrap: wrap; align-items: baseline; gap: 0.2rem 0.75rem; }
  .lista { font-size: 0.85rem; }
  .comecar { justify-self: start; margin-top: 0.6rem; padding: 0.4rem 1.2rem; }
  .sem-sessao { margin: 0; font-family: var(--fonte-titulo); font-size: 1.3rem; }

  /* números de questão: o mesmo gesto da grade de Praticar */
  .numero { background: none; border: 0; border-bottom: 2px solid transparent; padding: 0 2px; min-width: 1.4rem; font: inherit; font-variant-numeric: tabular-nums; color: var(--texto); cursor: pointer; }
  .numero:hover { color: var(--destaque-texto); }
  .numero.ok { color: var(--ok); border-bottom-color: var(--ok); }
  .numero.err { color: var(--err); border-bottom-color: var(--err); }
  .numero.dub { color: var(--dub-texto); border-bottom-color: var(--dub); }
  .numero.resolvida:not(.ok):not(.err):not(.dub) { border-bottom: 2px dotted var(--suave); }

  .revisar .linha-revisar { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.3rem 0.9rem; padding: 0.35rem 0; border-top: 1px solid var(--fio); }
  .revisar .linha-revisar:first-of-type { border-top: 0; }
  .nome { font-family: var(--fonte-titulo); font-size: 1.02rem; }
  .unidade { font-size: 0.85rem; }
  .numeros { display: inline-flex; flex-wrap: wrap; gap: 0.2rem 0.75rem; margin-left: auto; }

  ul { list-style: none; margin: 0; padding: 0; }
  .proximos li { display: grid; grid-template-columns: 4.6rem 2.6rem minmax(0, 1fr) auto; gap: 0.6rem; align-items: baseline; padding: 0.3rem 0; }
  .quando { font-size: 0.85rem; font-variant-numeric: tabular-nums; }
  .codigo { font-size: 0.85rem; font-variant-numeric: tabular-nums; }
  .texto { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .evento .codigo { grid-column: span 1; }
  .prova-item .codigo, .prova-item .quando { color: var(--destaque-texto); font-weight: 500; }
  .estado { font-size: 0.8rem; color: var(--suave); }
  .estado.feita { color: var(--ok); }
  .estado.hoje { color: var(--destaque-texto); }
  .mais { justify-self: start; font-size: 0.9rem; }

  .topicos li { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; grid-template-rows: auto auto; gap: 0.15rem 0.8rem; align-items: baseline; padding: 0.45rem 0; border-top: 1px solid var(--fio); }
  .topicos li:first-child { border-top: 0; }
  .nome-topico { text-decoration: none; min-width: 0; }
  .nome-topico:hover { text-decoration: underline; text-decoration-color: var(--destaque); text-underline-offset: 3px; }
  .estado-topico { font-size: 0.8rem; color: var(--suave); }
  .estado-topico.hoje { color: var(--destaque-texto); font-weight: 500; }
  .estado-topico.visto { color: var(--texto); }   /* aula passada, não domínio: sem o verde do acerto */
  .estado-topico.comecado { color: var(--texto); }
  .placar { font-size: 0.85rem; font-variant-numeric: tabular-nums; }
  .fio { grid-column: 1 / -1; position: relative; display: flex; height: 2px; background: var(--fio); }
  .fio .feito { background: var(--ok); }
  .fio .erros { background: var(--err); }

  .reta { padding-bottom: 1.2rem; border-bottom: 1px solid var(--fio); }
  .reta-linha { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.4rem 1.6rem; margin: 0; }
  .dias { font-family: var(--fonte-titulo); font-size: 1.8rem; color: var(--destaque); line-height: 1; }


  @media (max-width: 1100px) { .colunas { grid-template-columns: 1fr; } }
</style>
