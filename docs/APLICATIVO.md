# Aplicativo Vaga

A interface nativa usa o detector e os arquivos de análise deste repositório. Ela reproduz uma gravação e sincroniza cada imagem com os estados calculados para 71 regiões. A janela apresenta a gravação incluída; ilhas e corredores ficam fora do mapa; as duas áreas da van central são monitoradas para análise conjunta.

## Instalação e abertura

No Windows, instale Python 3.10 ou mais recente e execute `INICIAR_APLICATIVO.bat`, na raiz do projeto. A primeira abertura cria `.venv` e instala as dependências, com internet. As próximas aberturas usam os arquivos locais. Extraia o ZIP antes de executar; mantenha juntos código, fontes e pasta `dados/`.

Alternativa pelo terminal na raiz do projeto:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-app.txt
.\.venv\Scripts\python.exe aplicativo.py
```

Em Linux, use `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements-app.txt` e `.venv/bin/python aplicativo.py`. A máquina precisa de uma sessão gráfica para mostrar a janela. No Ubuntu, o Qt também precisa da biblioteca EGL: `sudo apt-get install libegl1`. Os testes automatizados instalam essa biblioteca e executam Qt em modo offscreen.

O programa analisa o vídeo completo ao abrir. Durante o processamento, os controles ficam desabilitados e os contadores mostram traços. Depois de conferir os 679 quadros, a janela abre pausada no quadro 60, aproximadamente dois segundos após o início. O botão **Reiniciar** permite observar os primeiros quadros em análise.

Para reutilizar resultados completos de uma execução anterior:

```powershell
.\.venv\Scripts\python.exe aplicativo.py --usar-resultados
```

## Controles

| Controle | Ação |
|---|---|
| Reproduzir / Pausar | Avança ou congela vídeo, contadores e estados |
| Reiniciar, ao lado de Reproduzir | Retorna ao primeiro quadro e pausa |
| Barra de posição | Busca um quadro ao soltar o controle |
| Velocidade | Reprodução em 0,5×, 1×, 1,5× ou 2× |
| Marcações | Mostra ou oculta polígonos e etiquetas no vídeo |
| Filtro de vagas | Restringe a lista por estado, sem alterar o total dos contadores |
| Vaga na lista ou região no vídeo | Destaca a mesma vaga e mostra sua densidade de textura |
| Últimas alterações | Clique em uma mudança para voltar ao quadro em que foi confirmada |
| Reprocessar | Executa novamente o detector e substitui a análise anterior |
| Apresentar / F11 | Entra ou sai da tela cheia, ocultando a barra lateral e o rodapé |
| Esc | Sai da tela cheia; na janela normal, pausa a reprodução |
| Tab / Shift+Tab | Percorre os controles, com foco visível |
| Espaço | Aciona o botão com foco; com o vídeo em foco, alterna reprodução e pausa |
| Sobre o projeto | Método, equipe, origem da filmagem, resultados e limitações |

A navegação usa uma lateral azul-escura e os contadores destacam os totais do quadro atual. A lista mostra etiquetas de estado com texto e fundo colorido. Os controles reservam o mesmo contorno em repouso, seleção e foco, evitando deslocamentos durante a navegação.

Verde significa **Livre**, vermelho significa **Ocupada** e amarelo significa **Em análise**. Os estados também aparecem por escrito. A textura detectada é a proporção de pixels marcados pelo processamento dentro da vaga, não uma probabilidade de haver um carro. As 71 regiões têm retângulos compactos e a lista tem rolagem.

O histórico inclui somente mudanças confirmadas até o instante mostrado; as confirmações iniciais não são exibidas como entradas ou saídas. Buscar um instante anterior também recua o histórico. Ao terminar a gravação, Reproduzir começa novamente no início.

Ao selecionar V70 ou V71, o detalhe mostra o motivo da análise conjunta. O amarelo não significa vaga disponível: indica que o programa não confirma a ocupação individual porque um mesmo objeto claro atravessa as duas regiões. A V69, acima da V59, participa normalmente da classificação.

## Exportações

**Exportar resultados** abre o seletor de destino para um ZIP com `ocupacao.csv`, `eventos.csv`, `resumo.json`, `avaliacao.json`, `ultimo_quadro.png` e `video_anotado.mp4`. São os resultados da análise completa, independentemente do filtro ou quadro mostrado. O arquivo de destino é escrito de forma temporária antes de substituir o ZIP escolhido.

Os resultados originais ficam em `resultados/carpark/`. O botão Reprocessar invalida os resumos anteriores antes de analisar novamente; uma execução incompleta não deve ser apresentada como análise concluída. Fechar a janela durante o processamento encerra o processo do detector.

## Ensaio para a apresentação

1. Abra o aplicativo e aguarde a análise. Mostre 12 estados livres, 57 ocupados e dois em análise no instante inicial exibido.
2. Reproduza a gravação. V01, V02 e V03 são confirmadas pelo algoritmo como livres nos quadros 118, 172 e 370, respectivamente.
3. Pause, selecione uma vaga e compare o destaque no vídeo com o texto da lista.
4. Aplique o filtro Somente livres e volte a uma alteração pelo histórico.
5. Use Apresentar para mostrar a gravação em tela cheia; volte com Esc e clique em Pausar.
6. Exporte o ZIP e explique uma linha do CSV. Abra Sobre o projeto para discutir resultados e limitações.

O clipe contém saídas de V01, V02 e V03. O classificador também registra falsas mudanças em V55 durante passagem de pessoas/sombras; apresente essa limitação. Não há entradas de veículos estacionando no clipe. Para mostrar uma entrada, use o cenário simulado ou uma coleta própria que contenha essa situação e identifique a origem do material.

## Solução de problemas

- Se a instalação falhar, execute os comandos pelo terminal para ler a mensagem completa. Confira Python, acesso à internet na instalação e permissão de escrita na pasta.
- Se a análise falhar, confira os arquivos em `dados/terceiros/` e clique em Reprocessar. Os contadores não mostram disponibilidade enquanto a análise estiver indisponível.
- Se `--usar-resultados` rejeitar uma análise, abra sem essa opção para gerar uma execução completa.
- Se a busca no vídeo falhar, a reprodução pausa e exibe a mensagem. Reprocesse ou confira a integridade do arquivo.
- As fontes Sora e Manrope são distribuídas localmente, com suas licenças em `app/fonts/`; preserve essa pasta ao copiar o projeto.

O tamanho mínimo da janela é 1060 × 700 pixels lógicos. Foram inspecionadas capturas em 1060 × 700, 1440 × 760 e 1440 × 900, incluindo estados de carregamento, falha, filtros vazios e foco de teclado. A coleta com câmera física e a validação em gravações independentes continuam pendentes.
