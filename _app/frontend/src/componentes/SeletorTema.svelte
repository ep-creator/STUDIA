<script lang="ts">
  import { escolherTema, tema, type Identidade, type Modo } from '../estado/tema.svelte'
  import Seletor from './Seletor.svelte'

  const IDENTIDADES = [{ valor: 'editorial', rotulo: 'Editorial' }, { valor: 'padrao', rotulo: 'Padrão' }]
  const MODOS = [{ valor: 'sistema', rotulo: 'Seguir o sistema' }, { valor: 'claro', rotulo: 'Claro' }, { valor: 'escuro', rotulo: 'Escuro' }]
</script>

<div class="tema">
  <span class="rotulo">Tema</span>
  <Seletor rotulo="Identidade visual" opcoes={IDENTIDADES} valor={tema.identidade} onmudar={(v) => escolherTema(v as Identidade, tema.modo)} variante="compacto" />
  <Seletor rotulo="Claro ou escuro" opcoes={MODOS} valor={tema.modo} onmudar={(v) => escolherTema(tema.identidade, v as Modo)} variante="compacto" />
</div>

<style>
  .tema { display: grid; gap: 0.35rem; }
  /* no rodapé da barra lateral a lista abre para cima */
  .tema :global(.opcoes) { top: auto; bottom: calc(100% + 4px); }
</style>
