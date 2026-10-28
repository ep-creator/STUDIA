<script lang="ts">
  // Cabeçalho da proposta de importação: o tipo, a troca de tipo ("tipo: lista ⌄") e, só quando o palpite é duvidoso,
  // um "conferir" em amarelo com a confiança e o porquê no title.
  import { NOME_TIPO, TIPOS_ARQUIVO } from '../api/proposta'
  import { corDoSelo, numeroPt } from '../confianca'
  import Seletor from './Seletor.svelte'

  let { tipo, classificacao, ontrocar }: {
    tipo: string
    classificacao: { tipo: string; confianca: number; revisar: boolean }
    ontrocar: (tipo: string) => void
  } = $props()

  const duvidoso = $derived(corDoSelo(classificacao) !== 'certo')
</script>

<header>
  <h3>{NOME_TIPO[tipo] ?? tipo}</h3>
  {#if duvidoso}
    <span class="conferir" title={`confiança ${numeroPt(classificacao.confianca)} · pelo texto do arquivo (datas, unidades, sumário, questões…); se estiver errado, troque o tipo`}>conferir</span>
  {/if}
  <span class="tipo">
    <Seletor rotulo="tipo" variante="compacto" valor={tipo} onmudar={ontrocar}
      opcoes={TIPOS_ARQUIVO.map((t) => ({ valor: t, rotulo: NOME_TIPO[t] }))} />
  </span>
</header>

<style>
  header { display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
  h3 { margin: 0; font-size: 1.3rem; }
  .conferir { color: var(--dub); font-size: 0.85rem; }
  .tipo { margin-left: auto; font-size: 0.85rem; color: var(--suave); }
</style>
