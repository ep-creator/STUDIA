<script lang="ts">
  // Atalhos e ajuda (tecla ?): o que cada área faz, as teclas, o que querem dizer os estados e os códigos da tela.
  // Curto de propósito: o guia completo fica em docs/guia.md.
  import { tick } from 'svelte'
  import guiaBruto from '../../../../docs/guia.md?raw'
  import Markdown from './Markdown.svelte'

  let { onfechar }: { onfechar: () => void } = $props()
  let caixa: HTMLElement
  // o guia completo abre aqui mesmo (o app é local: sem depender de internet); as imagens ficam de fora
  const GUIA = (() => {
    const inicio = Math.max(0, guiaBruto.indexOf('## As telas da matéria'))
    const fim = guiaBruto.indexOf('## Problemas comuns')
    const linhas = guiaBruto.slice(inicio, fim > inicio ? fim : undefined).split(/\r?\n/).filter((l) => !l.trim().startsWith('<img'))
    // o arquivo quebra as linhas à mão (~120 colunas) e o Markdown do app respeita quebras: rejunta cada parágrafo e
    // cada item de lista (a continuação de um item vem recuada)
    const saida: string[] = []
    for (const l of linhas) {
      const anterior = saida.at(-1) ?? ''
      const continua = l.trim() !== '' && anterior.trim() !== '' && !/^\s*([-*#>|]|\d+\.)/.test(l) && !/^#/.test(anterior)
      if (continua) saida[saida.length - 1] = `${anterior.trimEnd()} ${l.trim()}`
      else saida.push(l)
    }
    return saida.join('\n')
  })()
  let guia = $state(false)

  $effect(() => {
    const antes = document.activeElement as HTMLElement | null
    void tick().then(() => caixa?.focus())
    return () => antes?.focus?.()
  })

  const TECLAS: [string, string][] = [
    ['Ctrl K', 'buscar no conteúdo ou ir para uma área, unidade, tópico ou questão (ex.: 14.1 46)'],
    ['Alt 1 · 2 · 3 · 4', 'Hoje · Tópicos · Praticar · Biblioteca'],
    ['Alt I', 'abrir ou fechar a IA da matéria'],
    ['1 · 2 · 3 · 0', 'em Praticar: acertei · errei · dúvida · limpar, na questão aberta'],
    ['N', 'em Praticar: a próxima questão ainda não feita'],
    ['setas', 'na grade de Praticar: andar entre as questões'],
    ['Ctrl Z', 'desfazer a última alteração'],
    ['?', 'esta ajuda'],
  ]
  const ESTADOS: [string, string][] = [
    ['feita', 'todas as questões da sessão foram marcadas ou resolvidas por você'],
    ['2 de 3', 'sessão começada: questões feitas de quantas tem'],
    ['hoje', 'o tópico é o da sessão do dia'],
    ['a seguir', 'a aula do tópico ainda não chegou'],
    ['em dia', 'a aula já passou e você fez metade ou mais das questões'],
    ['falta praticar', 'a aula já passou e você fez menos da metade das questões'],
    ['prova passou', 'a unidade terminou; o tópico não cobra mais nada'],
  ]
  const CODIGOS: [string, string][] = [
    ['S3, P1', 'sessão do plano de estudo (S de sessão, P de preparação)'],
    ['14.1, 15.4', 'seção do livro; a lista com o mesmo código é a dos exercícios dela'],
    ['L5', 'lista da turma (Lista 5)'],
    ['principais · reforço', 'as duas linhas de questões de cada lista'],
    ['✓ ✗ ?', 'acertei, errei, dúvida; nos números, traço cheio, duplo e tracejado'],
  ]
</script>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape') { e.preventDefault(); onfechar() } }} />

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div class="fundo" onclick={onfechar}></div>
<div class="ajuda" role="dialog" aria-modal="true" aria-labelledby="ajuda-titulo" tabindex="-1" bind:this={caixa}>
  <header>
    <h2 id="ajuda-titulo">{guia ? 'Guia de uso' : 'Atalhos e ajuda'}</h2>
    <button class="acao-texto" aria-label="Fechar a ajuda" onclick={onfechar}>✕</button>
  </header>
  {#if guia}
    <div class="guia leitura-medida"><Markdown texto={GUIA} rebaixar={1} /></div>
    <p class="rodape"><button class="acao-texto" onclick={() => (guia = false)}>← Atalhos e ajuda</button></p>
  {:else}
  <div class="colunas">
    <section aria-label="Teclas">
      <h3 class="rotulo">Teclas</h3>
      <dl>{#each TECLAS as [tecla, oque] (tecla)}<dt><kbd>{tecla}</kbd></dt><dd>{oque}</dd>{/each}</dl>
    </section>
    <section aria-label="Estados">
        <h3 class="rotulo">Estados</h3>
        <dl>{#each ESTADOS as [nome, oque] (nome)}<dt>{nome}</dt><dd>{oque}</dd>{/each}</dl>
      </section>
    <section aria-label="Códigos">
      <h3 class="rotulo">Códigos</h3>
      <dl>{#each CODIGOS as [nome, oque] (nome)}<dt>{nome}</dt><dd>{oque}</dd>{/each}</dl>
    </section>
  </div>
  <p class="suave rodape">As áreas: <b>Hoje</b> (a sessão do dia), <b>Tópicos</b> (uma página por tópico), <b>Praticar</b> (as listas) e <b>Biblioteca</b> (resumos e PDFs). <button class="acao-texto" onclick={() => { guia = true; caixa?.scrollTo?.({ top: 0 }) }}>Guia completo de uso</button></p>
  {/if}
</div>

<style>
  .fundo { position: fixed; inset: 0; z-index: 60; background: rgb(0 0 0 / 35%); }
  .ajuda {
    position: fixed; z-index: 61; top: 6vh; left: 50%; transform: translateX(-50%); width: min(74rem, calc(100vw - 2rem));
    max-height: 84vh; overflow-y: auto; padding: 1.4rem 1.6rem; background: var(--lateral); color: var(--texto);
    border-radius: 10px; box-shadow: 0 24px 60px rgb(0 0 0 / 35%);
  }
  .ajuda:focus { outline: none; }
  header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 0.8rem; }
  h2 { margin: 0; font-size: 1.5rem; }
  .colunas { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 2rem; }
  section { margin-bottom: 1.2rem; }
  h3.rotulo { margin: 0 0 0.5rem; font-family: var(--fonte-texto); font-weight: 400; }
  dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 0.35rem 0.8rem; margin: 0; font-size: 0.92rem; }
  dt { font-weight: 500; white-space: nowrap; }
  dd { margin: 0; color: var(--suave); }
  kbd { font-family: var(--fonte-texto); font-size: 0.88rem; padding: 0.05rem 0.4rem; border-radius: 4px; background: var(--leve); }
  .rodape { margin: 0.4rem 0 0; font-size: 0.92rem; }
  .guia { font-size: 0.98rem; line-height: 1.6; }
  @media (max-width: 900px) { .colunas { grid-template-columns: 1fr; } }
</style>
