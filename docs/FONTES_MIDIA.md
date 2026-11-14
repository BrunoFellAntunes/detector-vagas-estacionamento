# Fontes dos arquivos de mídia

## Vídeo externo de estacionamento

Arquivo: `dados/terceiros/carPark.mp4`.

Fonte de obtenção: [harshbafnaa/car-parking-detection](https://github.com/harshbafnaa/car-parking-detection), projeto de Harsh Bafna. [Arquivo na revisão utilizada](https://github.com/harshbafnaa/car-parking-detection/blob/a35ce5055beb2d50eac971254720892944e0f7fb/carPark.mp4).

O [README da fonte](https://github.com/harshbafnaa/car-parking-detection/blob/a35ce5055beb2d50eac971254720892944e0f7fb/README.md#license) declara licença MIT para o projeto. A origem não contém um arquivo LICENSE separado nem uma declaração específica sobre a autoria da filmagem. O crédito ao responsável pelo repositório identifica a fonte de obtenção; não atribui a ele a gravação original. O arquivo foi mantido sem alterações.

Obtido em 13/11/2026. Resolução: 1100 × 720 pixels. Taxa: 24 quadros por segundo. Total: 679 quadros, todos decodificados na conferência local. Duração aproximada: 28,29 segundos. Tamanho: 10.607.736 bytes.

SHA-256:

```text
f2d804e9b2e8ff7e0ae9776068a9cbc8126b6bce2e09ef6f56d3ad9c8fe84069
```

Este material é uma entrada externa para testes. Não foi gravado pelo grupo, não substitui a investigação do problema e sua inclusão não comprova o desempenho do detector. Na apresentação, identificar a origem ao mostrar o vídeo.

`dados/terceiros/referencia_carpark.png` é um quadro derivado dessa mesma filmagem, extraído sem recorte do índice 678. `assets/demonstracao_real.png` mostra um quadro da filmagem processado pelo detector. `vagas_carpark.json` registra as regiões cadastradas e `rotulos_carpark.csv` contém a rotulagem visual da amostra. O procedimento e os resultados estão em [EXPERIMENTO_REAL.md](EXPERIMENTO_REAL.md).

## Demonstração simulada

As imagens, o vídeo e o gabarito em `dados/` são gerados por `demo.py`. A imagem em `assets/demonstracao_simulada.png` mostra o resultado do processamento dessa simulação. Esses arquivos permanecem separados da filmagem externa e das futuras gravações do grupo.


## Interface e tipografia

`assets/aplicativo.png` é uma captura da janela real implementada neste repositório, em 1440 × 900, mostrando o quadro 60 da filmagem externa. Os polígonos e estados vêm dos resultados do detector. `assets/editor-vagas.png` mostra o editor integrado ao painel principal, com uma cópia do mesmo mapa nesse quadro. O azul identifica o cadastro, sem afirmar um estado de ocupação. As capturas não são montagens nem comprovação de desempenho em outras gravações. As imagens em `assets/` também carregam um registro de origem em seus metadados PNG.

As fontes locais [Sora](https://github.com/google/fonts/tree/main/ofl/sora) e [Manrope](https://github.com/google/fonts/tree/main/ofl/manrope) foram obtidas do repositório oficial Google Fonts. São redistribuídas sob a SIL Open Font License, com os textos de licença em `app/fonts/Sora-OFL.txt` e `app/fonts/Manrope-OFL.txt`. Os arquivos TTF são carregados localmente pela interface; não há busca de fontes durante o uso.

Os ícones SVG e o símbolo P da janela são desenhados no código do aplicativo.


O mapa completo em `vagas_completas_carpark.json` e os 197 rótulos em `rotulos_completos_carpark.csv` foram cadastrados para esta mesma filmagem. Não são anotações fornecidas pelo autor do vídeo nem dados de campo independentes. A captura atual de `assets/aplicativo.png` mostra as 71 regiões no quadro 60.
