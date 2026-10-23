<script lang="ts">
  import type { PropostaLivro } from '../api/proposta'
  import SeloConfianca from './SeloConfianca.svelte'
  import Seletor from './Seletor.svelte'

  let { proposta, alterar }: { proposta: PropostaLivro; alterar: (mudar: (p: PropostaLivro) => void) => void } = $props()

  const duvidosas = $derived(proposta.secoes.filter((s) => s.revisar))
  let verTodas = $state(false)
</script>

{#if proposta.sem_texto}
  <p class="alerta">⚠ Este PDF parece escaneado (sem texto): ele entra, mas não aparece na busca.</p>
{/if}
{#if proposta.avisos.length}<ul class="suave">{#each proposta.avisos as a (a)}<li>⚠ {a}</li>{/each}</ul>{/if}

<dl>
  <dt>Obra</dt><dd>{proposta.titulo_obra}</dd>
  <dt>Papel</dt>
  <dd>
    <Seletor rotulo="Papel do livro" variante="compacto" valor={proposta.papel} onmudar={(v) => alterar((p) => (p.papel = v as PropostaLivro['papel']))}
      opcoes={[{ valor: 'principal', rotulo: 'principal (o livro da disciplina)' }, { valor: 'complementar', rotulo: 'complementar' }]} />
  </dd>
  <dt>Seções</dt><dd>{proposta.secoes.length} ({proposta.origem === 'sumario_embutido' ? 'sumário do próprio PDF' : proposta.origem === 'sumario_embutido_sem_codigo' ? 'sumário do PDF, códigos pela ordem' : 'sumário lido do texto'}){#if duvidosas.length} · {duvidosas.length} para conferir{/if}</dd>
  <dt>Páginas</dt><dd>{proposta.offset_pagina === null ? 'não consegui alinhar a numeração impressa' : `página impressa + ${-proposta.offset_pagina} = página do PDF`}</dd>
  <dt>Respostas</dt><dd>{proposta.gabarito ? `páginas ${proposta.gabarito[0]}–${proposta.gabarito[1]} do PDF` : 'não encontradas'}</dd>
</dl>

<button class="botao" onclick={() => (verTodas = !verTodas)}>{verTodas ? 'Esconder seções' : 'Ver seções'}</button>
{#if verTodas}
  <ol class="secoes">
    {#each proposta.secoes as s (s.codigo)}
      <li class:duvida={s.revisar} style:padding-left={`${(s.nivel - 1) * 1}rem`}>{s.codigo} {s.titulo} <span class="suave">p. {s.pagina_pdf_ini}–{s.pagina_pdf_fim}</span></li>
    {/each}
  </ol>
{/if}

{#if proposta.topicos.length}
  <h4>Tópicos do programa ligados a este livro</h4>
  <div class="vinculos">
    {#each proposta.topicos as t, i (`${t.topico_id}-${t.codigo}`)}
      <label>
        <input type="checkbox" checked={t.aceito} onchange={(e) => alterar((p) => Object.assign(p.topicos[i], { aceito: e.currentTarget.checked, revisar: false }))} />
        {t.titulo} → {t.codigo} <SeloConfianca item={t} />
      </label>
    {/each}
  </div>
{/if}
{#if proposta.equivalencias.length}
  <p class="suave">{proposta.equivalencias.length} seções equivalentes às do livro principal.</p>
{/if}

<style>
  .alerta { color: var(--err); }
  dl { display: grid; grid-template-columns: 7rem 1fr; gap: 0.25rem 0.75rem; margin: 0.5rem 0 1rem; }
  dt { color: var(--suave); }
  dd { margin: 0; }
  .secoes { max-height: 16rem; overflow: auto; list-style: none; padding: 0; font-size: 0.9rem; }
  .duvida { background: color-mix(in srgb, var(--dub) 30%, transparent); }
  .vinculos { display: grid; gap: 0.2rem; }
  label { display: flex; gap: 0.4rem; align-items: center; }
  h4 { margin: 1rem 0 0.4rem; font-family: var(--fonte-titulo); font-weight: 500; }
</style>
