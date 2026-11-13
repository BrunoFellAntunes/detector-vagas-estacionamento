"""Gera cena e vídeo SIMULADOS para verificar o fluxo, sem dados reais."""
import json
from pathlib import Path
import cv2
import numpy as np
from detector import write_image


def main():
    base = Path(__file__).resolve().parent / 'dados'
    base.mkdir(exist_ok=True)
    ref = np.full((600, 1000, 3), 68, np.uint8)
    cv2.putText(ref, 'DEMONSTRACAO SIMULADA - SEM DADOS DE CAMPO', (35, 580),
                cv2.FONT_HERSHEY_SIMPLEX, .63, (220, 220, 220), 1, cv2.LINE_AA)
    spaces = []
    for index in range(6):
        x, y = 55 + (index % 3) * 315, 100 + (index // 3) * 230
        pts = [[x, y], [x+250, y], [x+250, y+170], [x, y+170]]
        cv2.polylines(ref, [np.array(pts, np.int32)], True, (225, 225, 225), 3)
        spaces.append({'id': f'V{index+1:02}', 'points': [[x+8,y+8],[x+242,y+8],[x+242,y+162],[x+8,y+162]]})
    write_image(base / 'referencia_vazia.png', ref)
    config = {'width': 1000, 'height': 600, 'pixel_threshold': 25, 'occupied_ratio': .2,
              'free_ratio': .1, 'stable_frames': 5, 'spaces': spaces}
    (base / 'vagas_demo.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    video = cv2.VideoWriter(str(base / 'video_simulado.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 20., (1000, 600))
    if not video.isOpened():
        raise RuntimeError('Codec MP4 indisponível.')
    truth = []
    try:
        for number in range(240):
            occupied = [0, 2] if number < 80 else [0, 2, 4] if number < 160 else [2, 4]
            frame = ref.copy()
            for index in occupied:
                x, y = spaces[index]['points'][0]
                cv2.rectangle(frame, (x+40, y+14), (x+190, y+142), (180, 110, 35), -1)
                cv2.rectangle(frame, (x+65, y+32), (x+165, y+58), (210, 205, 190), -1)
                cv2.rectangle(frame, (x+65, y+101), (x+165, y+124), (210, 205, 190), -1)
            video.write(frame)
            truth.append({'quadro': number, 'ocupadas': [f'V{i+1:02}' for i in occupied]})
            if number == 120:
                write_image(base / 'cena_simulada.png', frame)
    finally:
        video.release()
    (base / 'gabarito_simulado.json').write_text(json.dumps(truth, indent=2), encoding='utf-8')
    print('Demonstração simulada gerada em', base)


if __name__ == '__main__':
    main()
