# Fase 6 · Peça B — Busca melhor (embeddings, busca híbrida e busca na interface)

> Primeira peça da Fase 6. Base: `2026-10-20-refatoracao-plataforma-design.md` (§8 RAG, §11 Fases) e
> `2026-10-22-reestruturacao-inteligencia.md` (§3–§5). As outras peças (A. assistente, C. segunda opinião na importação,
> D. geração de material) terão specs próprias.

## 1. Objetivo e critério de sucesso

Melhorar como o STUDIA encontra coisas, **medindo antes de trocar**:

- uma **busca na interface** (Ctrl K) que procura na matéria inteira e abre o resultado no lugar certo;
- **embeddings locais** como candidatos para a busca (busca híbrida) e para os vínculos da importação;
- um **comando de avaliação** com gabaritos revisados pelo usuário, que decide por números o que entra.

Sucesso:

1. existe uma tabela com números (atual × candidatos) para busca e vínculos, registrada em `docs/avaliacoes/`;
2. a busca da interface acha o que se procura também quando a pergunta usa palavras diferentes das do livro (se a
   híbrida ganhar) ou, no mínimo, acha pelo texto como hoje;
3. indexar uma matéria leva menos de 10 minutos e uma busca responde em menos de 300 ms no notebook do usuário
   (Core Ultra 7 155H, 16 núcleos, 15,5 GB de RAM, sem GPU dedicada).

## 2. Decisões

| Tema | Decisão |
|---|---|
| Ordem na Fase 6 | Peça B primeiro (escolha do usuário) |
| Gabarito | Rascunho do Claude (~40 perguntas do Cálculo 2), revisado e completado pelo usuário |
| Escopo | Busca **e** vínculos da importação; cada um só muda se ganhar no seu gabarito |
| Interface | Inclui a busca na interface (paleta com Ctrl K) |
| Execução dos embeddings | `fastembed` (ONNX Runtime, só CPU, sem PyTorch) |
| Vetores | Coluna `vetor BLOB` na tabela `trecho` do índice; comparação em memória com NumPy |
| Fusão | Reciprocal Rank Fusion com k = 60 fixo |
| Treinamento | **Nenhum.** O modelo vem pronto; o gabarito só escolhe técnica, modelo e limiares |
| Padrão até haver números | `busca = "texto"` e vínculos só por regra (comportamento atual) |

### 2.1 Por que juntar texto e sentido

- **Busca atual (BM25 do FTS5 sobre radicais) e vínculos atuais (Jaccard com IDF):** casam **palavras iguais**. São
  exatos e explicáveis: acertam números de seção, termos raros e notação ("15.4", "Jacobiano").
- **Falha das duas:** paráfrase. Exemplo real, na ordenação dos documentos, que usa o mesmo princípio: o resumo
  "14.7 Valores máximo e mínimo" não casa com os tópicos
  "Pontos críticos e ponto de sela" e "Extremos absolutos em região fechada", porque não há palavra em comum.
- **Embeddings:** um modelo pronto transforma cada texto num vetor de números, e textos de mesmo sentido ficam
  próximos mesmo sem palavras em comum.
- **Fraquezas dos embeddings:** são piores com termos exatos e notação, leem só ~512 tokens por trecho e não explicam
  o resultado.
- **A híbrida:** como as duas técnicas erram em lugares diferentes, a fusão costuma ganhar das duas. A avaliação mede as
  três (texto, vetor, híbrida) e só a vencedora entra.

## 3. Motor

### 3.1 Componentes

```text
estudos/
├── ia/embeddings.py        interface Embeddings + FastEmbed (único ponto de troca do provedor)
├── rag/indice.py           trecho.vetor BLOB; modelo e dimensão registrados em `estado`; VERSAO_INDICE sobe para 2
├── rag/indexador.py        gera vetores dos trechos novos/alterados, em lotes
├── rag/busca.py            buscar(..., modo) com "texto" (BM25 atual), "vetor" e "hibrida" (RRF)
├── importacao/vinculo.py   nota combinada regra + sentido (só se ligada); continua o único ponto de pontuação
└── avaliacao/              gabaritos + `python -m estudos.avaliacao`
```

### 3.2 Interface de embeddings

```python
class Embeddings(Protocol):
    nome: str          # ex.: "intfloat/multilingual-e5-small"
    dimensao: int      # ex.: 384
    def de_trechos(self, textos: list[str]) -> np.ndarray: ...   # matriz n × dimensao, linhas normalizadas
    def de_consulta(self, texto: str) -> np.ndarray: ...         # vetor normalizado
```

- `FastEmbed` implementa a interface. Para modelos e5, aplica os prefixos exigidos (`passage: ` nos trechos e
  `query: ` na consulta).
- **Modelos candidatos:**
  - um small, com 384 dimensões (alvo: `multilingual-e5-small`);
  - um base, com 768 dimensões (alvo: `multilingual-e5-base`).

  A lista exata é confirmada no passo 3 da entrega contra o catálogo do `fastembed`. Se um modelo e5 não estiver no
  catálogo, ele é carregado como modelo ONNX customizado. Se nem assim, entra o multilíngue mais próximo do catálogo
  (por exemplo, `paraphrase-multilingual-MiniLM-L12-v2`), com a troca registrada na avaliação.
- **Download:** acontece na primeira vez que for necessário, para um cache em `_app/.modelos/` (no `.gitignore`).
- **Testes:** usam um provedor falso e determinístico, `EmbeddingsFalso`, que gera vetores a partir das palavras.
  Nenhum teste da suíte padrão baixa modelo.

### 3.3 Índice

- Coluna `trecho.vetor BLOB NULL`, com `float32` normalizado.
- A tabela `estado` passa a guardar `modelo` e `dimensao`. Modelo ou dimensão diferente do configurado conta como índice
  desatualizado e leva a refazer, como já acontece com `VERSAO_INDICE`.
- **Sincronização incremental:** vale o mesmo critério de hoje (sha da fonte, `atualizado_em` do documento), e só os
  trechos novos ou alterados ganham vetor.
- **Sem embeddings** (desligado ou modelo indisponível): `vetor` fica NULL e o índice continua válido para a busca por
  texto.
- **Busca vetorial:** a matriz de vetores da matéria é carregada uma vez por processo e invalidada a cada sincronização.
  O cosseno é calculado por produto de matrizes (cerca de 3 mil × 384 `float32`, uns 5 MB).

### 3.4 Busca

- `buscar(indice, q, unidade, secao_id, tipos, limite, modo)`:
  - `texto`: o BM25 atual, sem mudança;
  - `vetor`: cosseno, com os mesmos filtros de unidade, seção e tipo (filtro aplicado sobre os ids permitidos);
  - `hibrida`: pega os top-50 de cada modo e funde por RRF, `nota = Σ 1/(60 + posição)`.
- O `Resultado` ganha o campo `por`, que vale `"texto"`, `"sentido"` ou `"ambos"` e alimenta a etiqueta "pelo sentido"
  da interface.
- Em `GET /api/materias/{uid}/busca`:
  - entra o parâmetro opcional `modo`, cujo padrão é o do config;
  - a resposta ganha `modo` (o modo efetivamente usado). Se o pedido for `vetor` ou `hibrida` sem vetores disponíveis,
    a busca cai para `texto` e a resposta diz isso.

### 3.5 Vínculos

- Em `vinculo.py`, `nota = (1 − p) · regra + p · sentido`:
  - `regra` é a similaridade atual (Jaccard com IDF);
  - `sentido = (1 + cos) / 2`, levado para 0 a 1;
  - `p` começa em 0,5 e é o único parâmetro calibrado no gabarito.
- Vale para todas as ligações que hoje passam por `pontuar` e `melhores`: tópico ↔ seção, lista ↔ tópico/unidade,
  livro ↔ livro e referência ↔ livro. A ordem dos resumos na lista de documentos é do frontend
  (`ordenarPeloAssunto`) e fica fora desta peça.
- Os limiares `limiar_vinculo` e `limiar_confianca` continuam decidindo entre "grava" e "revisar", e são recalibrados
  com o gabarito se os embeddings entrarem.
- **Origem do vínculo:** a proposta mostra o motivo, que pode ser "por palavras", "pelo sentido" ou "pelos dois".
- Com `vinculos_com_embeddings = false`, o resultado é **idêntico** ao atual (há teste para isso).

### 3.6 Configuração

```toml
[inteligencia]
# Embeddings locais (modelo baixado uma vez; depois funciona offline). false = só regras e busca por texto.
embeddings = false
modelo = "intfloat/multilingual-e5-small"
# "texto" (BM25), "vetor" ou "hibrida".
busca = "texto"
vinculos_com_embeddings = false
# Peso do sentido na nota dos vínculos (calibrado pela avaliação).
peso_sentido_vinculo = 0.5
```

Os valores padrão só mudam depois da avaliação (§4.4), num commit próprio que cita os números.

### 3.7 Falhas

| Situação | Comportamento |
|---|---|
| Sem internet no primeiro download, modelo corrompido ou ONNX incompatível | Um aviso; a busca cai para `texto` e os vínculos para regra pura; nada trava |
| Índice de outro modelo ou dimensão | Refeito sozinho na próxima sincronização |
| Matéria sem índice | Sincroniza e devolve o progresso; a interface mostra "Montando o índice…" |

## 4. Avaliação

### 4.1 Gabarito de busca: `estudos/avaliacao/gabaritos/calculo2_busca.toml`

Cerca de 40 itens:

```toml
[[pergunta]]
texto = "como calculo a área de uma região circular com integral dupla"
estilo = "parafrase"            # ou "exata"
aceitas = ["secao:15.4"]        # seções por código, ou "documento:<título>"
unidade = 3                     # opcional
```

Metade `exata` (palavras do livro), metade `parafrase` (como um aluno perguntaria). O rascunho do Claude é apresentado
como tabela, o usuário corrige e acrescenta dúvidas reais, e só então o arquivo vale.

### 4.2 Gabarito de vínculos: `calculo2_vinculos.toml`

Contém:
- tópicos de cada unidade, com a seção certa do Stewart;
- listas, com a unidade (e o tópico, quando houver) certa.

É preenchido a partir dos vínculos que hoje estão no banco, com os casos duvidosos marcados para o usuário revisar.

### 4.3 Comando

```text
python -m estudos.avaliacao busca    --materia "Calculo 2"
python -m estudos.avaliacao vinculos --materia "Calculo 2"
```

- **Isolamento:** roda cada configuração candidata num índice temporário, sem tocar no índice nem no `materia.db`
  reais.
- **Configurações candidatas:**
  - busca: texto; vetor (small, base); híbrida (small, base);
  - vínculos: regra; regra + sentido, com `p` em {0,3; 0,5; 0,7}.
- **Métricas de busca:**
  - acerto@5, no geral e por estilo;
  - MRR@10;
  - tempo de indexação;
  - latência da busca (mediana e p95);
  - pico de memória.
- **Métricas de vínculos:**
  - acertos;
  - erros gravados com confiança acima do limiar (os "erros confiantes");
  - itens mandados para revisão.
- **Saída:** a tabela no terminal e o arquivo `docs/avaliacoes/AAAA-MM-DD-<busca|vinculos>.md`.

### 4.4 Regras de decisão (fixadas antes de ver os números)

**Busca:** `hibrida` vira o padrão se cumprir todas:
- acerto@5 em `parafrase` sobe **≥ 10 pontos** sobre `texto`;
- acerto@5 em `exata` não cai **mais de 2 pontos**;
- p95 da busca **< 300 ms**;
- indexação da matéria **< 10 min**.

O modelo base só substitui o small se ganhar **mais ≥ 5 pontos** de acerto@5 geral. Se nada passar, o padrão fica
`texto` e os embeddings ficam desligados e documentados.

**Vínculos:** os embeddings entram se cumprirem as duas:
- aumentam os acertos;
- não criam **nenhum** erro confiante novo.

Escolhe-se o melhor `p` entre os testados e os limiares são recalibrados com o mesmo gabarito.

**Contra o excesso de ajuste:** RRF com k = 60 fixo e um único parâmetro nos vínculos.

## 5. Interface: busca na matéria

- **Gatilho:**
  - campo "Buscar na matéria…" na barra do topo das telas da matéria (ao lado dos botões das unidades), com a dica
    `Ctrl K`;
  - o atalho Ctrl K vale em qualquer tela da matéria.
- **Paleta:** janela sobre a tela, nas cores do tema. Tem:
  - o campo de busca;
  - o filtro **Esta unidade** (padrão) / **Toda a matéria**;
  - o filtro de tipo: **Tudo**, **Livros**, **Listas e provas**, **Textos**.
- **Resultados** agrupados por tipo. Cada um mostra:
  - o título (seção · livro · página, ou o título do documento);
  - o trecho com as palavras da busca destacadas;
  - a etiqueta **"pelo sentido"** quando `por = "sentido"`.
- **Teclado:** setas andam, Enter abre, Esc fecha. A busca dispara a partir de 2 letras, com espera de 200 ms.
- **Abrir:** usa `estado/pedido.svelte.ts`, que ganha um pedido de fonte com página e um de documento com âncora.
  - livro, lista, prova ou gabarito: Documentos, com o PDF aberto na página;
  - texto: Documentos, com o documento aberto e rolado até o bloco `##` que casou.
- **Vazio:** "Nada encontrado nesta unidade", com o atalho "Buscar na matéria toda".
- **Índice sendo montado:** "Montando o índice…", com o progresso da sincronização.

## 6. Testes

- **Motor** (pytest, com `EmbeddingsFalso`):
  - fusão RRF;
  - os três modos com filtros;
  - queda para `texto` sem vetores;
  - troca de modelo invalidando o índice;
  - sincronização incremental de vetores;
  - nota combinada nos vínculos;
  - **igualdade exata** com o comportamento atual quando desligado;
  - leitura dos gabaritos e cálculo das métricas.
- **Modelo real:** um teste marcado `modelo`, fora da suíte padrão e do CI, que carrega o `fastembed` e gera um vetor.
- **Interface:**
  - Vitest da paleta (teclado, filtros, etiqueta, abrir) e dos pedidos de abertura;
  - um e2e: buscar, abrir e cair na página ou no bloco certo.

## 7. Ordem de entrega

Cada passo termina com as suítes verdes:

1. Gabaritos (rascunho → revisão do usuário) e comando de avaliação sobre o BM25 atual: a **linha de base**.
2. Busca na interface (Ctrl K) sobre a busca atual.
3. `estudos/ia/embeddings.py`, vetores no índice e busca `vetor`/`hibrida`, desligados por padrão. Avaliação e decisão
   pela §4.4.
4. Nota combinada nos vínculos. Avaliação, decisão e calibração.
5. Registro das decisões em `docs/avaliacoes/`, novos padrões no `config.toml` (se for o caso) e emenda nesta spec com
   os números.

## 8. Fora de escopo

- Treinar ou ajustar o modelo (*fine-tuning*).
- Embeddings por API (o Gemini fica como provedor possível atrás da interface, não implementado).
- Extensão vetorial no SQLite e servidor remoto.
- Normalização especial de fórmulas para a busca (pergunta em aberto, fica para depois dos números).
- Peças A, C e D da Fase 6.
