<script lang="ts">
  import type { PropostaLista } from '../api/proposta'
  import { explicarUnidadeLista } from '../confianca'
  import SeloConfianca from './SeloConfianca.svelte'

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
  <label class="modo">
    Listas que já existem:
    <select value={proposta.modo} onchange={(e) => alterar((p) => (p.modo = e.currentTarget.value as PropostaLista['modo']))}>
      <option value="mesclar">mesclar (mantém marcações e questões que já existem)</option>
      <option value="substituir">substituir pelas questões deste arquivo</option>
    </select>
  </label>
{/if}

{#each proposta.listas as item, i (item.codigo)}
  <section class="item">
    <h4>{item.titulo} <span class="suave">· {item.codigo} · {item.questoes.length} questões</span></h4>
    {#if item.existente}
      <p class="suave">Já existe: {item.existente.novas.length} novas, {item.existente.mantidas.length} mantidas, {item.existente.ausentes.length} ausentes neste arquivo.</p>
    {/if}
    <div class="linha">
      <label>
        Unidade
        <select
          aria-label={`Unidade da lista ${item.codigo}`}
          value={item.unidade.numero === null ? '' : String(item.unidade.numero)}
          onchange={(e) => alterar((p) => (p.listas[i].unidade.numero = e.currentTarget.value ? Number(e.currentTarget.value) : null))}
        >
          <option value="">escolha…</option>
          {#each unidades as n (n)}<option value={String(n)}>{n}ª unidade</option>{/each}
        </select>
      </label>
      <SeloConfianca item={item.unidade} porque={explicarUnidadeLista(item)} />
    </div>
    {#if item.topicos.length}
      <div class="topicos">
        <span class="rotulo">Tópicos ligados</span>
        {#each item.topicos as t, j (t.topico_id)}
          <label class="vinculo">
            <input type="checkbox" checked={t.aceito} onchange={(e) => alterar((p) => (p.listas[i].topicos[j].aceito = e.currentTarget.checked))} />
            {t.titulo} <SeloConfianca item={t} />
          </label>
        {/each}
      </div>
    {/if}
  </section>
{/each}

<style>
  .avisos { margin: 0 0 0.75rem; padding-left: 1rem; color: var(--suave); }
  .modo { display: block; margin-bottom: 0.75rem; }
  .item { border-top: 1px solid color-mix(in srgb, var(--borda) 30%, transparent); padding: 0.75rem 0; }
  h4 { margin: 0 0 0.4rem; font-family: var(--fonte-titulo); font-weight: 500; }
  .linha { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
  .topicos { display: grid; gap: 0.2rem; margin-top: 0.5rem; }
  .vinculo { display: flex; gap: 0.4rem; align-items: center; }
  select { background: var(--cartao); border: 1px solid var(--borda); border-radius: 6px; padding: 0.15rem 0.3rem; }
</style>
