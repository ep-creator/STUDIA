<script lang="ts">
  // Matéria vazia: o que soltar e o que o app monta com cada arquivo, em três passos, e um único botão para começar.
  // Nada aqui depende de IA: cada PDF é lido por regras e o que o app não tiver certeza vem para conferir.
  let { hrefImportar }: { hrefImportar: string } = $props()

  const PASSOS: [string, string][] = [
    ['O programa da disciplina', 'vira as unidades e os tópicos de cada uma.'],
    ['O calendário da turma', 'traz as datas das aulas e das provas.'],
    ['Os livros e as listas', 'viram as seções para ler e as questões para praticar.'],
  ]
</script>

<section class="passos" aria-label="Primeiros passos">
  <h2>Esta matéria ainda está vazia</h2>
  <p class="suave intro">Solte os PDFs da disciplina, em qualquer ordem. Nada é gravado sem você conferir.</p>
  <ol>
    {#each PASSOS as [arquivo, resultado], i (arquivo)}
      <li><span class="n" aria-hidden="true">{i + 1}</span><span><b>{arquivo}</b> {resultado}</span></li>
    {/each}
  </ol>
  <a class="acao-forte" href={hrefImportar}>＋ Adicionar material</a>
  <p class="suave depois">Com as datas no lugar, esta tela passa a mostrar a sessão do dia, o que revisar e a prova.</p>
</section>

<style>
  .passos { display: grid; gap: 0.9rem; justify-items: start; max-width: 38rem; }
  h2 { font-size: 1.6rem; margin: 0; }
  p { margin: 0; }
  .intro { font-size: 1.02rem; }
  ol { list-style: none; margin: 0.4rem 0 0.6rem; padding: 0; display: grid; gap: 0.7rem; }
  li { display: grid; grid-template-columns: 2rem minmax(0, 1fr); align-items: baseline; gap: 0.4rem; font-size: 1.02rem; }
  .n { font-family: var(--fonte-titulo); font-size: 1.4rem; color: var(--destaque); line-height: 1; }
  b { font-weight: 500; }
  .acao-forte { padding: 0.4rem 1.2rem; }
  .depois { font-size: 0.92rem; }
</style>
