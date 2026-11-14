# Experimento com 68 vagas

## Cadastro e exclusões

O mapa `dados/terceiros/vagas_completas_carpark.json` contém 68 retângulos conferidos visualmente sobre a filmagem original, em 1100 × 720. Há seis colunas (setores A a F) e até 12 linhas. Os setores A, B e E possuem 12 vagas cada; C e D possuem 11 cada, excluindo a linha 9 ocupada pelo obstáculo central; F possui dez, começando na linha 3 porque as duas primeiras posições são ilha/calçada. Corredores e veículos em circulação não são vagas adicionais.

V01–V05 mantêm as posições do experimento anterior, agora com retângulos que abrangem as vagas. V06–V68 completam o mapa. Os rótulos normais na janela mostram apenas o identificador; selecionar uma região mostra também seu estado. A lista possui rolagem para acessar todas as vagas.

## Método e calibração

O vídeo não fornece fundo vazio para todas as vagas: a maioria dos veículos permanece estacionada até o fim. O modo completo usa textura por limiarização adaptativa invertida, após tons de cinza e Gaussian 3 × 3; aplica mediana 5 × 5 e dilatação 3 × 3. A proporção de pixels marcados é medida dentro de cada polígono, com margem interna de três pixels para reduzir influência das linhas do piso. O recorte das máscaras preserva as coordenadas do vídeo.

Bloco adaptativo 25 e constante 16; limiares gerais livre ≤ 0,11 e ocupada ≥ 0,12. V06 e V18 usam livre ≤ 0,05 e ocupada ≥ 0,065, ajustados às superfícies lisas das vans. Não há estado ocupado fixado por configuração: a medida continua sendo calculada em cada quadro. Cinco quadros consecutivos confirmam uma candidatura; a faixa entre limiares conserva o estado anterior.

O arquivo `referencia_carpark.png` é usado somente para fornecer formato e resolução nesse modo. Seus pixels não entram na comparação por textura e ele não é tratado como imagem vazia das 68 vagas. O modo anterior de diferença contra referência permanece disponível, com suas cinco regiões e rótulos separados.

## Rotulagem e resultados

`rotulos_completos_carpark.csv` contém 191 chaves únicas. Foram conferidas visualmente todas as 68 vagas nos quadros 60 e 678 e mantidos os 60 rótulos anteriores; cinco pares do quadro 60 se repetiriam e entram apenas uma vez. As vagas vazias no quadro 60 são V04, V05, V29, V41, V44, V45, V53, V55, V57, V65 e V66. No quadro 678, V01, V02 e V03 também estão vazias; as demais regiões têm veículos visíveis.

| Medida | Resultado |
|---|---:|
| Quadros | 679 |
| Vagas | 68 |
| Decisões | 46.172 |
| Eventos incluindo inicialização | 75 |
| Rótulos visuais | 191 |
| Concordantes | 183 |
| Indefinidos | 5 |
| Divergentes definidos | 3 |
| Concordância total | 95,81% |
| Cobertura | 97,38% |
| Acurácia somente definida | 98,39% |
| TP / TN / FP / FN | 116 / 67 / 1 / 2 |
| Quadro 60: livres / ocupadas | 11 / 57 |
| Quadro 678: livres / ocupadas | 14 / 54 |

Os cinco indefinidos pertencem à amostra do quadro zero, antes da inicialização temporal. As três divergências são V01 no quadro 120 e V02 no quadro 180 (liberação antecipada pelo algoritmo enquanto a anotação ainda considera a vaga ocupada), e V03 no quadro 360 (ainda ocupada durante a confirmação de saída). O algoritmo confirma livre em V01/118, V02/172 e V03/370. Esses são instantes do classificador, não medidas da saída física completa.

O histórico completo também contém falsas mudanças de V55 durante passagem de pessoas/sombras: livre → ocupada → livre nos intervalos 126–140 e 443–512. A amostra pontual de 191 rótulos não captura todos os erros ao longo do vídeo; não apresentar sua concordância como precisão integral de cada decisão.

Os instantes acima são da execução Windows registrada. Na execução Linux dos testes, V01 foi confirmada no quadro 117 em vez de 118. As duas plataformas podem produzir pequenas diferenças na análise da imagem; o histórico sempre busca o índice efetivamente gravado em `eventos.csv`.

## Limites e reprodução

Regiões, parâmetros e avaliação usam o mesmo clipe. A amostra não é validação independente nem mede generalização. Textura não reconhece semanticamente um automóvel: pessoas, sombras e marcas do piso podem gerar falsos positivos; veículos lisos e saídas parciais podem gerar falsos negativos. A câmera deve permanecer fixa.

Execute `python executar_exemplo.py --completo` ou abra `aplicativo.py`. O CSV usa `densidade_textura`; o experimento anterior usa `fracao_alterada`. O campo `metodo` no resumo distingue as saídas. O aplicativo rejeita um resumo com quantidade de vagas ou método incompatíveis com seu mapa.

O vídeo original e seus limites de licença/autoria estão em [FONTES_MIDIA.md](FONTES_MIDIA.md). A coleta própria e os conjuntos independentes ainda precisam ser produzidos pelo grupo.
