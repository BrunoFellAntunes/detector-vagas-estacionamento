"""Extrai um quadro do vídeo na resolução original para usar como referência."""
import argparse
from pathlib import Path
import cv2
from detector import write_image


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video', required=True)
    p.add_argument('--quadro', type=int, default=0, help='Índice do quadro, começando em zero.')
    p.add_argument('--output', default='dados/referencia_real.png')
    p.add_argument('--confirmar-vagas-vazias', action='store_true', required=True,
                   help='Confirmação humana: todas as vagas a cadastrar estão vazias nesse quadro.')
    args = p.parse_args()
    if args.quadro < 0:
        p.error('--quadro deve ser maior ou igual a zero.')
    destination = Path(args.output)
    if destination.suffix.lower() != '.png':
        p.error('Use saída PNG para preservar o quadro sem nova compressão com perdas.')
    if destination.exists():
        p.error('A saída já existe. Escolha outro nome para preservar a referência atual.')
    cap = cv2.VideoCapture(args.video)
    try:
        if not cap.isOpened():
            p.exit(1, 'Erro: vídeo não pôde ser aberto.\n')
        # Leitura sequencial evita busca aproximada por keyframes no codec.
        for _ in range(args.quadro + 1):
            ok, frame = cap.read()
            if not ok:
                p.exit(1, 'Erro: quadro indisponível no vídeo.\n')
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_image(destination, frame)
        print(f'Referência salva: {destination} ({frame.shape[1]}x{frame.shape[0]})')
        print('Confirme visualmente o quadro antes de cadastrar as vagas.')
    finally:
        cap.release()


if __name__ == '__main__':
    main()
