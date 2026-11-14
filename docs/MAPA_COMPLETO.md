# Mapa com 71 regiões e ocupação ambígua

## Cadastro e exclusões

O mapa `dados/terceiros/vagas_completas_carpark.json` contém 71 retângulos em 1100 × 720: 69 vagas cadastradas e duas áreas centrais que exigem análise conjunta. Há seis setores de até 12 linhas. A ilha na primeira posição de F e os corredores ficam fora do mapa. V69 ocupa a segunda posição de F, imediatamente acima da V59, que faltava na versão anterior.

V01–V68 preservam os identificadores anteriores. V70 e V71 abrangem a van nas duas áreas centrais hachuradas (C9 e D9). Essas regiões são exibidas para revisão e não são acrescentadas à disponibilidade enquanto houver ambiguidade. As etiquetas normais são compactas; a seleção mostra estado e motivo. A lista tem rolagem.

## Método e calibração

O vídeo não fornece fundo vazio para todas as vagas: a maioria dos veículos permanece estacionada até o fim. O modo completo usa textura por limiarização adaptativa invertida, após tons de cinza e Gaussian 3 × 3; aplica mediana 5 × 5 e dilatação 3 × 3. A proporção de pixels marcados é medida dentro de cada polígono, com margem interna de três pixels para reduzir influência das linhas do piso. O recorte das máscaras preserva as coordenadas do vídeo.

Bloco adaptativo 25 e constante 16; limiares gerais livre ≤ 0,11 e ocupada ≥ 0,12. V06 e V18 usam livre ≤ 0,05 e ocupada ≥ 0,065, ajustados às superfícies lisas das vans. Não há estado ocupado fixado por configuração: a medida continua sendo calculada em cada quadro. Cinco quadros consecutivos confirmam uma candidatura; a faixa entre limiares conserva o estado anterior.

O arquivo `referencia_carpark.png` é usado somente para fornecer formato e resolução nesse modo. Seus pixels não entram na comparação por textura e ele não é tratado como imagem vazia do mapa completo. O modo anterior de diferença contra referência permanece disponível, com suas cinco regiões e rótulos separados.

## Ocupação de duas regiões

O grupo cadastrado `ambiguous_groups` une V70 e V71. No retângulo conjunto, o algoritmo encontra componentes claros conexos (cinza suavizado ≥ 180). Quando um mesmo componente cobre pelo menos 8% da máscara interna de cada região, ambas passam imediatamente a `indefinida`, exibida em amarelo como Em análise. A textura individual ainda é registrada, mas não produz uma indicação confiante de livre ou ocupada nesse par. O motivo vai para o CSV e para o detalhe da janela.

Se a conexão deixa de existir, o motivo é removido e os estados voltam a exigir cinco quadros consecutivos antes de serem confirmados. Não há estado amarelo fixado por ID ou por intervalo de tempo. O mecanismo é uma heurística restrita aos pares cadastrados, não reconhecimento semântico de vans, detecção de infração ou solução geral para todos os tipos de veículos. Objetos claros e marcas do piso podem provocar ambiguidade indevida.

No clipe incluído, V70 e V71 permaneceram em análise nos 679 quadros, com o motivo registrado em todas as 1.358 decisões do par. V69 está livre nos dois quadros da amostra.

## Rotulagem e resultados

`rotulos_completos_carpark.csv` contém 197 chaves únicas. Foram conferidas visualmente as 71 regiões nos quadros 60 e 678 e mantidos os 60 rótulos anteriores; cinco pares do quadro 60 se repetiriam e entram apenas uma vez. As vagas vazias no quadro 60 são V04, V05, V29, V41, V44, V45, V53, V55, V57, V65, V66 e V69. No quadro 678, V01, V02 e V03 também estão vazias; as demais regiões têm veículos visíveis. V70 e V71 foram rotuladas como ocupadas pela presença visível da van, mas o algoritmo se abstém de decidir a ocupação individual: suas quatro amostras entram como indefinidas no cálculo de cobertura, sem serem ocultadas.

| Medida | Resultado |
|---|---:|
| Quadros | 679 |
| Regiões cadastradas | 71 |
| Decisões | 48.209 |
| Eventos incluindo inicialização | 76 |
| Rótulos visuais | 197 |
| Concordantes | 185 |
| Indefinidos | 9 |
| Divergentes definidos | 3 |
| Concordância total | 93,91% |
| Cobertura | 95,43% |
| Acurácia somente definida | 98,40% |
| TP / TN / FP / FN | 116 / 69 / 1 / 2 |
| Quadro 60: livres / ocupadas / análise | 12 / 57 / 2 |
| Quadro 678: livres / ocupadas / análise | 15 / 54 / 2 |

Cinco dos nove indefinidos pertencem à amostra do quadro zero, antes da inicialização temporal. Os outros quatro são as abstenções intencionais do par central nos quadros 60 e 678. As três divergências são V01 no quadro 120 e V02 no quadro 180 (liberação antecipada pelo algoritmo enquanto a anotação ainda considera a vaga ocupada), e V03 no quadro 360 (ainda ocupada durante a confirmação de saída). O algoritmo confirma livre em V01/118, V02/172 e V03/370. Esses são instantes do classificador, não medidas da saída física completa.

O histórico completo também contém falsas mudanças de V55 durante passagem de pessoas/sombras: livre → ocupada → livre nos intervalos 126–140 e 443–512. A amostra pontual de 197 rótulos não captura todos os erros ao longo do vídeo; não apresentar sua concordância como precisão integral de cada decisão.

Os instantes acima são da execução Windows registrada. Na execução Linux dos testes, V01 foi confirmada no quadro 117 em vez de 118. As duas plataformas podem produzir pequenas diferenças na análise da imagem; o histórico sempre busca o índice efetivamente gravado em `eventos.csv`.

## Limites e reprodução

Regiões, parâmetros e avaliação usam o mesmo clipe. A amostra não é validação independente nem mede generalização. Textura não reconhece semanticamente um automóvel: pessoas, sombras e marcas do piso podem gerar falsos positivos; veículos lisos e saídas parciais podem gerar falsos negativos. A câmera deve permanecer fixa.

Execute `python executar_exemplo.py --completo` ou abra `aplicativo.py`. O CSV usa `densidade_textura`; o experimento anterior usa `fracao_alterada`. O campo `metodo` no resumo distingue as saídas. O aplicativo rejeita um resumo com quantidade de vagas ou método incompatíveis com seu mapa.

O vídeo original e seus limites de licença/autoria estão em [FONTES_MIDIA.md](FONTES_MIDIA.md). A coleta própria e os conjuntos independentes ainda precisam ser produzidos pelo grupo.
