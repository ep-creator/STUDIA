<script lang="ts">
  import { requisitar } from '../api/cliente'
  import { type PropostaCalendario, type PropostaLista, type PropostaLivro, type PropostaOutro,
    type PropostaPrograma, type PropostaTurma } from '../api/proposta'
  import type { ImportacaoSaida, Painel, ResumoImportacao } from '../api/tipos'
  import FilaImportacao from '../componentes/FilaImportacao.svelte'
  import PropostaCalendarioView from '../componentes/PropostaCalendario.svelte'
  import PropostaListaView from '../componentes/PropostaLista.svelte'
  import PropostaLivroView from '../componentes/PropostaLivro.svelte'
  import PropostaProgramaView from '../componentes/PropostaPrograma.svelte'
  import PropostaTurmaView from '../componentes/PropostaTurma.svelte'
  import CabecalhoProposta from '../componentes/CabecalhoProposta.svelte'
  import { avisar, erro } from '../estado/avisos.svelte'
  import { desfazer } from '../estado/desfazer'
  import { recarregar } from '../estado/materia.svelte'
  import { EdicaoProposta } from '../estado/revisao'

  let { painel }: { painel: Painel } = $props()

  const uid = $derived(painel.materia.uid)
  const base = $derived(`/api/materias/${uid}/importacoes`)
  let selecionada = $state<number | null>(null)
  let imp = $state<ImportacaoSaida | null>(null)
  let versao = $state(0)
  let indexando = $state(false)

  // Opções de unidade para as listas: as que existem e mais uma (a lista pode abrir uma unidade nova)
  const unidades = $derived.by(() => {
    const ns = painel.unidades.map((u) => u.numero)
    const maior = Math.max(0, ...ns)
    return [...new Set([...ns, maior + 1])].sort((a, b) => a - b)
  })

  let edicao: EdicaoProposta<Record<string, unknown>> | null = null

  function abrir(r: ImportacaoSaida) {
    imp = r
    const id = r.id
    // Edições em fila: a tela muda na hora e cada PUT leva todas as mudanças feitas até ali
    edicao = new EdicaoProposta(r.proposta, async (proposta) => {
      const salvo = await requisitar<ImportacaoSaida>('PUT', `${base}/${id}`, proposta)
      if (imp?.id === id) imp = { ...salvo, proposta: edicao!.proposta }   // mantém o que já foi editado depois
      versao++
    }, (e) => {
      erro(e)
      requisitar<ImportacaoSaida>('GET', `${base}/${id}`).then((atual) => { if (selecionada === id) abrir(atual) }, erro)
    })
  }

  $effect(() => {
    const id = selecionada
    imp = null
    edicao = null
    if (id === null) return
    requisitar<ImportacaoSaida>('GET', `${base}/${id}`).then((r) => { if (selecionada === id) abrir(r) }, erro)
  })

  /** Edita a proposta (o motor guarda as decisões da revisão). */
  function alterar<T>(mudar: (p: T) => void) {
    if (!imp || !edicao) return
    void edicao.alterar(mudar as unknown as (p: Record<string, unknown>) => void)
    imp = { ...imp, proposta: edicao.proposta }
  }

  async function trocarTipo(tipo: string) {
    if (!imp) return
    try {
      abrir(await requisitar<ImportacaoSaida>('POST', `${base}/${imp.id}/tipo`, { tipo }))
      versao++
    } catch (e) {
      erro(e)
    }
  }

  function resumir(r: ResumoImportacao): string {
    const partes = [
      [r.unidades, 'unidades'], [r.topicos, 'tópicos'], [r.eventos, 'eventos'], [r.secoes, 'seções'], [r.listas, 'listas'],
      [r.questoes, 'questões'], [r.vinculos, 'vínculos'], [r.criterios, 'critérios'],
    ].filter(([n]) => (n as number) > 0).map(([n, nome]) => `${n} ${nome}`)
    return partes.length ? `Importado: ${partes.join(', ')}` : 'Importado (nada novo)'
  }

  async function confirmar() {
    if (!imp) return
    const atual = imp
    try {
      await edicao?.esperar()   // a última edição da revisão precisa chegar ao motor antes de confirmar
      const r = await requisitar<ResumoImportacao>('POST', `${base}/${atual.id}/confirmar`)
      avisar(resumir(r), { rotulo: 'Desfazer', executar: () => void desfazer().then(() => versao++) })
      selecionada = null
      versao++
      await recarregar()
      if (atual.tipo === 'livro') {
        indexando = true
        await requisitar('POST', `/api/materias/${uid}/busca/sincronizar`).then(() => avisar('Livro pronto para a busca'), erro)
        indexando = false
      }
    } catch (e) {
      erro(e)
    }
  }

  async function descartar() {
    if (!imp) return
    try {
      await requisitar('POST', `${base}/${imp.id}/descartar`)
      selecionada = null
      versao++
    } catch (e) {
      erro(e)
    }
  }
</script>

<h2>Importar</h2>
{#if indexando}<p class="suave" role="status">Indexando o livro para a busca…</p>{/if}

<div class="importacao">
  <FilaImportacao {uid} {selecionada} onselecionar={(id) => (selecionada = id)} {versao} onmudou={() => void recarregar()} />

  <section class="proposta">
    {#if imp}
      {@const p = imp.proposta as { classificacao: { tipo: string; confianca: number; revisar: boolean } }}
      <CabecalhoProposta tipo={imp.tipo} classificacao={p.classificacao} ontrocar={trocarTipo} />

      {#if imp.tipo === 'lista'}
        <PropostaListaView proposta={imp.proposta as PropostaLista} {unidades} alterar={alterar<PropostaLista>} />
      {:else if imp.tipo === 'programa'}
        <PropostaProgramaView proposta={imp.proposta as PropostaPrograma} alterar={alterar<PropostaPrograma>} />
      {:else if imp.tipo === 'livro'}
        <PropostaLivroView proposta={imp.proposta as PropostaLivro} alterar={alterar<PropostaLivro>} />
      {:else if imp.tipo === 'calendario'}
        <PropostaCalendarioView proposta={imp.proposta as PropostaCalendario} />
      {:else if imp.tipo === 'turma'}
        <PropostaTurmaView proposta={imp.proposta as PropostaTurma} />
      {:else}
        <p class="suave">{(imp.proposta as PropostaOutro).observacao}</p>
      {/if}

      <footer>
        <button class="acao-forte" onclick={confirmar}>Confirmar</button>
        <button class="acao-texto" onclick={descartar}>descartar</button>
        {#if imp.pendencias > 0}<span class="pendencias">{imp.pendencias} para conferir</span>{/if}
      </footer>
    {:else}
      <p class="suave">Escolha um arquivo da fila.</p>
    {/if}
  </section>
</div>

<style>
  .importacao { display: grid; grid-template-columns: minmax(20rem, 28rem) minmax(0, 1fr); gap: 2.4rem; align-items: start; }
  .importacao > :global(*) { min-width: 0; }
  .proposta { position: sticky; top: 1rem; max-height: calc(100vh - 2rem); overflow-y: auto; border-left: 1px solid var(--fio); padding-left: 2rem; }
  footer { display: flex; gap: 1.1rem; align-items: center; margin-top: 1.25rem; }
  .pendencias { color: var(--dub); font-size: 0.85rem; }
</style>
