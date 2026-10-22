<script lang="ts">
  import { analisarRota, type Rota } from './rotas/rota'

  let rota = $state<Rota>(analisarRota(location.hash))

  $effect(() => {
    const atualizar = () => (rota = analisarRota(location.hash))
    window.addEventListener('hashchange', atualizar)
    return () => window.removeEventListener('hashchange', atualizar)
  })
</script>

<main>
  <p>Plataforma de Estudos — {rota.tela}</p>
</main>
