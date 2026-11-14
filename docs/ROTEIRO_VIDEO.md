# Roteiro da apresentação

Duração planejada: 8 minutos e 40 segundos. Reservar 1 minuto e 20 segundos de margem até o limite de dez minutos. Todos os quatro integrantes devem falar com a própria voz e demonstrar que compreendem o projeto.

Este é um roteiro para ensaio, não um relato de coleta já realizada. Atualizem os trechos sobre local, usuários, observação e resultados com evidências reais antes da gravação final. Se demonstrarem a simulação, identifiquem-na expressamente. A gravação deve mostrar o programa em execução; slides podem servir apenas de apoio.

## Divisão do tempo

| Tempo | Integrante | Conteúdo e tela |
|---|---|---|
| 0:00 a 1:30 | Vitor Rodi | Integrantes, problema, local e investigação |
| 1:30 a 3:00 | Pedro Toigo | Solução, tecnologias e método |
| 3:00 a 5:00 | Bruno Fell Antunes | Referência, cadastro e primeira execução |
| 5:00 a 7:00 | Edson Leandro Soares | Entrada e saída, contagem e exportações |
| 7:00 a 7:25 | Vitor Rodi | Resultados medidos e relação com o problema |
| 7:25 a 7:50 | Pedro Toigo | Dificuldades técnicas |
| 7:50 a 8:15 | Bruno Fell Antunes | Limitações e melhorias |
| 8:15 a 8:40 | Edson Leandro Soares | Conclusão e links de entrega |

## Vitor Rodi apresenta o problema

Começar com: “Nosso grupo é formado por Vitor Rodi, Pedro Toigo, Bruno Fell Antunes e Edson Leandro Soares. Desenvolvemos um protótipo para indicar a ocupação de vagas de estacionamento usando imagens de uma câmera fixa.”

Explicar que a busca depende da visualização das vagas e pode exigir percorrer corredores. Identificar o estacionamento efetivamente observado, quem o utiliza e como o grupo investigou o problema. Relatar apenas o que a observação ou entrevista permitiu concluir. Não afirmar redução de tempo, economia ou melhoria de trânsito sem medição.

Mostrar uma foto autorizada do contexto e o objetivo do projeto. Transição: “O Pedro vai explicar como transformamos essa necessidade em um processamento de imagens.”

## Pedro Toigo explica a solução

Mostrar brevemente `detector.py` e o diagrama verbal: câmera fixa → tons de cinza e suavização → limiarização adaptativa → mediana e dilatação → densidade de textura por vaga → confirmação temporal → contagem e registro.

Fala central: “Usamos Python, OpenCV e NumPy, com PySide6 para a janela nativa. Não treinamos uma rede neural. Cadastramos manualmente 71 regiões e medimos textura em cada região. O valor não é uma probabilidade de haver um carro. O modo anterior por referência vazia também permanece disponível.”

Explicar os dois limiares e os cinco quadros de confirmação. Explicar por que não se usa o último quadro como fundo vazio global: muitos carros continuam estacionados. A textura permite analisar esses carros parados, com limitações. Explicar que alterações de sombra também podem causar erro. Transição: “Agora vamos executar o programa e acompanhar o que acontece em cada vaga.”

## Bruno Fell Antunes inicia a demonstração

Mostrar vagas_completas_carpark.json e como os quatro cantos delimitam cada vaga. Identificar os seis setores e as exclusões de ilhas e corredores. Mostrar V69 acima da V59 e a revisão conjunta de V70/V71 sob a van. Usar uma cópia da configuração caso se demonstre a ferramenta de cadastro manual.

Abrir `INICIAR_APLICATIVO.bat`, aguardar a análise e mostrar a janela Vaga com 12 estados livres, 57 ocupados e dois em análise. Mostrar Reprocessar, que executa novamente o detector, e o botão Reproduzir. Explicar o significado de verde, vermelho e amarelo. Demonstrar que a contagem acompanha os estados e que uma alteração fora de uma região não deveria mudar aquela vaga.

Para ensaiar com dados simulados:

```powershell
.\.venv\Scripts\python.exe demo.py
.\.venv\Scripts\python.exe detector.py --source dados/cena_simulada.png --reference dados/referencia_vazia.png --config dados/vagas_demo.json --output resultados/imagem --show
```

O exemplo real já cadastrado abre em uma janela nativa com `.\.venv\Scripts\python.exe aplicativo.py`. O comando `executar_exemplo.py --completo --show` continua disponível para demonstrar o detector diretamente. Ele monitora 71 regiões do vídeo de terceiros; explicar a origem, o mapa e os limiares conforme `MAPA_COMPLETO.md`. A imagem do quadro 678 não é um fundo vazio das 71 regiões. Na interface Vaga, usar Reproduzir/Pausar e a barra de posição para explicar as saídas. O botão Apresentar abre tela cheia; Esc retorna à janela. Veja [APLICATIVO.md](APLICATIVO.md) para o percurso de ensaio. Para uma gravação própria, seguir `COLETA_REAL.md`. Mostrar o comando completo e pelo menos um trecho do processamento. A demonstração deve usar o mesmo código publicado no GitHub.

## Edson Leandro Soares continua a demonstração

Na gravação externa, mostrar as saídas de V01, V02 e V03, confirmadas nos quadros 118, 172 e 370. Essa gravação não contém entradas de veículos estacionando; para demonstrar uma entrada, usar a simulação identificada ou a coleta própria. Destacar os cinco quadros de confirmação e explicar que liberação parcial de uma vaga pode ser indicada antes da saída física completa. Mostrar um veículo parado mantendo o estado ocupado. Se a coleta tiver falhas com sombras, mostrar um exemplo e explicar a limitação.

Na janela Vaga, selecionar uma vaga, aplicar Somente livres e voltar a uma mudança pelo histórico. Usar Exportar resultados, extrair o ZIP, abrir `ocupacao.csv` e explicar quadro, tempo estimado, vaga, estado e densidade de textura. Abrir o vídeo exportado. Não apresentar o FPS do arquivo como velocidade medida do algoritmo.

Para ensaio reproduzível:

```powershell
.\.venv\Scripts\python.exe detector.py --source dados/video_simulado.mp4 --reference dados/referencia_vazia.png --config dados/vagas_demo.json --output resultados/video
.\.venv\Scripts\python.exe verificar_demo.py
```

O vídeo simulado tem somente 12 segundos. O período de demonstração inclui a execução, o cadastro, a explicação dos estados e as exportações; não é necessário esticar ou repetir a reprodução para preencher quatro minutos.

## Os quatro apresentam os resultados e encerram

Vitor: relatar os resultados reais medidos e retomar o objetivo de apresentar disponibilidade. Se houver apenas simulação, dizer que o funcionamento foi verificado em cenário controlado e que a efetividade no local ainda não foi demonstrada.

Pedro: explicar uma dificuldade técnica efetivamente observada, como alinhamento da câmera, limiares ou oscilação entre quadros. Evitar relatar problemas que o grupo não verificou.

Bruno: comentar veículos lisos, pedestres, sombras, oclusão e mudança de iluminação. Mostrar os erros de V55 registrados no histórico. Como melhorias, propor calibração por condição de luz, avaliação com mais sequências ou comparação com um classificador treinado. Identificar propostas como trabalho futuro.

Edson: concluir o que foi demonstrado e mostrar o repositório público. Informar que a reprodução está descrita no README e encerrar antes de dez minutos. Não inventar endereço do YouTube antes de publicar.

## Conferência antes de gravar

- Ensaiar o percurso com os quatro integrantes e cronometrar.
- Testar microfones, volume e captura da tela; deixar a janela do aplicativo e qualquer texto do terminal legíveis.
- Fechar abas pessoais e notificações antes da captura.
- Mostrar entradas, programa e saídas em vez de apresentar exclusivamente slides.
- Gravar as próprias falas. Cada integrante deve conseguir explicar o trecho apresentado e responder perguntas.
- Publicar no YouTube como público ou não listado; vídeo privado não atende ao enunciado.
- Testar os links sem login e preencher `ENTREGA.md`.
