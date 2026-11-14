# Duplicação de vagas

`app.duplicacao.duplicate_spaces(spaces, selected_id, dx, dy, copies, width, height)`
é uma função pura, implementada apenas com a biblioteca padrão. Não depende de
Qt, OpenCV, disco ou rede. Esta entrega não acrescenta controles ao painel.

## Contrato

- `spaces`: lista de dicionários do mapa cadastrado, com IDs únicos em `id` e
  polígonos válidos em `points` (listas de pares `[x, y]` em pixels inteiros).
  Use os dados do mapa, não as estruturas internas do detector com máscaras.
- `selected_id`: ID exato de uma região existente; mapa vazio ou seleção ausente
  causam `ValueError`.
- `dx` e `dy`: inteiros em pixels da imagem original, inclusive negativos.
  Um deles pode ser zero, mas `(0, 0)` é rejeitado.
- `copies`: quantidade de **novas** regiões, inteiro de 1 a 50, inclusive.
- `width` e `height`: dimensões inteiras positivas da imagem original.
  Booleanos, strings e floats (mesmo `1.0`) não são aceitos como inteiros em
  nenhum desses cinco argumentos numéricos.
- Retorno: nova lista, com as regiões existentes na mesma ordem e as cópias ao
  final. A cópia de índice `i`, começando em 1, soma `(i*dx, i*dy)` a cada vértice
  da origem. Não há rotação, escala, arredondamento nem recorte.

Os IDs novos começam após o maior sufixo numérico entre IDs no formato
`V[0-9]+`. São formatados com pelo menos dois dígitos: `V09`, `V10`, `V100`.
Zeros à esquerda contam numericamente (`V009` conta como 9); lacunas não são
reutilizadas. IDs personalizados são preservados e não entram nesse cálculo.
Sem IDs numéricos V, a sequência começa em `V01`. Nenhum ID antigo é renumerado.

Todos os vértices de todas as cópias devem satisfazer `0 <= x < width` e
`0 <= y < height`: o último pixel é `(width-1, height-1)`. Uma única violação
gera `ValueError` indicando a cópia que sairia da imagem. A operação inteira
falha, sem resultado parcial e sem alteração na entrada.

## Campos preservados

As regiões existentes são copiadas integralmente. Nas novas regiões:

| Campo | Tratamento |
| --- | --- |
| `id` | Novo identificador único |
| `points` | Mesmos vértices, ordem e forma, apenas transladados |
| `free_ratio`, `occupied_ratio` | Preservados quando presentes; ausentes continuam ausentes para herdar os limiares gerais |
| `setor`, `linha` | Removidos; a posição lógica deve ser cadastrada depois |
| Outros campos, inclusive aninhados | Preservados por cópia profunda |

O resultado não compartilha objetos mutáveis com a entrada. Cada nova região
também tem seus próprios pontos e metadados aninhados, independentes das demais
cópias. Alterar o retorno não altera o mapa original.

## Exemplo

```python
from app.duplicacao import duplicate_spaces

spaces = [{
    'id': 'V03',
    'points': [[10, 10], [30, 10], [30, 30], [10, 30]],
    'free_ratio': 0.05,
    'occupied_ratio': 0.065,
    'setor': 'A',
    'linha': 1,
}]
updated = duplicate_spaces(spaces, 'V03', 40, 0, 2, 200, 100)
assert [s['id'] for s in updated] == ['V03', 'V04', 'V05']
assert updated[1]['points'] == [[50, 10], [70, 10], [70, 30], [50, 30]]
assert updated[2]['points'] == [[90, 10], [110, 10], [110, 30], [90, 30]]
assert 'setor' not in updated[1] and 'linha' not in updated[1]
assert len(spaces) == 1

try:
    duplicate_spaces(spaces, 'V03', 100, 0, 2, 200, 100)
except ValueError as error:
    print(error)  # A cópia 2 sairia da imagem; a primeira não é aplicada.
```

## Integração futura com MapCanvas

A integração será feita em outra tarefa. O comando do painel deve:

1. Encerrar/cancelar o gesto de edição pendente pelo mecanismo do canvas antes
   de capturar o estado estável. Usar `canvas.spaces`, `canvas.selected_space`,
   `canvas.source_width` e `canvas.source_height`; não usar dimensões do widget
   nem coordenadas de tela. Converter controles da interface para inteiros.
2. Guardar `before = deepcopy(canvas.spaces)` e chamar a função. Se houver
   `ValueError`, exibir a mensagem via `notice` e não substituir o mapa,
   alterar a seleção ou adicionar uma entrada ao histórico de duplicação.
3. Somente no sucesso, atribuir o retorno a `canvas.spaces`, selecionar uma
   nova região (por exemplo, `canvas.select(result[-1]['id'])`) e chamar
   `canvas._commit(before)` **uma única vez** para todo o lote. Esse mecanismo
   existente registra desfazer, limpa refazer/prévia, emite `changed` e redesenha.
4. Atualizar `canvas._next_number` para pelo menos o maior sufixo numérico V do
   resultado mais um, sem reduzir o contador atual. Isso evita que o próximo
   desenho manual reutilize um ID criado pela duplicação. Manter essa regra
   também ao integrar desfazer/refazer.

Não usar `set_map` para aplicar a duplicação: ele reinicializa seleção e
histórico. A função não emite sinais, não muda seleção/contadores do canvas,
não salva perfis nem dispara análise. O painel continua responsável por isso.
As configurações gerais e os grupos de revisão conjunta ficam fora de `spaces`
e não são duplicados automaticamente.

## Limitações e testes

O mapa de entrada deve estar previamente validado: esta operação não revalida
convexidade, área mínima, IDs duplicados preexistentes ou formato de metadados.
Não detecta sobreposição entre vagas, não recalibra limiares e não infere setor
ou linha. A translação conserva o formato, mas perspectiva e textura podem
exigir ajustes manuais na nova posição. IDs são únicos no mapa recebido, não
um contador global entre mapas ou chamadas concorrentes.

Os testes de comportamento cobrem uma/múltiplas/50 cópias, lacunas e zeros nos
IDs, chamadas sucessivas, isolamento profundo, campos opcionais, quatro bordas,
falha na segunda cópia e argumentos inválidos. Execute na raiz do repositório:

```console
python -m unittest discover -s tests -v
```
