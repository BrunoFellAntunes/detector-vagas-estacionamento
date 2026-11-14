# Produto

## Plataforma

Aplicativo de desktop para Windows, com janela nativa.

## Tecnologia

Python e OpenCV implementam a classificação. A interface nativa usa PySide6 Essentials. Não há servidor, hospedagem ou conexão de rede durante a apresentação.

## Pessoas e uso

Vitor Rodi, Pedro Toigo, Bruno Fell Antunes e Edson Leandro Soares apresentarão o projeto de Robótica e Visão Computacional ao professor Wagner Titon, na Unochapecó. A interface deve tornar visíveis o vídeo, a disponibilidade de vagas e o funcionamento do projeto durante uma apresentação de até dez minutos.

## Finalidade

Reproduzir uma gravação e mostrar o resultado do detector para cada vaga monitorada, com contagens sincronizadas de vagas livres, ocupadas e ainda em análise. Permitir pausar, avançar na gravação e destacar uma vaga para explicar o resultado.

Permitir cadastrar outros estacionamentos em Vídeos e vagas, dentro do painel principal. O usuário importa um vídeo local, desenha e ajusta regiões com o mouse, confere a classificação pontual e salva um perfil. Cada edição gera uma revisão com resultados separados; perfis sem alterações podem reabrir uma análise completa. A câmera deve permanecer fixa e a classificação exige conferência por local.

## Evidências existentes

O projeto inclui um vídeo externo de estacionamento com 679 quadros a 24 FPS, 71 regiões cadastradas, com classificação por textura e confirmação temporal. A execução exporta ocupação, eventos e avaliação exploratória. A amostra tem 197 rótulos: 185 concordantes, nove indefinidos e três divergentes. Os resultados são do mesmo clipe usado no cadastro e não constituem validação independente.

## Restrições

- Exibir as 71 regiões cadastradas, incluindo o par central para análise conjunta e a vaga acima da V59; excluir ilhas e corredores.
- Identificar a gravação como demonstração, sem simular uma câmera ao vivo.
- Associar cor e texto aos estados para que o resultado não dependa somente de cor.
- Não inventar sensores, câmeras, redes neurais, dados de campo ou precisão de generalização.
- Manter os programas de linha de comando e os testes existentes.
- Manter o editor na mesma janela, com rascunho preservado ao alternar páginas durante a sessão.
- Guardar perfis e caminhos dos vídeos apenas localmente; não herdar métricas de avaliação da demonstração em novos vídeos.
- Publicar código, instruções e mudanças reais no repositório público.
