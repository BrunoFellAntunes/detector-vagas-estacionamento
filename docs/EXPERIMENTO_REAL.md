# Experimento com vídeo real de terceiros

Este relatório descreve o experimento anterior de cinco regiões por referência vazia. O aplicativo atual monitora 68 vagas pelo método descrito em [MAPA_COMPLETO.md](MAPA_COMPLETO.md).

O exemplo acompanha cinco regiões internas de vagas no arquivo `dados/terceiros/carPark.mp4`. O vídeo é externo e sua origem está documentada em [FONTES_MIDIA.md](FONTES_MIDIA.md). A execução ilustra o funcionamento do algoritmo no clipe; não é um levantamento do estacionamento do grupo nem uma avaliação independente de generalização.

## Reprodução

Depois de instalar as dependências, a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe executar_exemplo.py --show
```

Espaço pausa e retoma; Q ou Esc encerra. Para gerar todos os resultados sem abrir janela:

```powershell
.\.venv\Scripts\python.exe executar_exemplo.py
```

O programa aceita `--output caminho` para escolher outra pasta. Ele também pode ser chamado pelo caminho absoluto a partir de outro diretório. Se o usuário encerrar a reprodução antecipadamente, o resumo identifica a interrupção e a avaliação da amostra completa não é executada.

## Cadastro e referência

A referência foi extraída do quadro 678, o último do vídeo. Nesse quadro, as cinco regiões selecionadas estão vazias. As demais vagas do estacionamento não precisam estar vazias porque não são classificadas. Essa escolha depende de uma inspeção prévia do próprio clipe; não representa uma solução que inicia automaticamente em um estacionamento desconhecido.

Os polígonos estão em `dados/terceiros/vagas_carpark.json`. Eles representam áreas internas das vagas, reduzindo a influência das linhas, dos veículos vizinhos e das bordas. O vídeo apresenta pequenos deslocamentos de enquadramento. Não há estabilização automática: o cadastro funciona para este clipe, e movimento maior da câmera exige novo cadastro ou outro tratamento.

| Vaga | Localização | Situação observada no clipe |
|---|---|---|
| V01 | Fileira esquerda, lado direito, região inferior | SUV escuro sai da vaga |
| V02 | Fileira direita, lado esquerdo, região central superior | Carro branco sai da vaga |
| V03 | Fileira esquerda, lado direito, região central inferior | Veículo branco sai da vaga |
| V04 | Fileira esquerda, lado esquerdo, região central | Região permanece vazia na amostra |
| V05 | Fileira central, lado esquerdo, região inferior | Região permanece vazia na amostra |

Foram mantidos os parâmetros iniciais: diferença de pixels 25, fração de ocupação 0,20, fração de liberação 0,10 e cinco quadros consecutivos de confirmação. O método detecta alterações em relação à referência e não reconhece semanticamente automóveis.

## Rótulos e avaliação

O arquivo `dados/terceiros/rotulos_carpark.csv` contém 60 rótulos: cinco regiões em 12 quadros, do quadro 0 ao 660, a cada 60 quadros. Os estados foram anotados por inspeção visual das regiões, sem calcular os rótulos pela saída do detector. A conferência dos rótulos deve integrar o ensaio técnico do grupo.

Esta é uma amostra exploratória do mesmo clipe usado para escolher as regiões e a referência. Ela não cobre todos os instantes nem estabelece o desempenho em condições variadas. Para uma avaliação independente, serão necessárias outras sequências, rótulos adicionais e parâmetros fixados antes da execução sobre essas sequências.

Resultados da amostra, obtidos pela execução completa e por `avaliar.py`:

| Medida | Resultado |
|---|---:|
| Quadros processados | 679 |
| Vagas monitoradas | 5 |
| Decisões exportadas no clipe | 3.395 |
| Rótulos avaliados | 60 |
| Decisões concordantes na amostra | 54 |
| Estados indefinidos na amostra | 5 |
| Decisões definidas divergentes | 1 |
| Cobertura da amostra | 91,67% |
| Concordância incluindo indefinidos | 90,00% |
| Acurácia somente das decisões definidas | 98,18% |
| Precisão para ocupado nas decisões definidas | 90,91% |
| Revocação para ocupado nas decisões definidas | 100,00% |
| F1 para ocupado nas decisões definidas | 95,24% |

Matriz de confusão nas 55 decisões definidas: VP = 10, VN = 44, FP = 1 e FN = 0. Os cinco estados indefinidos correspondem ao quadro zero, antes da confirmação inicial. O falso positivo ocorre em V03 no quadro 360; o detector confirma a liberação no quadro 361. Isso mostra o efeito da confirmação temporal em uma transição e não deve ser ocultado ao apresentar as métricas.

O detector registra cinco confirmações iniciais no quadro 4 e três liberações posteriores: V01 no quadro 147, V02 no quadro 222 e V03 no quadro 361. Os tempos da fonte são 6,125 s, 9,250 s e aproximadamente 15,042 s. Esses valores são instantes de confirmação do detector; não equivalem a atraso medido desde a saída física completa do veículo.

## Arquivos de saída

Em `resultados/carpark/`:

- `video_anotado.mp4`: vídeo processado com rótulos, contagem e índice de quadro.
- `ocupacao.csv`: uma linha por quadro e vaga.
- `eventos.csv`: inicializações e mudanças confirmadas de estado.
- `resumo.json`: contagem final, quadros, tempo total e indicação de interrupção.
- `ultimo_quadro.png`: imagem final processada.
- `avaliacao.json`: cobertura, concordância e métricas da amostra rotulada.

O tempo total inclui leitura, classificação e exportação, além da apresentação e das pausas quando a janela é utilizada. Por isso, a taxa registrada com `--show` não isola a velocidade do algoritmo. O FPS informado pelo arquivo descreve sua reprodução, não o desempenho de processamento.

Para avaliar outros rótulos com uma saída existente:

```powershell
.\.venv\Scripts\python.exe avaliar.py --predicoes resultados/carpark/ocupacao.csv --rotulos dados/terceiros/rotulos_carpark.csv --output resultados/carpark/avaliacao.json
```

O avaliador rejeita duplicações, estados inválidos e rótulos sem predição correspondente. Indefinidos permanecem no denominador da concordância total. Precisão, revocação, F1 e matriz de confusão são calculados somente entre decisões definidas; cobertura e quantidade de indefinidos devem ser relatadas junto dessas medidas.
