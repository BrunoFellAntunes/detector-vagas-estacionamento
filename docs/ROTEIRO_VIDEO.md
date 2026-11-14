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

Mostrar brevemente `detector.py` e o diagrama verbal: câmera fixa → tons de cinza e suavização → diferença para referência vazia → máscara de cada vaga → fração de pixels alterados → confirmação temporal → contagem e registro.

Fala central: “Usamos Python, OpenCV e NumPy. Não treinamos uma rede neural. Cadastramos as vagas manualmente e medimos quanto sua aparência muda em relação a uma imagem vazia. O valor exibido é uma fração de pixels alterados, não uma probabilidade de haver um carro.”

Explicar os dois limiares e os cinco quadros de confirmação. Justificar a referência fixa: um veículo que permanece parado deve continuar sendo percebido como ocupação. Explicar que alterações de sombra também podem causar erro. Transição: “Agora vamos executar o programa e acompanhar o que acontece em cada vaga.”

## Bruno Fell Antunes inicia a demonstração

Mostrar a referência vazia e o arquivo de polígonos. Abrir a calibração, selecionar uma vaga, confirmar e explicar como o JSON registra a resolução e as coordenadas. Usar uma cópia de configuração no ensaio para preservar a versão demonstrada.

Executar o detector no terminal e mostrar a saída anotada, com um estado livre e outro ocupado. Explicar o significado de verde, vermelho e amarelo. Demonstrar que a contagem acompanha os estados e que uma alteração fora de uma região não deveria mudar aquela vaga.

Para ensaiar com dados simulados:

```powershell
.\.venv\Scripts\python.exe demo.py
.\.venv\Scripts\python.exe detector.py --source dados/cena_simulada.png --reference dados/referencia_vazia.png --config dados/vagas_demo.json --output resultados/imagem --show
```

O exemplo real já cadastrado pode ser aberto com `.\.venv\Scripts\python.exe executar_exemplo.py --show`. Ele monitora cinco regiões do vídeo de terceiros; explicar a origem, a referência do quadro 678 e a seleção das regiões conforme `EXPERIMENTO_REAL.md`. A janela pode ser pausada com espaço para explicar as saídas. Para uma gravação própria, seguir `COLETA_REAL.md`. Mostrar o comando completo e pelo menos um trecho do processamento. A demonstração deve usar o mesmo código publicado no GitHub.

## Edson Leandro Soares continua a demonstração

Mostrar uma entrada de veículo e uma saída. Destacar os cinco quadros de confirmação e o pequeno atraso introduzido. Mostrar um veículo parado mantendo o estado ocupado. Se a coleta tiver falhas com sombras, mostrar um exemplo e explicar a limitação.

Abrir `ocupacao.csv` e explicar quadro, tempo estimado, vaga, estado e fração alterada. Abrir o vídeo exportado. Não apresentar o FPS do arquivo como velocidade medida do algoritmo.

Para ensaio reproduzível:

```powershell
.\.venv\Scripts\python.exe detector.py --source dados/video_simulado.mp4 --reference dados/referencia_vazia.png --config dados/vagas_demo.json --output resultados/video
.\.venv\Scripts\python.exe verificar_demo.py
```

O vídeo simulado tem somente 12 segundos. O período de demonstração inclui a execução, o cadastro, a explicação dos estados e as exportações; não é necessário esticar ou repetir a reprodução para preencher quatro minutos.

## Os quatro apresentam os resultados e encerram

Vitor: relatar os resultados reais medidos e retomar o objetivo de apresentar disponibilidade. Se houver apenas simulação, dizer que o funcionamento foi verificado em cenário controlado e que a efetividade no local ainda não foi demonstrada.

Pedro: explicar uma dificuldade técnica efetivamente observada, como alinhamento da câmera, limiares ou oscilação entre quadros. Evitar relatar problemas que o grupo não verificou.

Bruno: comentar referência vazia, sombras, oclusão e mudança de iluminação. Como melhorias, propor calibração por condição de luz, avaliação com mais sequências ou comparação com um classificador treinado. Identificar propostas como trabalho futuro.

Edson: concluir o que foi demonstrado e mostrar o repositório público. Informar que a reprodução está descrita no README e encerrar antes de dez minutos. Não inventar endereço do YouTube antes de publicar.

## Conferência antes de gravar

- Ensaiar o percurso com os quatro integrantes e cronometrar.
- Testar microfones, volume e captura da tela; deixar o texto do terminal legível.
- Fechar abas pessoais e notificações antes da captura.
- Mostrar entradas, programa e saídas em vez de apresentar exclusivamente slides.
- Gravar as próprias falas. Cada integrante deve conseguir explicar o trecho apresentado e responder perguntas.
- Publicar no YouTube como público ou não listado; vídeo privado não atende ao enunciado.
- Testar os links sem login e preencher `ENTREGA.md`.
