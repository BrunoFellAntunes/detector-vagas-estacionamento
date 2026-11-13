# Gravação e validação no estacionamento

Este guia prepara a coleta real. Até o momento, o projeto contém apenas cenas simuladas. Registrar o que foi observado e obtido em campo sem completar resultados com suposições.

## Escolher o local

Escolham um estacionamento autorizado com três a seis vagas visíveis a partir de um ponto fixo. Prefiram uma posição elevada e protegida, sem que carros de uma fileira escondam as vagas de outra. Registrem o local, a data, o período de observação, as pessoas consultadas e as dificuldades relatadas. Não afirmar que o problema ocorre na Unochapecó sem investigação no local.

Concluam a observação ou entrevista prevista na etapa 1. Perguntas úteis: como o usuário procura vagas; quando encontra mais dificuldade; o que dificulta perceber vagas livres; se uma indicação centralizada seria útil. Registrem as respostas reais e a quantidade de participantes, sem inventar depoimentos ou benefícios quantitativos.

## Montar a câmera

Pode ser usado celular ou webcam. Fixem o equipamento em um suporte; a câmera não pode ser movimentada entre a referência e os trechos de avaliação. Usem orientação horizontal e mantenham a resolução original. Desativem zoom automático e mudanças de enquadramento. Se possível, mantenham foco e exposição estáveis. Não fiquem em áreas de circulação para gravar.

O detector exige uma visão sem veículo de **cada vaga cadastrada** na referência. Não é necessário que todo o estacionamento esteja vazio; selecionem somente vagas que estiverem vazias no quadro escolhido. Se não houver esse quadro para as vagas desejadas, mudem o conjunto de vagas ou aguardem outra oportunidade.

## Sequência de gravação

1. Comecem com as vagas escolhidas vazias e registrem alguns segundos estáveis.
2. Gravem um veículo entrando em uma das vagas e permanecendo parado.
3. Mantenham pelo menos uma vaga vazia para comparar.
4. Gravem a saída do veículo e a liberação da vaga.
5. Se possível, registrem outra ocupação e uma sombra ou passagem de pessoa para observar limitações.
6. Façam uma segunda sequência para avaliação, sem ajustar parâmetros com base nela.

Um trecho de um a três minutos pode ser suficiente para a demonstração. Isso não garante uma amostra representativa de todas as condições do estacionamento. Variações de dia, chuva e luz exigem coletas adicionais.

## Preparar o vídeo

Guardem o vídeo em `dados/reais/video_real.mp4`. A pasta é ignorada pelo Git para que gravações não sejam publicadas sem revisão. No terminal, a partir da raiz do projeto:

```powershell
.\.venv\Scripts\python.exe extrair_referencia.py --video dados/reais/video_real.mp4 --quadro 0 --output dados/reais/referencia.png --confirmar-vagas-vazias
.\.venv\Scripts\python.exe calibrar.py --reference dados/reais/referencia.png --output dados/reais/vagas.json
.\.venv\Scripts\python.exe detector.py --source dados/reais/video_real.mp4 --reference dados/reais/referencia.png --config dados/reais/vagas.json --output resultados/real --show
```

Antes do primeiro comando, visualizem o vídeo e escolham um quadro em que as vagas a cadastrar estejam vazias. O índice começa em zero. O script extrai exatamente o quadro solicitado, preservando a resolução do vídeo, e recusa sobrescrever uma referência já existente. A opção de confirmação representa uma verificação humana, não uma classificação automática.

Não alterem o tamanho nem recortem o vídeo depois de cadastrar as vagas. Na janela de calibração, cliquem os quatro cantos em ordem ao redor da vaga. N confirma; U desfaz; S salva depois que todas as vagas estiverem confirmadas; Esc cancela. Confiram os rótulos na saída e testem esse procedimento no computador da apresentação.

## Registro mínimo da coleta

Criem um registro local com: local, data, horário, equipamento, resolução, FPS do arquivo, número de vagas cadastradas, iluminação, origem e permissão dos arquivos, índices dos eventos de entrada e saída e alterações de câmera. Anotem se houve observação ou entrevista, seu período e as conclusões reais do grupo.

Revisem a exposição de pessoas e placas antes de publicar qualquer material. Para permitir reprodução pública, publiquem somente os trechos autorizados. Se for necessário ocultar informações, apliquem a mesma transformação à referência e aos vídeos e garantam que ela não interfira nas vagas avaliadas. Não apliquem desfoque apenas em um dos dois arquivos usados na comparação.

## Avaliar

Separem uma sequência para calibração e outra para avaliação. Ajustem `pixel_threshold`, `free_ratio`, `occupied_ratio` e `stable_frames` apenas na primeira. Na segunda, rotulem manualmente vaga e quadro e comparem com `ocupacao.csv`.

Relatem acertos, erros, estados indefinidos e atraso de transição. A medida `fracao_alterada` não é confiança do modelo. Não usem 97,78% da simulação como precisão real. Não meçam FPS apenas pelo valor de reprodução do arquivo: velocidade do algoritmo exige medir quadros processados por tempo de execução no computador utilizado.
