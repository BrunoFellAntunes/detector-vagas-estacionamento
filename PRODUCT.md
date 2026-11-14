# Produto

## Plataforma

Aplicativo de desktop para Windows, com janela nativa.

## Tecnologia

Python e OpenCV implementam a classificação. A interface nativa usa PySide6 Essentials. Não há servidor, hospedagem ou conexão de rede durante a apresentação.

## Pessoas e uso

Vitor Rodi, Pedro Toigo, Bruno Fell Antunes e Edson Leandro Soares apresentarão o projeto de Robótica e Visão Computacional ao professor Wagner Titon, na Unochapecó. A interface deve tornar visíveis o vídeo, a disponibilidade de vagas e o funcionamento do projeto durante uma apresentação de até dez minutos.

## Finalidade

Reproduzir uma gravação e mostrar o resultado do detector para cada vaga monitorada, com contagens sincronizadas de vagas livres, ocupadas e ainda em análise. Permitir pausar, avançar na gravação e destacar uma vaga para explicar o resultado.

## Evidências existentes

O projeto inclui um vídeo externo de estacionamento com 679 quadros a 24 FPS, 68 regiões cadastradas, com classificação por textura e confirmação temporal. A execução exporta ocupação, eventos e avaliação exploratória. A amostra tem 191 rótulos: 183 concordantes, cinco indefinidos e três divergentes. Os resultados são do mesmo clipe usado no cadastro e não constituem validação independente.

## Restrições

- Exibir as 68 vagas cadastradas, excluindo ilhas, corredores e o obstáculo central.
- Identificar a gravação como demonstração, sem simular uma câmera ao vivo.
- Associar cor e texto aos estados para que o resultado não dependa somente de cor.
- Não inventar sensores, câmeras, redes neurais, dados de campo ou precisão de generalização.
- Manter os programas de linha de comando e os testes existentes.
- Publicar código, instruções e mudanças reais no repositório público.
