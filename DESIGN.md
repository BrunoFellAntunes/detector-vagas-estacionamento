---
name: "Vaga"
description: "Sinalização clara para acompanhar a disponibilidade de vagas em uma gravação."
colors:
  primary: "#355bd5"
  primary-hover: "#284ac1"
  primary-focus: "#173a7a"
  focus: "#486bd5"
  canvas-focus: "#6488f5"
  window: "#f0f3f8"
  sidebar: "#e5ecf8"
  surface: "#ffffff"
  text: "#253b50"
  heading: "#192f49"
  section: "#223a53"
  brand: "#1d3a6f"
  muted: "#596d82"
  small: "#526681"
  free-text: "#19734f"
  occupied-text: "#b34f48"
  analysis-text: "#966719"
  free-overlay: "#31b77b"
  occupied-overlay: "#ed7168"
  analysis-overlay: "#efbd54"
  border: "#d5deeb"
  hover: "#edf2fc"
  pressed: "#dfe8f9"
  disabled-text: "#8290a3"
  disabled-surface: "#e9edf3"
  primary-disabled: "#91a5d9"
  nav-text: "#425c7a"
  nav-selected: "#294bc1"
  field: "#f8faff"
  field-border: "#d8e1ee"
  space-border: "#e3e9f1"
  space-selected: "#edf2ff"
  space-selected-border: "#5271d7"
  space-focus: "#e1eaff"
  video: "#192e3e"
  overlay-label: "#152a3b"
  video-message: "#f3f7fc"
  video-detail: "#b5c9dc"
  timeline: "#dfe6f1"
  timeline-progress: "#4264d3"
  divider: "#e6ebf2"
typography:
  display:
    fontFamily: "Sora"
    fontSize: "32px"
    fontWeight: 600
  brand:
    fontFamily: "Sora"
    fontSize: "30px"
    fontWeight: 700
  heading:
    fontFamily: "Sora"
    fontSize: "26px"
    fontWeight: 600
  title:
    fontFamily: "Sora"
    fontSize: "14px"
    fontWeight: 600
  body:
    fontFamily: "Manrope"
    fontSize: "13px"
  label:
    fontFamily: "Manrope"
    fontSize: "12px"
    fontWeight: 600
  small:
    fontFamily: "Manrope"
    fontSize: "11px"
  overlay:
    fontFamily: "Manrope"
    fontSize: "12px"
    fontWeight: 700
rounded:
  track: "3px"
  overlay: "4px"
  field: "7px"
  control: "8px"
  video: "10px"
  panel: "14px"
spacing:
  step-4: "4px"
  step-8: "8px"
  step-10: "10px"
  step-12: "12px"
  step-16: "16px"
  step-18: "18px"
  step-20: "20px"
  step-24: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-primary-disabled:
    backgroundColor: "{colors.primary-disabled}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  nav:
    backgroundColor: "transparent"
    textColor: "{colors.nav-text}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
  nav-selected:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.nav-selected}"
  combo:
    backgroundColor: "{colors.field}"
    textColor: "{colors.text}"
    rounded: "{rounded.field}"
    padding: "7px 10px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
  space:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "5px 10px"
  space-selected:
    backgroundColor: "{colors.space-selected}"
  video:
    backgroundColor: "{colors.video}"
    rounded: "{rounded.video}"
  overlay-label:
    backgroundColor: "{colors.overlay-label}"
    rounded: "{rounded.overlay}"
    typography: "{typography.overlay}"
    height: "21px"
---
# Sistema visual: Vaga

## Overview

**Creative North Star: "Sinalização de transporte"**

A sinalização de transporte orienta o sistema: azuis claros organizam a janela, azul profundo dá estrutura ao texto e as cores de estado fazem o resultado aparecer imediatamente. A composição é serena, funcional e legível durante uma apresentação.

Os controles preservam a familiaridade de um aplicativo nativo Windows. A imagem real do estacionamento ocupa a maior área; contagens, rótulos e seleção conectam a gravação ao resultado do detector. Informação técnica e créditos usam uma hierarquia discreta.

**Key Characteristics:**

- Superfícies claras e planas, separadas por contraste tonal e espaço.
- Títulos Sora e leitura Manrope, com fontes distribuídas junto ao aplicativo.
- Estados comunicados por texto e cor, inclusive sobre o vídeo.
- Controles com contornos de foco explícitos e seleção persistente.

Este documento registra a interface nativa implementada em Qt/PySide6, com estilo QSS e desenho direto sobre o vídeo. Os tokens acima descrevem valores existentes; não pressupõem uma interface web. As medidas são unidades lógicas do Qt e acompanham a escala de exibição do Windows.

## Colors

A paleta combina branco, azuis acinzentados e um azul de ação, reservando verde, vermelho e âmbar para os estados. Os valores normativos estão no frontmatter.

### Primary

- **Azul de ação** (`primary`): botões de reprodução e apresentação, progresso e elementos interativos.
- **Azul pressionado e de foco** (`primary-hover`, `primary-focus`, `focus`, `canvas-focus`): diferencia estados dos controles e mantém o foco perceptível.

### Secondary

- **Verde de disponibilidade** (`free-text`, `free-overlay`): vaga livre; a versão escura serve à leitura sobre branco e a clara às marcações sobre imagem.
- **Vermelho de ocupação** (`occupied-text`, `occupied-overlay`): vaga ocupada, com a mesma separação entre texto e imagem.
- **Âmbar de análise** (`analysis-text`, `analysis-overlay`): resultado ainda indefinido, acompanhado de “Em análise”.

### Neutral

- **Azul de fundo** (`window`) e **azul de navegação** (`sidebar`): separam o espaço de trabalho da faixa lateral.
- **Branco de painel** (`surface`): contagens, vídeo e lista de vagas.
- **Azuis de leitura** (`text`, `heading`, `section`, `brand`, `muted`, `small`): hierarquia de títulos, conteúdo, identificação e informações auxiliares.
- **Azul noturno** (`video`, `overlay-label`): margem do vídeo, estados sem imagem e suporte aos rótulos sobrepostos.
- **Bordas e estados claros** (`border`, `field-border`, `space-border`, `hover`, `pressed`, `space-selected`): separação e resposta dos controles.

**The Estado Legível Rule.** Estado sempre combina texto e cor; seleção e foco usam contorno, sem substituir a informação de ocupação.

## Typography

**Display Font:** Sora. **Body Font:** Manrope. As duas famílias são carregadas dos arquivos locais em `app/fonts`; não há fallback de marca declarado. O estilo nativo usado é Fusion.

Sora confere precisão aos títulos e aos números; Manrope mantém controles e descrições compactos. A interface não aplica caixa alta ou espaçamento artificial como padrão.

### Hierarchy

- **Display:** números dos contadores; papel `display`.
- **Marca:** nome Vaga na lateral; papel `brand`.
- **Heading:** título da página e título da página explicativa; papel `heading`.
- **Title:** títulos dos painéis e identificadores das vagas; papel `title`.
- **Body:** texto e controles padrão; papel `body`. Botões recebem peso seminegrito (600).
- **Label:** estados nas linhas; papel `label`. Subtítulo e rótulos de métricas também usam 12px, com peso normal.
- **Small:** tempo, créditos e notas auxiliares; papel `small`.
- **Overlay:** identificação e estado sobre a imagem; papel `overlay`.

Na tela explicativa, o texto corrido usa 14px e entrelinha 1,6; subtítulos usam Sora em 17px. As mensagens centrais do vídeo usam Sora em 21px. Essas exceções servem aos respectivos contextos, sem alterar a escala operacional.

## Layout

A janela tem tamanho inicial até 1440 × 900 e mínimo de 1060 × 700. Não existem breakpoints de navegador nem versão móvel. Ao reduzir a janela, os painéis laterais mantêm a largura e o vídeo absorve a diferença; as duas capturas finais verificam esses extremos.

A navegação ocupa 180px à esquerda. O conteúdo tem margens de 24px nas laterais, 20px no topo e 16px abaixo, com intervalos verticais de 16px. O título antecede uma faixa única de contadores. Abaixo, o vídeo é expansível e a lista de vagas tem largura fixa de 252px, separados por 18px.

Os painéis do vídeo usam margem interna de 12px; a lista usa 15px; a faixa de métricas usa 20px nas laterais e 9px na vertical. As linhas das vagas ficam separadas por 7px. Controles de reprodução usam intervalos de 8px. Essas medidas vêm dos layouts nativos e coexistem com o preenchimento QSS dos controles.

O vídeo mantém a proporção da gravação, com margens azul-escuras quando necessário, sem recorte. A área de desenho tem mínimo de 360 × 220. No modo apresentação, a janela ocupa a tela inteira e oculta navegação e rodapé, preservando vídeo, contagens e controles.

## Elevation & Depth

A interface não usa sombras nem desfoque. Profundidade vem do contraste entre fundo azul-claro, navegação tonal e painéis brancos. Divisórias finas estruturam métricas e histórico. Hover, seleção e foco aparecem por mudança de fundo ou contorno; não há animação de elevação nem transição temporal declarada.

**The Plano Claro Rule.** Separar funções com superfície, espaço e borda; manter os painéis planos.

## Shapes

Painéis têm cantos amplos (`panel`); controles têm cantos menores (`control`) e seletores usam `field`. O vídeo possui recorte arredondado (`video`), enquanto as etiquetas sobrepostas usam `overlay`. A geometria acompanha a função e mantém linhas predominantemente retas.

Controles comuns usam borda de 1px. O foco e a seleção de vagas usam 2px; no vídeo, o foco usa 3px. Marcas de vagas preservam seus polígonos reais: traço colorido de 2px no estado comum, traço branco de 3px na seleção. O preenchimento de estado usa alfa 46 de 255; a seleção aumenta para 88 de 255.

## Components

### Buttons

Botões primários são azuis com texto e ícone brancos. Secundários são brancos com borda clara; a ação discreta usa fundo e borda transparentes. O preenchimento comum está em `button-primary`, `button-secondary` e `button-ghost`. Os ícones são vetores de traço arredondado, desenhados em área de 20px, com espessura 1,8.

O hover do primário escurece o azul; secundários clareiam o fundo; o estado pressionado comum adiciona azul suave. O foco é um contorno de 2px. Primários focados recebem borda azul profunda e o fundo de hover. Desabilitados reduzem contraste com preenchimento e texto próprios. A reprodução reserva largura mínima de 124px; o botão de reinício usa 39px.

### Inputs / Fields

A superfície usa seletores nativos de velocidade e filtro, sem campo de texto livre. Ambos têm fundo claro, borda de 1px, seta vetorial e canto `field`. O foco reforça a borda para 2px. A velocidade ocupa 74px; o filtro acompanha a largura do painel.

O controle temporal usa trilha de 5px, progresso azul e alça de 13px com borda branca de 2px. O foco também contorna a área do controle. Tempo atual e duração aparecem ao lado.

### Navigation

A navegação vertical alinha ícone e texto à esquerda. O item ativo recebe fundo branco e texto azul; o hover aplica fundo claro e o foco permanece visível. O histórico fica abaixo, com linhas que combinam identificador, estado, tempo e quadro. Selecionar um evento leva a gravação àquele instante.

### Cards / Containers

Os três contadores compartilham um painel branco, com divisórias e números destacados. Vídeo e lista usam painéis separados, sem sombra ou contorno externo. O painel de vagas mantém a exportação no fim e o filtro acima das linhas.

### Vagas monitoradas

Cada linha é um botão com identificador à esquerda e estado à direita. A seleção usa `space-selected-border` e `space-selected`; quando também focada, recebe `primary-focus` e `space-focus`. Selecionar a linha destaca a mesma região no vídeo e mostra o percentual de área alterada abaixo da lista.

### Marcações no vídeo

As regiões cadastradas recebem a cor de estado e uma etiqueta escura com identificador e estado. A seleção reforça contorno e preenchimento. As etiquetas têm altura de 21px e largura ajustada ao texto. A imagem permanece dominante; marcações podem ser ocultadas pelo controle “Marcações”.

Estados de preparação e falha ocupam a própria área escura do vídeo, com título claro e explicação secundária. Durante o processamento, contadores mostram um travessão e os controles dependentes ficam desabilitados.

## Do's and Don'ts

### Do:

- Manter texto junto às cores de estado e identificar cada vaga monitorada.
- Preservar a proporção do vídeo e alinhar as marcações às regiões da imagem.
- Usar Sora para títulos e números de destaque; Manrope para controles e leitura.
- Distinguir foco de teclado, seleção da vaga e estado de ocupação.

### Don't:

- Não sugerir câmera ao vivo: a superfície identifica uma gravação de demonstração.
- Não estender marcações ou contagens a vagas sem região cadastrada.
- Não usar a cor clara das marcações como texto de estado sobre fundo branco.
- Não acrescentar sombras ou animações decorativas aos painéis planos existentes.
