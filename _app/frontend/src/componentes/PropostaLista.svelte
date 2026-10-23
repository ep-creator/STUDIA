<script lang="ts">
  import type { PropostaLista } from '../api/proposta'
  import { explicarUnidadeLista } from '../confianca'
  import SeloConfianca from './SeloConfianca.svelte'
  import Seletor from './Seletor.svelte'

  let { proposta, unidades, alterar }: {
    proposta: PropostaLista
    unidades: number[]
    alterar: (mudar: (p: PropostaLista) => void) => void
  } = $props()

  const temExistente = $derived(proposta.listas.some((l) => l.existente))
</script>

{#if proposta.avisos.length}
  <ul class="avisos">{#each proposta.avisos as a (a)}<li>⚠ {a}</li>{/each}</ul>
{/if}
{#if proposta.conteudos.length}
  <p class="suave">Conteúdos: {proposta.conteudos.join(' · ')}</p>
{/if}
{#if temExistente}
  <div class="modo">
    Listas que já existem:
    <Seletor rotulo="Listas que já existem" valor={proposta.modo} onmudar={(v) => alterar((p) => (p.modo = v as PropostaLista['modo']))}
      opcoes={[{ valor: 'mesclar', rotulo: 'mesclar (mantém marcações e questões que já existem)' }, { valor: 'substituir', rotulo: 'substituir pelas questões deste arquivo' }]} />
  </div>
{/if}

{#each proposta.listas as item, i (item.codigo)}
  <section class="item">
    <h4>{item.titulo} <span class="suave">· {item.codigo} · {item.questoes.length} questões</span></h4>
    {#if item.existente}
      <p class="suave">Já existe: {item.existente.novas.length} novas, {item.existente.mantidas.length} mantidas, {item.existente.ausentes.length} ausentes neste arquivo.</p>
    {/if}
    <div class="linha">
      <div class="campo-unidade">
        <span>Unidade</span>
        <Seletor
          rotulo={`Unidade da lista ${item.codigo}`}
          variante="compacto"
          opcoes={unidades.map((n) => ({ valor: String(n), rotulo: `${n}ª unidade` }))}
          valor={item.unidade.numero === null ? null : String(item.unidade.numero)}
          onmudar={(v) => alterar((p) => { p.listas[i].unidade.numero = Number(v); p.listas[i].unidade.revisar = false })}
        />
      </div>
      <SeloConfianca item={item.unidade} porque={explicarUnidadeLista(item)} />
    </div>
    {#if item.topicos.length}
      <div class="topicos">
        <span class="rotulo">Tópicos ligados</span>
        {#each item.topicos as t, j (t.topico_id)}
          <label class="vinculo">
            <input type="checkbox" checked={t.aceito} onchange={(e) => alterar((p) => Object.assign(p.listas[i].topicos[j], { aceito: e.currentTarget.checked, revisar: false }))} />
            {t.titulo} <SeloConfianca item={t} />
          </label>
        {/each}
      </div>
    {/if}
  </section>
{/each}

<style>
  .avisos { margin: 0 0 0.75rem; padding-left: 1rem; color: var(--suave); }
  .modo { display: grid; gap: 0.25rem; max-width: 30rem; margin-bottom: 0.75rem; }
  .campo-unidade { display: flex; align-items: center; gap: 0.5rem; min-width: 12rem; }
  .item { border-top: 1px solid color-mix(in srgb, var(--borda) 30%, transparent); padding: 0.75rem 0; }
  h4 { margin: 0 0 0.4rem; font-family: var(--fonte-titulo); font-weight: 500; }
  .linha { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
  .topicos { display: grid; gap: 0.2rem; margin-top: 0.5rem; }
  .vinculo { display: flex; gap: 0.4rem; align-items: center; }
</style>
