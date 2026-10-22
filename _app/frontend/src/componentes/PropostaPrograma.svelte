<script lang="ts">
  import type { PropostaPrograma, TopicoProposto } from '../api/proposta'
  import SeloConfianca from './SeloConfianca.svelte'

  let { proposta, alterar }: { proposta: PropostaPrograma; alterar: (mudar: (p: PropostaPrograma) => void) => void } = $props()

  // Caminho do tópico dentro da proposta: [unidade, tópico, filho, filho…]
  function noTopico(p: PropostaPrograma, caminho: number[]): TopicoProposto {
    let t = p.unidades[caminho[0]].topicos[caminho[1]]
    for (const k of caminho.slice(2)) t = t.filhos[k]
    return t
  }
</script>

{#snippet arvore(topicos: TopicoProposto[], caminho: number[])}
  <ul>
    {#each topicos as t, k (t.titulo + k)}
      <li>
        <span class="titulo">{t.titulo}</span>
        {#if t.existente_id}<span class="suave">(já existe)</span>{/if}
        {#each t.secoes as s, j (s.secao_id)}
          <label class="secao">
            <input
              type="checkbox"
              checked={s.aceito}
              aria-label={`Ligar ${t.titulo} à seção ${s.codigo}`}
              onchange={(e) => alterar((p) => Object.assign(noTopico(p, [...caminho, k]).secoes[j], { aceito: e.currentTarget.checked, revisar: false }))}
            />
            {s.codigo} <SeloConfianca item={s} />
          </label>
        {/each}
        {#if t.filhos.length}{@render arvore(t.filhos, [...caminho, k])}{/if}
      </li>
    {/each}
  </ul>
{/snippet}

{#each proposta.unidades as u, i (u.numero)}
  <section>
    <h4>{u.titulo || `${u.numero}ª unidade`} {#if u.existente_id}<span class="suave">· já existe, os tópicos novos entram nela</span>{/if}</h4>
    {@render arvore(u.topicos, [i])}
  </section>
{/each}
{#if proposta.unidades.length === 0}
  <p class="suave">Não encontrei unidades neste arquivo. Ele é mesmo o programa? Use "Tipo errado?" acima.</p>
{/if}

<style>
  section { border-top: 1px solid color-mix(in srgb, var(--borda) 30%, transparent); padding: 0.6rem 0; }
  h4 { margin: 0 0 0.3rem; font-family: var(--fonte-titulo); font-weight: 500; }
  ul { list-style: none; margin: 0; padding-left: 1rem; }
  li { padding: 0.15rem 0; }
  .titulo { margin-right: 0.4rem; }
  .secao { display: inline-flex; gap: 0.25rem; align-items: center; margin-left: 0.5rem; font-size: 0.85rem; }
</style>
