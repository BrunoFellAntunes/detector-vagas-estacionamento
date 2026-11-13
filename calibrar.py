"""Selecione quatro cantos por vaga em ordem ao redor do seu contorno."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from detector import read_image


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', required=True)
    p.add_argument('--output', default='dados/vagas.json')
    a = p.parse_args()
    frame = read_image(a.reference)
    height, width = frame.shape[:2]
    points, spaces = [], []
    title = '4 cantos | N confirma | U desfaz | S salva | ESC cancela'

    def click(event, x, y, flags, userdata):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
            points.append([x, y])

    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(title, click)
    try:
        while True:
            view = frame.copy()
            for space in spaces:
                polygon = np.asarray(space['points'], np.int32)
                cv2.polylines(view, [polygon], True, (0, 220, 0), 2)
                cv2.putText(view, space['id'], tuple(polygon[0]), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 220, 0), 2)
            for point in points:
                cv2.circle(view, tuple(point), 5, (0, 200, 255), -1)
            cv2.imshow(title, view)
            key = cv2.waitKey(30) & 0xff
            if key == 27 or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                return
            if key == ord('u'):
                if points:
                    points.pop()
                elif spaces:
                    spaces.pop()
            if key == ord('n') and len(points) == 4:
                polygon = np.asarray(points, np.int32)
                if cv2.isContourConvex(polygon) and cv2.contourArea(polygon) >= 4:
                    spaces.append({'id': f'V{len(spaces)+1:02}', 'points': points.copy()})
                    points.clear()
                else:
                    print('Polígono inválido. Use U e selecione os cantos em ordem.')
            if key == ord('s') and spaces and not points:
                config = {'width': width, 'height': height, 'pixel_threshold': 25,
                          'occupied_ratio': .2, 'free_ratio': .1, 'stable_frames': 5, 'spaces': spaces}
                destination = Path(a.output)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(config, indent=2), encoding='utf-8')
                print(f'{len(spaces)} vagas salvas: {destination.resolve()}')
                return
    finally:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
