<script lang="ts">
  import { requisitar } from '../api/cliente'
  import type { MateriaCriada, ResumoMateria } from '../api/tipos'
  import CartaoMateria from '../componentes/CartaoMateria.svelte'
  import EstadoVazio from '../componentes/EstadoVazio.svelte'
  import { erro } from '../estado/avisos.svelte'
  import { montarHash } from './rota'

  let { materias }: { materias: ResumoMateria[] } = $props()

  let criando = $state(false)
  let nome = $state('')

  async function criar(evento: SubmitEvent) {
    evento.preventDefault()
    try {
      const nova = await requisitar<MateriaCriada>('POST', '/api/materias', { nome: nome.trim() })
      location.hash = montarHash({ tela: 'importar', uid: nova.uid })
    } catch (e) {
      erro(e)
    }
  }
</script>

<div class="materias">
  <header>
    <h1>Suas matérias</h1>
    <button class="botao primario" onclick={() => (criando = true)}>＋ Nova matéria</button>
  </header>

  {#if criando}
    <form class="cartao nova" onsubmit={criar}>
      <label>Nome <input bind:value={nome} required placeholder="Ex.: Cálculo 2" /></label>
      <button class="botao primario" type="submit" disabled={!nome.trim()}>Criar</button>
      <button class="botao" type="button" onclick={() => (criando = false)}>Cancelar</button>
      <p class="suave">Depois de criar, é só soltar os PDFs (programa, calendário, livros, listas) na importação.</p>
    </form>
  {/if}

  {#if materias.length === 0 && !criando}
    <EstadoVazio texto="Nenhuma matéria ainda. Crie a primeira: dê um nome e solte os PDFs." />
  {/if}
  <div class="grade">
    {#each materias as m (m.uid)}<CartaoMateria materia={m} />{/each}
  </div>
</div>

<style>
  .materias { max-width: 60rem; margin: 0 auto; padding: 2rem 1.5rem; }
  header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
  .nova { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; margin-bottom: 1.5rem; }
  .nova input { margin-left: 0.5rem; padding: 0.3rem 0.5rem; border: 1px solid var(--borda); border-radius: 6px; background: var(--fundo); }
  .nova p { flex-basis: 100%; margin: 0; }
  .grade { display: grid; grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr)); gap: 1rem; }
</style>
