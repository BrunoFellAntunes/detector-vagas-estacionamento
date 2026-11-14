# Rascunhos locais do editor

`app.rascunhos.DraftStore(directory)` persiste **um rascunho ativo por diretório**,
independentemente de Qt, OpenCV, detector e perfis. Usa somente a biblioteca padrão.
O chamador deve fornecer uma pasta local dedicada, por exemplo
`perfis/rascunhos/`, dentro da árvore `perfis/` já ignorada pelo Git.
O construtor não cria arquivos. Não há timers, widgets nem integração automática
nesta entrega (issue #19).

## Contrato JSON, versão 1

Os nomes em inglês acompanham o contrato existente dos perfis e mapas.
O argumento de `save` e o retorno de `load` são dicionários JSON comuns:

```json
{
  "version": 1,
  "name": "Pátio São João",
  "source": "C:/Vídeos/gravação.mp4",
  "width": 1100,
  "height": 720,
  "frame_index": 60,
  "config": {
    "width": 1100,
    "height": 720,
    "method": "texture",
    "texture_block_size": 25,
    "texture_constant": 16,
    "analysis_inset": 1,
    "stable_frames": 5,
    "free_ratio": 0.11,
    "occupied_ratio": 0.12,
    "spaces": []
  },
  "source_profile_id": null
}
```

| Campo | Regra |
| --- | --- |
| `version` | Inteiro exatamente `1`. Booleanos e versões desconhecidas são rejeitados. |
| `name` | Texto de até 80 caracteres. Pode estar vazio: o usuário pode ainda estar preenchendo o nome. |
| `source` | Caminho do vídeo em texto não vazio, sem caractere nulo. Preservado literalmente, sem resolver, abrir ou modificar o arquivo. |
| `width`, `height` | Inteiros positivos de 32 bits, iguais aos valores de `config`. |
| `frame_index` | Índice inteiro não negativo, começando em zero. |
| `config` | Objeto de mapa do editor, com `width`, `height`, `method: "texture"` e lista `spaces` obrigatórios. Lista vazia é válida. |
| `source_profile_id` | Opcional: ausente, `null` ou UUID canônico em minúsculas, como o `Profile.id`. Nunca usado para acessar pastas. |

Campos principais desconhecidos são rejeitados para detectar erros de contrato.
Metadados adicionais dentro de `config`, vagas e grupos são preservados sem
coerção: por exemplo setor, linha, motivo, limiares locais e grupos de ambiguidade.
Todo o conteúdo deve usar tipos JSON: objetos com chaves de texto, listas,
strings, números finitos, booleanos e `null`. Tuplas, conjuntos, NaN, infinito,
referências cíclicas e valores não serializáveis são rejeitados.

O serviço valida identificadores únicos de vagas, vértices inteiros sem repetição,
polígonos estritamente convexos dentro da imagem e área mínima de quatro pixels
quadrados. Aceita os dois sentidos de desenho. Valida também:

- `0 <= free_ratio < occupied_ratio <= 1`, inclusive os limiares locais;
- `stable_frames` inteiro positivo; `analysis_inset` inteiro entre 0 e 20;
- `texture_block_size` inteiro ímpar >= 3 de 32 bits; `texture_constant` finito;
- `0 < pixel_threshold < 255`, quando presente;
- grupos com pelo menos duas vagas existentes distintas,
  `0 < brightness_threshold < 255` e `0 < min_region_ratio <= 1`.

Parâmetros opcionais ausentes são validados com os padrões atuais do detector
(`free_ratio=.1`, `occupied_ratio=.2`, `stable_frames=5`, `analysis_inset=0`,
`texture_block_size=25`, `texture_constant=16`, `pixel_threshold=25`;
grupos: brilho 180 e razão .08). O arquivo não recebe campos novos nem sofre
normalização. Ao criar um novo rascunho, prefira fornecer a configuração completa
do editor, cujos limiares iniciais são .11/.12 e margem 1.

## Operações e tratamento de erros

```python
from app.rascunhos import DraftStore

store = DraftStore("perfis/rascunhos")
store.save(draft)       # retorna None; não altera o dicionário fornecido
recovered = store.load()  # dict validado ou None se não existe ativo
archived = store.archive()  # Path da cópia arquivada ou None se não existe ativo
```

### Salvar

`save(draft)` valida os dados antes de tocar no disco, cria a pasta se necessário
e grava JSON UTF-8 legível com acentos em um temporário exclusivo na **mesma
pasta** de `rascunho.json`. Faz `flush`, `os.fsync`, fecha o arquivo e só então
chama `os.replace` para substituir atomicamente o ativo. Assim, leitores veem o
arquivo anterior completo ou o novo completo. Uma falha de escrita,
sincronização ou substituição mantém o rascunho anterior legível.

Dados inválidos geram `ValueError`. Erros de acesso/gravação geram `OSError`
com a operação e o caminho; a exceção original é encadeada. O temporário é
removido ao final. Se a própria limpeza falhar, pode sobrar um `.tmp`, que nunca
é considerado ativo por `load`. Uma validação rejeitada não substitui o ativo.

### Recuperar

`load()` lê exclusivamente `rascunho.json`. Ausência retorna `None`; falhas de
permissão/leitura geram `OSError`, em vez de parecer que não há rascunho.
JSON corrompido (com linha/coluna), UTF-8 inválido, chaves duplicadas, valores
não finitos, versão desconhecida ou dados inconsistentes geram `ValueError`
com explicação. **O arquivo problemático permanece intacto**, sem exclusão,
regravação, execução de conteúdo ou migração automática.

### Arquivar e restaurar manualmente

`archive()` reserva um nome único com `mkstemp` em
`arquivados/rascunho-<sufixo-exclusivo>.json` e move o ativo para esse caminho
com `os.replace`. O nome é reservado de forma exclusiva, sem sobrescrever
arquivamentos anteriores. O conteúdo é preservado byte a byte, inclusive se
estiver corrompido ou em versão desconhecida. A operação não percorre perfis
nem remove revisões ou resultados. Em caso de falha ao mover, o ativo permanece
e a reserva é limpa quando possível.

Para recuperação manual, com as operações de edição pausadas, preserve qualquer
ativo atual e copie o arquivo arquivado escolhido para `rascunho.json`; depois
chame `load()` para validar. Arquivos inválidos precisam de correção manual ou
de uma versão futura compatível. Não há interface nem API de seleção de arquivos
arquivados nesta etapa. Não existe limpeza automática de histórico.

## Pontos de integração futura

1. **Após alterações, com debounce:** montar um snapshot com `name_edit.text()`,
   `str(video_info.source)`, dimensões de `video_info`, índice do `frame_slider`,
   `current_config()` e `profile.id` quando houver perfil de origem. O chamador
   adiciona `version=1` e agenda `save` após uma pausa curta. Não gravar a cada
   movimento do mouse. A duração do debounce será definida na integração.
2. **Ao abrir o editor:** chamar `load()` e oferecer recuperar o rascunho ou
   começar outro. Informar erros claramente, preservando o arquivo. Ao recuperar,
   conferir novamente o vídeo, resolução e índice disponível antes de aplicá-los
   à interface; carregar a geometria e os parâmetros preservados. Não assumir
   que o vídeo permaneceu no mesmo caminho ou que um perfil ainda exista.
3. **Após “Salvar e analisar”:** somente depois de confirmar o salvamento do
   perfil, cancelar qualquer gravação pendente do debounce e chamar `archive()`.
   Não arquivar se o salvamento do perfil falhar. Se o arquivamento falhar,
   informar que o perfil foi salvo, mas o rascunho continua ativo; não desfazer
   o perfil nem apagar suas revisões.

Não alterar o painel antes da revisão deste contrato pelo grupo. A documentação
existente da interface continua descrevendo o comportamento atual da sessão.

## Limitações e garantias

- Um ativo por diretório; o chamador deve serializar `save`, `load` e `archive`
  e evitar gravações concorrentes. Não há lock nem resolução de conflitos;
  entre salvamentos concorrentes, vence a última substituição.
- O serviço não verifica existência, duração, FPS, identidade ou conteúdo do
  vídeo, existência do perfil, nem limite superior do quadro (a contagem não é
  armazenada). Essas verificações pertencem à recuperação na interface.
- A validação do mapa não executa o detector nem simula máscaras de pixels.
  Antes de analisar, validar com `Detector`, inclusive se a margem interna
  remove toda uma região muito pequena. Mapa sem vagas é rascunho válido,
  mas ainda não é perfil pronto para análise.
- Atomicidade depende do sistema de arquivos local suportar `os.replace`.
  `fsync` sincroniza o temporário, mas não há promessa de durabilidade absoluta
  de diretórios/metadados em queda de energia. Não há transação entre perfil
  salvo e arquivamento, nem sincronização em nuvem ou cópia do vídeo.
- Nenhum arquivo de vídeo, perfil, resultado ou revisão existente é modificado.
  Não há dependências novas, rede, execução de conteúdo JSON ou timers.

## Testes

```powershell
python -m unittest discover -s tests -p test_rascunhos.py -v
python -m unittest discover -s tests -v
```

Os testes de rascunhos usam diretórios temporários e biblioteca padrão. Cobrem
primeira gravação, substituição, UTF-8 com acentos, mapa vazio, perfil opcional,
compatibilidade com o mapa completo da demonstração, validação, corrupção,
arquivamento único e restauração manual, preservação de revisões, falhas durante
escrita parcial, `fsync`, substituição e arquivamento. A suíte existente completa
requer as dependências de `requirements-app.txt` para incluir os widgets Qt.
