<script lang="ts">
  import { untrack } from 'svelte'
  // Casa da matéria: a sessão do plano em foco, com o material a um clique; depois o que revisar (todas as unidades),
  // os próximos 7 dias e os tópicos com o progresso derivado no motor (spec 2026-11-05-redesenho-hoje-design).
  import { requisitar } from '../api/cliente'
  import type { Hoje, Painel, SecaoVinculada } from '../api/tipos'
  import { DEFINICAO_ESTADO, dataCurta, dataPorExtenso, nomeUnidade, ordinal } from '../apresentacao'
  import PrimeirosPassos from '../componentes/PrimeirosPassos.svelte'
  import { erro } from '../estado/avisos.svelte'
  import { abrirNoPainel } from '../estado/ia.svelte'
  import { pedido } from '../estado/pedido.svelte'
  import { montarHash, type Area } from './rota'

  let { painel, hoje = new Date() }: { painel: Painel; hoje?: Date } = $props()

  const uid = $derived(painel.materia.uid)
  let dados = $state<Hoje | null>(null)

  // o painel é relido depois de toda escrita (marcar, gravar…): a tela Hoje acompanha
  $effect(() => {
    void painel
    const pedida = painel.unidade
    // outra unidade (ou outra matéria): o que está na tela é da anterior, então some até a nova chegar
    // (lido sem rastrear: este efeito grava `dados`, e rastreá-lo faria cada resposta pedir outra)
    if (untrack(() => dados !== null && dados.unidade !== pedida)) dados = null
    const unidade = pedida === null ? '' : `?unidade=${pedida}`
    requisitar<Hoje>('GET', `/api/materias/${encodeURIComponent(uid)}/hoje${unidade}`).then((d) => { if (painel.unidade === pedida) dados = d }, erro)
  })

  const NOME_MARCA: Record<string, string> = { ok: 'acertei', err: 'errei', dub: 'dúvida' }
  const ESTADO_SESSAO: Record<string, string> = { feita: 'feita', passou: 'passou', hoje: 'hoje', futura: '' }
  const TIPO_EVENTO: Record<string, string> = {
    prova: 'Prova', aula: 'Aula', segunda_chamada: 'Segunda chamada', exame_final: 'Exame final', extra: 'Aula extra', feriado: 'Feriado',
  }

  const href = (area: Area, unidade: number | null = painel.unidade) => montarHash({ tela: 'materia', uid, unidade, area })
  const rotuloQuestao = (lista: string, rotulo: string, estado: string | null, resolvida = false) =>
    `${lista} #${rotulo}${estado ? `, ${NOME_MARCA[estado]}` : ''}${resolvida ? ', resolvida' : ''}`

  // uma questão da sessão abre Praticar dentro da sessão (a faixa com as questões dela, próxima e N por ela)
  function abrirQuestao(id: number, unidade: number, sessaoId: number | null = null) {
    location.hash = montarHash({ tela: 'materia', uid, unidade, area: 'listas', questao: id, sessao: sessaoId })
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
  const primeira = $derived(sessao?.questoes.find((q) => !q.trabalhada) ?? null)
  const primeiraRevisar = $derived(dados?.revisar[0] ? { id: dados.revisar[0].questoes[0].id, unidade: dados.revisar[0].unidade } : null)
  // a ação forte segue o estado: na reta final, revisar os erros; senão, a próxima questão da sessão; feita a sessão,
  // revisar os erros (ou nada, se não houver)
  const acao = $derived.by(() => {
    const revisar = primeiraRevisar && {
      rotulo: `Revisar ${plural(totalRevisar, 'questão marcada', 'questões marcadas')}`, ...primeiraRevisar, sessao: null,
    }
    if (dados?.reta_final && revisar) return revisar
    if (primeira) {
      return { rotulo: sessao && sessao.trabalhadas > 0 ? 'Continuar pelas questões' : 'Começar pelas questões', id: primeira.id,
        unidade: primeira.unidade, sessao: sessao?.id ?? null }
    }
    return revisar
  })
  const codigosSessao = $derived(sessao?.secoes.map((s) => s.codigo).join(', ') ?? '')

  // em Hoje só os tópicos que pedem algo agora (o de hoje e os de aula recente com pouca prática), até cinco; numa
  // unidade que já terminou, nenhum: a prova passou. A matéria inteira fica no mapa de Tópicos
  const paraCuidar = $derived(dados?.prova_passada ? [] : (dados?.topicos ?? [])
    .filter((t) => t.estado === 'hoje' || t.estado === 'falta praticar')
    .sort((a, b) => Number(b.estado === 'hoje') - Number(a.estado === 'hoje') || (b.ultima_aula ?? '').localeCompare(a.ultima_aula ?? ''))
    .slice(0, 5))
  // o que revisar: a unidade mostrada; as outras ficam recolhidas (a prova delas pode já ter passado)
  const revisarDaUnidade = $derived((dados?.revisar ?? []).filter((g) => g.unidade === dados?.unidade))
  const revisarOutras = $derived((dados?.revisar ?? []).filter((g) => g.unidade !== dados?.unidade))
  let verOutras = $state(false)
  const totalOutras = $derived(revisarOutras.reduce((t, g) => t + g.questoes.length, 0))
  // dica do ? uma vez só
  let dicaVista = $state(lerDica())
  function lerDica(): boolean {
    try { return localStorage.getItem('studia.dica-ajuda') === '1' } catch { return true }
  }
  function fecharDica() {
    dicaVista = true
    try { localStorage.setItem('studia.dica-ajuda', '1') } catch { /* segue */ }
  }

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
  const questoesAtrasadas = $derived((dados?.atrasadas ?? []).reduce((t, s) => t + s.faltam, 0))
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
    {#if painel.importacoes_pendentes > 0 && (dados.sessao || dados.tem_datas)}
      <p class="pendente">
        {painel.importacoes_pendentes === 1 ? '1 arquivo para conferir' : `${painel.importacoes_pendentes} arquivos para conferir`}
        <a class="acao-texto" href={montarHash({ tela: 'importar', uid })}>Conferir →</a>
      </p>
    {/if}
    {#if dados.reta_final && prova}
      <section class="reta" aria-label="Reta final">
        <h2 class="rotulo">Reta final</h2>
        <p class="reta-linha">
          <span class="dias">{plural(prova.dias, 'dia', 'dias')}</span>
          <span>{plural(totalRevisar, 'questão para revisar', 'questões para revisar')}</span>
          {#if fracos.length}<span class="suave">mais erros em {fracos.map((t) => t.titulo).join(', ')}</span>{/if}
          <a class="acao-texto" href={href('formulario')}>Folha de fórmulas</a>
          <button class="acao-texto" onclick={() => abrirNoPainel('geral', 'estrategista')}>Plano de revisão com a IA</button>
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
              <p class="progresso-sessao">{sessao.trabalhadas} de {sessao.total} questões já feitas</p>
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
                        <button class="numero {q.estado ?? ''}" class:resolvida={q.trabalhada && !q.estado}
                          aria-label={rotuloQuestao(g.lista, q.rotulo, q.estado, q.trabalhada && !q.estado)}
                          title={q.trabalhada && !q.estado ? 'resolvida por você' : undefined}
                          onclick={() => abrirQuestao(q.id, q.unidade, sessao.id)}>{q.rotulo}</button>
                      {/each}
                    </span>
                  {/each}
                </dd>
              {/if}
            </dl>

            {#if acao}
              <button class="acao-forte comecar" onclick={() => abrirQuestao(acao.id, acao.unidade, acao.sessao)}>{acao.rotulo}</button>
            {/if}
            {#if dados.atrasadas.length}
              <!-- sem culpa e sem fila de códigos: um número e um caminho; o plano mostra sessão por sessão -->
              <p class="atrasadas">
                <a class="acao-texto" href={href('cronograma')}
                  title={dados.atrasadas.map((s) => `${s.codigo} ${s.titulo} (${s.faltam})`).join(' · ')}>
                  {plural(questoesAtrasadas, 'questão ficou', 'questões ficaram')} de {plural(dados.atrasadas.length, 'sessão passada', 'sessões passadas')} →
                </a>
              </p>
            {/if}
          </section>
        {:else if dados.prova_passada}
          <section class="sessao" aria-label="Sessão">
            <p class="sem-sessao">A prova da {nomeUnidade(dados.unidade ?? 0)} foi na {dataCurta(dados.prova_passada, null)}.</p>
            <p class="suave">{revisarDaUnidade.length ? 'Esta unidade terminou: o que ficou para revisar está logo abaixo.' : 'Esta unidade terminou.'}</p>
            {#if dados.unidade_atual !== null && dados.unidade_atual !== dados.unidade}
              <a class="acao-suave comecar" href={href('painel', dados.unidade_atual)}>Ir para a {nomeUnidade(dados.unidade_atual)}</a>
            {/if}
          </section>
        {:else if !dados.tem_datas && painel.importacoes_pendentes > 0}
          <section class="sessao" aria-label="Sessão">
            <p class="sem-sessao">{plural(painel.importacoes_pendentes, 'arquivo espera', 'arquivos esperam')} conferência.</p>
            <p class="suave">Com o calendário conferido, o plano ganha datas e esta tela passa a mostrar a sessão do dia.</p>
            <a class="acao-suave comecar" href={montarHash({ tela: 'importar', uid })}>Conferir</a>
          </section>
        {:else if !dados.tem_datas}
          <section class="sessao" aria-label="Sessão">
            <p class="sem-sessao">Sem datas ainda.</p>
            <p class="suave">Com o calendário da turma, o plano ganha datas e esta tela passa a mostrar a sessão do dia.</p>
            <a class="acao-suave comecar" href={montarHash({ tela: 'importar', uid })}>Adicionar o calendário</a>
          </section>
        {:else}
          <section class="sessao" aria-label="Sessão">
            <p class="sem-sessao">Nenhuma sessão marcada no plano daqui para a frente.</p>
            <p class="suave">Crie as sessões no plano (data, foco e questões) e esta tela passa a mostrar a do dia.</p>
            <a class="acao-texto" href={href('cronograma')}>Abrir o plano</a>
          </section>
        {/if}

        {#if dados.tem_datas || dados.revisar.length}
        <section class="revisar" aria-label="Para revisar">
          <h2 class="rotulo">Para revisar</h2>
          {#if dados.revisar.length}
            {#if revisarDaUnidade.length === 0}<p class="suave">Nada para revisar nesta unidade.</p>{/if}
            {#each [...revisarDaUnidade, ...(verOutras ? revisarOutras : [])] as g (g.lista_id)}
              <div class="linha-revisar">
                <span class="nome"><span class="codigo-lista">{g.lista_codigo}</span> {g.lista_titulo}</span>
                {#if g.unidade !== dados.unidade}<span class="suave unidade">{nomeUnidade(g.unidade)}</span>{/if}
                <span class="numeros">
                  {#each g.questoes as q (q.id)}
                    <button class="numero {q.estado}" aria-label={rotuloQuestao(g.lista_codigo, q.rotulo, q.estado)}
                      title={q.enunciado || undefined} onclick={() => abrirQuestao(q.id, g.unidade)}>{q.rotulo}</button>
                  {/each}
                </span>
              </div>
            {/each}
            {#if totalOutras > 0}
              <button class="acao-texto outras" aria-expanded={verOutras} onclick={() => (verOutras = !verOutras)}>
                {verOutras ? 'Esconder as de outras unidades' : `De outras unidades (${totalOutras})`}
              </button>
            {/if}
          {:else}
            <p class="suave">Nada para revisar.</p>
          {/if}
        </section>
        {/if}
      </div>

      <div class="lateral-hoje">
        {#if (dados.tem_datas || dados.proximos.length) && !dados.prova_passada}
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
                    {#if item.estado !== 'feita' && item.trabalhadas > 0}<span class="estado" title="questões feitas / questões da sessão">{item.trabalhadas}/{item.total}</span>
                    {:else if item.data !== dados.data && ESTADO_SESSAO[item.estado ?? '']}<span class="estado {item.estado}">{ESTADO_SESSAO[item.estado ?? '']}</span>{/if}
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
        {/if}

        {#if dados.unidade && dados.tem_datas && !dados.prova_passada}
          <section aria-label="Tópicos para cuidar">
            <h2 class="rotulo">Tópicos para cuidar</h2>
            {#if paraCuidar.length === 0}
              <p class="suave">Tudo em dia nesta unidade.</p>
            {/if}
            <ul class="topicos">
              {#each paraCuidar as t (t.id)}
                <li>
                  <a class="nome-topico" href={montarHash({ tela: 'materia', uid, unidade: dados.unidade, area: 'topicos', topico: t.id })}>{t.titulo}</a>
                  {#if t.estado === 'hoje'}<span class="estado-topico hoje" title={DEFINICAO_ESTADO.hoje}>hoje</span>{:else}<span></span>{/if}
                  {#if t.total}
                    <span class="placar suave" title="questões trabalhadas (marcadas ou resolvidas por você) / questões ligadas">{t.trabalhadas}/{t.total}</span>
                    <!-- o fio: trabalhadas sem problema, depois as com ✗ ou ? (que já estão entre as trabalhadas) -->
                    <span class="fio" aria-hidden="true">
                      <span class="feito" style:width={`${(100 * Math.max(0, t.trabalhadas - t.err - t.dub)) / t.total}%`}></span>
                      {#if t.err + t.dub}<span class="erros" style:width={`${(100 * (t.err + t.dub)) / t.total}%`}></span>{/if}
                    </span>
                  {/if}
                </li>
              {/each}
            </ul>
            <a class="acao-texto mais" href={href('topicos', dados.unidade)}>Todos os tópicos da {ordinal(dados.unidade)} unidade →</a>
          </section>
        {/if}
      </div>
    </div>
    {#if !dicaVista}
      <p class="dica-ajuda suave" role="note">
        Dica: aperte <kbd>?</kbd> para ver os atalhos e o que quer dizer cada estado.
        <button class="acao-texto" onclick={fecharDica}>entendi</button>
      </p>
    {/if}
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
  .codigo-lista { font-family: var(--fonte-texto); font-size: 0.85rem; color: var(--suave); font-variant-numeric: tabular-nums; margin-right: 0.3rem; }
  .outras { justify-self: start; font-size: 0.9rem; margin-top: 0.3rem; }
  .pendente { margin: 0; display: flex; gap: 1rem; align-items: baseline; color: var(--destaque-texto); }
  .pendente .acao-texto { color: var(--texto); }
  .dica-ajuda { margin: 0; font-size: 0.9rem; display: flex; gap: 0.8rem; align-items: baseline; }
  .dica-ajuda kbd { font-family: var(--fonte-texto); padding: 0 0.35rem; border-radius: 4px; background: var(--leve); }
  .comecar { justify-self: start; margin-top: 0.6rem; padding: 0.4rem 1.2rem; }
  .atrasadas { margin: 0.5rem 0 0; display: flex; flex-wrap: wrap; gap: 0.2rem 0.6rem; align-items: baseline; font-size: 0.92rem; }
  .atrasadas .acao-texto { color: var(--texto); }
  .sem-sessao { margin: 0; font-family: var(--fonte-titulo); font-size: 1.3rem; }

  /* números de questão: o mesmo gesto da grade de Praticar */
  .numero { background: none; border: 0; border-bottom: 2px solid transparent; padding: 0 2px; min-width: 1.4rem; font: inherit; font-variant-numeric: tabular-nums; color: var(--texto); cursor: pointer; }
  .numero:hover { color: var(--destaque-texto); }
  .numero.ok { color: var(--ok); border-bottom-color: var(--ok); }
  .numero.err { color: var(--err); border-bottom: 3px double var(--err); }
  .numero.dub { color: var(--dub-texto); border-bottom: 2px dashed var(--dub); }
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
  .estado-topico.emdia { color: var(--ok); }
  .estado-topico.falta { color: var(--texto); font-weight: 500; }
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
