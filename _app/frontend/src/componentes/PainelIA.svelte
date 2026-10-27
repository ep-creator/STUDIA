<script lang="ts">
  // Painel do assistente: a conversa do alvo (questão, seção ou geral) com os atalhos por cima. A resposta chega aos
  // pedaços; citações viram links que abrem o PDF na página ou o texto; o que o agente grava aparece com Abrir e
  // Desfazer; o custo fica no rodapé. Sem chave do Gemini, o painel oferece colar a chave e "Copiar o contexto".
  import { requisitar } from '../api/cliente'
  import { conversar, type EventoAgente } from '../api/agente'
  import type { ConversaSaida, EstadoAgente, FonteResumo, GrupoHistorico, PacoteContexto, PedidoAgente } from '../api/tipos'
  import { avisar, erro } from '../estado/avisos.svelte'
  import { desfazer } from '../estado/desfazer'
  import { ia } from '../estado/ia.svelte'
  import { estadoMateria } from '../estado/materia.svelte'
  import { pedido } from '../estado/pedido.svelte'
  import { montarHash } from '../rotas/rota'
  import ConfigurarChave from './ConfigurarChave.svelte'
  import Markdown from './Markdown.svelte'

  let { uid, alvo, papel, atalhos }: { uid: string; alvo: string; papel: string; atalhos: string[] } = $props()

  const NOMES: Record<string, string> = {
    N1: 'N1 Dica', N2: 'N2 Caminho', N3: 'N3 Esboço', N4: 'N4 Resolução', resumir: 'Resumir a seção', plano: 'Plano de revisão',
  }
  type Gravado = { tipo: string; id: number; titulo: string; grupo_id: number; historico?: boolean }
  type Item = { autor: string; texto: string; gravado?: Gravado }

  let itens = $state<Item[]>([])
  let estado = $state<EstadoAgente | null>(null)
  let respondendo = $state(false)
  let aviso = $state<string | null>(null)       // o que a ferramenta está fazendo
  let ultimoCusto = $state<number | null>(null)
  let confirmar = $state<{ pedido: PedidoAgente; total: number; teto: number } | null>(null)
  let falha = $state<{ texto: string; pedido: PedidoAgente } | null>(null)
  let escrita = $state('')
  let fontes: FonteResumo[] | null = null
  let corrente: AbortController | null = null   // a resposta em andamento; trocar de alvo a corta

  const reais = (v: number) => `R$ ${v.toFixed(2).replace('.', ',')}`

  async function carregar() {
    try {
      const c = await requisitar<ConversaSaida>('GET', `/api/materias/${uid}/agente/conversa?alvo=${encodeURIComponent(alvo)}&papel=${papel}`)
      itens = c.mensagens.map((m) => ({ autor: m.autor, texto: m.texto }))
      estado = await requisitar<EstadoAgente>('GET', '/api/agente/estado')
    } catch {
      itens = []   // motor desligado ou matéria sem as tabelas ainda: o painel fica vazio, sem quebrar a tela
    }
  }

  $effect(() => {
    void alvo
    void papel
    corrente?.abort()
    corrente = null
    respondendo = false
    aviso = null
    confirmar = null
    falha = null
    void carregar().then(() => {
      if (ia.pendente && ia.alvo === alvo) {
        const atalho = ia.pendente
        ia.pendente = null
        void enviar({ alvo, papel: papel as PedidoAgente['papel'], atalho: atalho as PedidoAgente['atalho'], confirmado: false })
      }
    })
  })

  function aoEvento(e: EventoAgente) {
    const ultimo = itens.at(-1)
    if (e.tipo === 'texto') {
      if (ultimo?.autor === 'agente' && respondendo) ultimo.texto += e.dados.texto
      else itens.push({ autor: 'agente', texto: e.dados.texto })
      aviso = null
    } else if (e.tipo === 'ferramenta') {
      aviso = e.dados.aviso
    } else if (e.tipo === 'gravado') {
      itens.push({ autor: 'ferramenta', texto: `${e.dados.titulo} salva`, gravado: e.dados })
      itens.push({ autor: 'agente', texto: '' })
    } else if (e.tipo === 'confirmar') {
      confirmar = null
    } else if (e.tipo === 'fim') {
      ultimoCusto = e.dados.custo_brl
      if (estado) estado.total_mes = e.dados.total_mes
    }
  }

  async function enviar(p: PedidoAgente) {
    if (respondendo) return
    const controle = new AbortController()
    corrente = controle
    respondendo = true
    falha = null
    confirmar = null
    itens.push({ autor: 'voce', texto: p.texto ?? NOMES[p.atalho ?? ''] ?? '' })
    itens.push({ autor: 'agente', texto: '' })
    try {
      await conversar(uid, p, (e) => {
        if (controle.signal.aborted) return   // resposta de outra questão: não entra nesta conversa
        if (e.tipo === 'confirmar') confirmar = { pedido: p, total: e.dados.total_mes, teto: e.dados.teto }
        else if (e.tipo === 'erro') falha = { texto: textoDoErro(e.dados.motivo, e.dados.detalhe), pedido: p }
        else aoEvento(e)
      }, controle.signal)
    } catch (e) {
      if (controle.signal.aborted) return
      falha = { texto: e instanceof Error ? e.message : String(e), pedido: p }
    } finally {
      if (corrente === controle) corrente = null
      if (!controle.signal.aborted) {   // cortada: a troca de alvo já zerou o painel
        respondendo = false
        aviso = null
        itens = itens.filter((i) => i.autor !== 'agente' || i.texto)   // tira a bolha vazia de quem não chegou a responder
      }
    }
  }

  function textoDoErro(motivo: string, detalhe: string): string {
    if (motivo === 'sem_chave') {
      if (estado) estado.chave_configurada = false
      return 'Falta configurar a chave do Gemini.'
    }
    if (motivo === 'chave_invalida') return 'O Gemini recusou a chave. Confira a chave configurada.'
    if (motivo === 'ocupado') return detalhe
    if (motivo === 'pedido_invalido') return `O Gemini recusou o pedido: ${detalhe}`
    if (motivo === 'resposta_invalida') return `O Gemini mandou uma resposta que não consegui ler (${detalhe}).`
    if (motivo === 'interno' || motivo === 'alvo') return `Algo deu errado no app: ${detalhe}`
    return `Não consegui falar com o Gemini (${motivo === 'limite_de_uso' ? 'limite de uso' : motivo === 'tempo_esgotado' ? 'demorou demais' : 'fora do ar'}).`
  }

  const atalho = (a: string) => void enviar({ alvo, papel: papel as PedidoAgente['papel'], atalho: a as PedidoAgente['atalho'], confirmado: false })

  function mandar(e: SubmitEvent) {
    e.preventDefault()
    const texto = escrita.trim()
    if (!texto) return
    escrita = ''
    void enviar({ alvo, papel: papel as PedidoAgente['papel'], texto, confirmado: false })
  }

  async function recomecar() {
    try {
      const c = await requisitar<ConversaSaida>('POST', `/api/materias/${uid}/agente/conversa/recomecar`, { alvo, papel })
      itens = c.mensagens.map((m) => ({ autor: m.autor, texto: m.texto }))
      ultimoCusto = null
    } catch (e) {
      erro(e)
    }
  }

  async function copiarContexto() {
    try {
      const r = await requisitar<PacoteContexto>('GET',
        `/api/materias/${uid}/agente/contexto?alvo=${encodeURIComponent(alvo)}&papel=${papel}${atalhos[0] ? `&atalho=${atalhos[0]}` : ''}`)
      await navigator.clipboard.writeText(r.texto)
      avisar('Contexto copiado: cole num chat de IA')
    } catch (e) {
      erro(e)
    }
  }

  // O Histórico só desfaz a última ação: o Desfazer daqui vale enquanto a gravação do agente for a última.
  async function desfazerGravado(g: Gravado) {
    try {
      const [topo] = await requisitar<GrupoHistorico[]>('GET', `/api/materias/${uid}/historico?limite=1`)
      if (topo?.id === g.grupo_id && !topo.desfeito_em) await desfazer()
      else g.historico = true
    } catch (e) {
      erro(e)
    }
  }

  function abrirGravado(g: Gravado) {
    if (g.tipo === 'documento') pedido.documento = g.id
    location.hash = montarHash({ tela: 'materia', uid, unidade: estadoMateria.unidade, area: g.tipo === 'documento' ? 'documentos' : 'formulario' })
  }

  // [Stewart p. 312], [Stewart 14.1 exercício 22 p. 312], [resumo 14.1 Polares], [resolução Resolução L1-3]
  const CITACAO = /\[((?:[^\]\n]+? p\. \d+)|(?:resumo|resolução) [^\]\n]+)\](?!\()/g
  const comLinks = (texto: string) => texto.replace(CITACAO, (_, r: string) => `[${r}](#citar:${encodeURIComponent(r)})`)

  async function abrirCitacao(rotulo: string) {
    const pagina = rotulo.match(/^(.*?)(?: \S+ exercício \d+)? p\. (\d+)$/)
    if (pagina) {
      fontes ??= await requisitar<FonteResumo[]>('GET', `/api/materias/${uid}/fontes`).catch(() => [])
      const nome = pagina[1].trim()
      const f = fontes.find((x) => (x.titulo || x.caminho.split('/').pop()?.replace(/\.pdf$/i, '')) === nome)
      if (!f) return avisar(`Não achei "${nome}" entre os arquivos da matéria`)
      pedido.fonte = { id: f.id, pagina: Number(pagina[2]) }
    } else {
      const titulo = rotulo.replace(/^(resumo|resolução) /, '')
      const d = estadoMateria.painel?.documentos.find((x) => x.titulo === titulo)
      if (!d) return avisar(`Não achei o texto "${titulo}"`)
      pedido.documento = d.id
    }
    location.hash = montarHash({ tela: 'materia', uid, unidade: estadoMateria.unidade, area: 'documentos' })
  }

  function clicar(e: MouseEvent) {
    const link = (e.target as HTMLElement).closest?.('a[href^="#citar:"]')
    if (!link) return
    e.preventDefault()
    void abrirCitacao(decodeURIComponent(link.getAttribute('href')!.slice('#citar:'.length)))
  }
</script>

<!-- o clique só é delegado aos links de citação (que já são <a> com teclado próprio) -->
<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions, a11y_no_noninteractive_element_interactions -->
<section class="painel-ia" aria-label="Assistente" onclick={clicar}>
  <header>
    <div class="atalhos">
      {#each atalhos as a (a)}
        <button class="botao" disabled={respondendo} onclick={() => atalho(a)}>{NOMES[a] ?? a}</button>
      {/each}
    </div>
    <div class="acoes">
      <button class="botao discreto" onclick={() => void copiarContexto()}>Copiar o contexto</button>
      <button class="botao discreto" disabled={respondendo || !itens.length} onclick={() => void recomecar()}>Recomeçar</button>
    </div>
  </header>

  {#if estado && !estado.chave_configurada}
    <ConfigurarChave onsalvo={() => void carregar()} />
  {/if}

  <div class="conversa" aria-live="polite">
    {#each itens as item, i (i)}
      {#if item.gravado}
        {@const g = item.gravado}
        <div class="gravado" role="status">
          <span>✓ {item.texto}</span>
          <button class="botao discreto" onclick={() => abrirGravado(g)}>Abrir</button>
          {#if g.historico}
            <a class="botao discreto" href={montarHash({ tela: 'historico', uid })}>Abrir o Histórico</a>
          {:else}
            <button class="botao discreto" onclick={() => void desfazerGravado(g)}>Desfazer</button>
          {/if}
        </div>
      {:else if item.autor === 'voce'}
        <p class="voce">{item.texto}</p>
      {:else if item.autor === 'agente' && item.texto}
        <div class="agente"><Markdown texto={comLinks(item.texto)} /></div>
      {/if}
    {/each}
    {#if aviso}<p class="suave aviso">{aviso}</p>{:else if respondendo}<p class="suave aviso">Pensando…</p>{/if}
    {#if confirmar}
      {@const c = confirmar}
      <div class="alerta" role="alert">
        <p>Esta resposta passaria do teto de {reais(c.teto)} no mês (já foram {reais(c.total)}).</p>
        <button class="botao primario" onclick={() => void enviar({ ...c.pedido, confirmado: true })}>Continuar</button>
        <button class="botao" onclick={() => (confirmar = null)}>Cancelar</button>
      </div>
    {/if}
    {#if falha}
      {@const f = falha}
      <div class="alerta" role="alert">
        <p>{f.texto}</p>
        <button class="botao" onclick={() => { itens = itens.slice(0, -1); void enviar(f.pedido) }}>Tentar de novo</button>
      </div>
    {/if}
  </div>

  <form onsubmit={mandar}>
    <textarea aria-label="Mensagem para o assistente" placeholder="Pergunte sobre o que está aberto…" bind:value={escrita} rows="2"
      onkeydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); (e.currentTarget.form as HTMLFormElement).requestSubmit() } }}></textarea>
    <button class="botao primario" type="submit" disabled={respondendo || !escrita.trim()}>Enviar</button>
  </form>
  <footer class="suave">
    {#if ultimoCusto !== null}Esta resposta: {reais(ultimoCusto)} · {/if}{#if estado}mês: {reais(estado.total_mes)} de {reais(estado.teto)}{/if}
  </footer>
</section>

<style>
  .painel-ia { display: flex; flex-direction: column; gap: 0.6rem; min-height: 0; }
  header { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.4rem; }
  .atalhos, .acoes { display: flex; flex-wrap: wrap; gap: 0.3rem; }
  .discreto { font-size: 0.8rem; padding: 0.15rem 0.5rem; }
  .conversa { display: flex; flex-direction: column; gap: 0.6rem; overflow-y: auto; min-height: 4rem; max-height: 60vh; }
  .voce { margin: 0; align-self: flex-end; max-width: 85%; background: var(--realce); padding: 0.4rem 0.65rem; border-radius: 10px; white-space: pre-wrap; }
  .agente { line-height: 1.55; overflow-wrap: anywhere; }
  .gravado { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; font-size: 0.88rem; border-left: 2px solid var(--ok); padding-left: 0.5rem; }
  .gravado span { margin-right: auto; }
  .aviso { margin: 0; font-size: 0.85rem; font-style: italic; }
  .alerta { border-left: 2px solid var(--destaque); padding: 0.4rem 0.6rem; background: var(--realce); border-radius: 6px; display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }
  .alerta p { margin: 0; flex-basis: 100%; }
  form { display: flex; gap: 0.4rem; align-items: flex-end; }
  textarea { flex: 1; resize: vertical; border: 1px solid var(--borda); border-radius: 6px; padding: 0.35rem 0.5rem; background: var(--fundo); color: var(--texto); font: inherit; }
  footer { font-size: 0.78rem; }
</style>
