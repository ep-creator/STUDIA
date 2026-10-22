<script lang="ts">
  import { escolherTema, tema, type Identidade, type Modo } from '../estado/tema.svelte'
</script>

<div class="tema">
  <label>
    <span class="rotulo">Tema</span>
    <select
      aria-label="Identidade visual"
      value={tema.identidade}
      onchange={(e) => escolherTema(e.currentTarget.value as Identidade, tema.modo)}
    >
      <option value="editorial">Editorial</option>
      <option value="padrao">Padrão</option>
    </select>
  </label>
  <select aria-label="Claro ou escuro" value={tema.modo} onchange={(e) => escolherTema(tema.identidade, e.currentTarget.value as Modo)}>
    <option value="sistema">Seguir o sistema</option>
    <option value="claro">Claro</option>
    <option value="escuro">Escuro</option>
  </select>
</div>

<style>
  .tema { display: grid; gap: 0.35rem; }
  label { display: grid; gap: 0.2rem; }
  select { background: var(--cartao); border: 1px solid var(--borda); border-radius: 6px; padding: 0.2rem 0.4rem; }
</style>
