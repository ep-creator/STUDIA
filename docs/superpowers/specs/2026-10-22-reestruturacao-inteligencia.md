# Reestruturação da Inteligência — Documento de Trabalho (Fase 6)

> Documento vivo. Junta o que já foi decidido e discutido sobre **como a plataforma "pensa"**: classificação de arquivos,
> ligações entre tópicos, seções e listas, busca e uso de modelos de IA. Ele é a base da discussão da **Fase 6**, que
> deixa de ser só "adaptar o agente" e passa a cobrir toda a camada de inteligência do projeto.
> Nada aqui está implementado além do que a seção 2 descreve como "hoje".

## 1. Princípios (já decididos)

1. **Regras primeiro, IA onde for necessário.** Criar e organizar uma matéria não pode depender de IA; modelos entram para
   funções inteligentes (tutor, resumos, decisões difíceis), não para o que uma regra resolve.
2. **Nada de valor chutado.** Toda decisão automática tem origem e nota de confiança; abaixo do limiar, ela é proposta e
   marcada para revisão, nunca gravada como certa.
3. **Medir antes de trocar.** Uma tecnologia nova só substitui a atual se ganhar num gabarito de casos reais, com custo
   medido no hardware do usuário.
4. **Local e barato por padrão.** O que roda a cada busca ou importação deve rodar offline no notebook. API paga
   (principalmente **Gemini**) só para o que precisa de raciocínio.
5. **Trocas isoladas.** Cada peça de inteligência tem um único ponto de entrada no código, para trocar a técnica sem
   mexer no resto.

## 2. Como funciona hoje (fim da Fase 4 + correções da importação)

| Peça | Técnica atual | Onde está |
|---|---|---|
| Tipo do arquivo | Pontos por sinais no texto (datas, "Unidade", sumário, "Questão 1."…) | `estudos/importacao/classificador.py` |
| Estrutura (unidades, tópicos, provas, seções, questões) | Parsers por regras explícitas | `estudos/importacao/parsers/` |
| Ligações tópico↔seção, lista↔tópico, livro↔livro, referência↔livro | Semelhança de texto (Jaccard ponderado por IDF sobre radicais) | `estudos/importacao/vinculo.py` (único ponto de pontuação) |
| Radical das palavras | Singular + sufixos, com mínimos de tamanho | `estudos/importacao/idioma.py` → `radical()` |
| Busca | BM25 do SQLite FTS5 com radical como prefixo; filtros exatos de unidade/seção/tipo | `estudos/rag/` |
| Agente (tutor, resumidor, estrategista) | Gemini com function calling, ainda no app legado | `Calculo 2/_app/` (legado) |

### 2.1 Sistema de confiança

Toda decisão recebe uma nota de 0 a 1. Dois limites em `_app/config.toml`:

- `limiar_vinculo = 0.35`: abaixo disso a ligação nem é proposta;
- `limiar_confianca = 0.75`: abaixo disso o item é proposto com `"revisar": true` (as "pendências" da importação).

As notas vêm de quatro cálculos:

1. **Tipo do arquivo:** `(pontos do 1º − pontos do 2º) ÷ pontos do 1º`, a folga do vencedor. Exemplo real: no
   calendário, calendário 6 e programa 2 dão 0,67, que pede revisão.
2. **Semelhança entre textos:** cada texto vira um conjunto de radicais, sem palavras comuns;
   `peso(radicais em comum) ÷ peso(todos os radicais dos dois)`, com peso `IDF = log(1 + N/df)` entre os candidatos (raro
   pesa mais). Empate numa escolha única corta a nota pela metade.
3. **Unidade de uma lista:**
   - unidade escrita no título dá 1,0;
   - senão, cada conteúdo vota em cada unidade com a nota do tópico mais parecido dela (basta metade do limiar para votar),
     e a seção do livro já ligada a um tópico vota com peso 1;
   - vence a maior soma;
   - confiança = `fatia da vencedora × vínculo mais forte dela`.

   Exemplo real (Lista 1): unidade 1 com 0,29 + 0,50 = 0,79 e unidade 2 com 0,545, o que dá unidade 1 com confiança
   0,30 (certa, mas marcada para revisão).
4. **Seções do livro:** 1,0 com sumário embutido; menor quando o sumário impresso precisou de correção de OCR.

Propostas pendentes são **recalculadas** ao ler e ao confirmar (a ordem dos envios não muda o resultado), e as decisões da
revisão sobrevivem ao recálculo: vínculo recusado, vínculo incluído à mão, unidade, seção ou papel escolhidos.

### 2.2 Limitações conhecidas

- **Palavras, não significado.** Exemplo: "Funções de duas variáveis" se parece mais, em palavras, com "Integração em duas
  variáveis" do que com "Funções de várias variáveis". Por isso a confiança soma várias evidências e marca o que for
  inseguro.
- **Busca só acha quem usa as mesmas palavras.** Termos exatos (jacobiano → 15.10, Clairaut → 14.3, centro de massa → 15.5,
  Lagrange → 14.8) funcionam muito bem. Perguntas com outras palavras ("volume de um sólido de revolução") não.
- **Fórmulas extraídas de PDF viram texto bagunçado** ("x2 + y2"). Isso afeta qualquer técnica baseada em texto.
- **O radical é uma regra fixa:** algumas formas de verbo não casam com o substantivo ("calcular" × "cálculo").

## 3. Opções discutidas

### 3.1 Embeddings locais

Um modelo pequeno transforma cada texto num vetor que representa o significado; textos parecidos têm vetores próximos.

**Hardware do usuário** (medido em 2026-10-22): Intel Core Ultra 7 155H (16 núcleos / 22 threads), 16 GB de RAM, Intel Arc
integrada (sem NVIDIA), 170 GB livres. Modelos pequenos e médios rodam bem só no processador.

**Custos estimados, ainda não medidos** (Cálculo 2 tem 2.232 trechos):

| Modelo (multilíngue) | Tamanho | Indexar a matéria (uma vez) | Por busca | Observação |
|---|---|---|---|---|
| `multilingual-e5-small` | ~118 M parâmetros, ~0,1–0,5 GB | ~0,5–2 min | ~10–30 ms | candidato principal |
| `multilingual-e5-base` | ~278 M | ~2–3× o small | ~30–60 ms | se o small perder em qualidade |
| `bge-m3` | ~568 M, ~2 GB de RAM | ~10 min | mais lento | pesado demais para o notebook |

- **Vetores:** ~3,4 MB por matéria (384 dimensões × 4 bytes × 2.232).
- **Comparação:** força bruta, menos de 1 ms (poucos ms mesmo com 100 mil trechos); não precisa de banco vetorial.
- **Atualização:** só os trechos alterados geram vetor de novo, aproveitando as assinaturas do índice atual.
- **Para rodar:** uma biblioteca leve (ONNX Runtime ou equivalente) em vez de PyTorch, para não pesar a instalação. Se
  algum dia valer a pena, a GPU Arc ou a NPU do processador podem ser usadas via OpenVINO.

### 3.2 Busca híbrida

BM25 (busca atual) e embeddings rodam juntos, e os rankings são combinados por **Reciprocal Rank Fusion**
(`soma de 1 / (k + posição)` em cada ranking). Fica com o melhor dos dois: nomes exatos pelo BM25, paráfrases pelos
vetores. É a hipótese principal para a busca.

### 3.3 Embeddings nos vínculos da importação

Usar o mesmo modelo em `vinculo.py`, como segunda nota de semelhança (por significado) ao lado da nota por palavras.
Resolveria o caso "duas variáveis". O sistema de confiança continua igual: muda só de onde vem a nota.

### 3.4 Gemini como segunda opinião

Só para itens que ficaram com `"revisar": true`: mandar o item e os candidatos ao Gemini e mostrar a sugestão dele na tela
de revisão, com origem `agente`. Mantém o princípio 1, porque a IA entra só onde a regra ficou insegura, com custo
proporcional às dúvidas e não ao volume.

### 3.5 Combinação provável

Regras quando a confiança é alta; embeddings para desempatar e para a busca; Gemini só para o que continuar inseguro.

## 4. Plano de avaliação (antes de qualquer troca)

1. **Gabarito de busca:** 30 a 40 perguntas sobre o Cálculo 2, cada uma com a seção esperada; metade com termos exatos,
   metade com outras palavras.
2. **Gabarito de vínculos:** os tópicos do programa com a seção correta do Stewart e a unidade correta de cada lista
   (L1–L6 e as listas por seção).
3. **Comparar:** BM25 atual × só embeddings × híbrida; regras × regras+embeddings nos vínculos.
4. **Métricas:**
   - seção certa entre os 5 primeiros (recall@5) e posição média da resposta certa (MRR);
   - acertos de unidade e de vínculo;
   - tempo para indexar uma matéria, tempo por busca e memória usada.
5. **Ambiente:** separado do motor, sem mudar o projeto; o modelo é baixado do Hugging Face (120–470 MB).
6. **Decisão pelos números:** se a híbrida ganhar com custo aceitável, entra no índice existente.

## 5. Como encaixaria na arquitetura

- **Índice:** coluna de vetor (BLOB) na tabela `trecho` de `<matéria>/.indice/indice.db`. Continua 100% derivável e fora
  do Git; mudar de modelo muda a versão do índice, que é refeito sozinho.
- **Busca:** `estudos/rag/busca.py` ganha a fusão dos rankings; a API `GET /busca` não muda (o frontend da Fase 5 não é
  afetado).
- **Vínculos:** `estudos/importacao/vinculo.py` passa a combinar as duas notas; limiares continuam no `config.toml`.
- **Config:** novas chaves para o modelo (nome, ligado/desligado), para o usuário poder desligar os embeddings e voltar às
  regras puras.

## 6. Ligação com o agente (Fase 6)

- O agente atual (Gemini + function calling) passa a usar as ferramentas sobre os repositórios e a busca nova, em vez de
  ler os arquivos do legado.
- **A busca híbrida beneficia o agente diretamente:** perguntas do aluno raramente usam as palavras do livro.
- **A discutir com o usuário na Fase 6:** o que muda na interação com a IA (redesenho que estava fora do escopo da
  refatoração), custos e limites de uso, e onde mais a segunda opinião do Gemini faz sentido.

## 7. Perguntas em aberto

- Qual modelo de embeddings vence no gabarito (small × base)? A qualidade em português técnico de matemática justifica o
  base?
- A busca híbrida deve ser o padrão ou uma opção?
- Vale tratar fórmulas à parte (por exemplo, normalizar "x2" para "x²" antes de indexar)?
- A segunda opinião do Gemini roda automaticamente nos itens marcados ou só quando o usuário pede?
- O que mais o agente deve fazer além de tutor, resumidor e estrategista?
