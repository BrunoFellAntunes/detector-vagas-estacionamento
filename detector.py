"""Protótipo acadêmico: ocupação por diferença contra referência vazia fixa.

Não detecta semanticamente automóveis. Sombras e objetos também alteram a vaga.
"""
import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np


def read_image(path):
    """Leitura compatível com caminhos que contêm acentos no Windows."""
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f'Imagem ilegível: {path}')
    return image


def write_image(path, image):
    ok, encoded = cv2.imencode(Path(path).suffix, image)
    if not ok:
        raise ValueError(f'Não foi possível codificar: {path}')
    encoded.tofile(str(path))


class Detector:
    def __init__(self, reference, config):
        self.shape = reference.shape
        h, w = self.shape[:2]
        if (config['width'], config['height']) != (w, h):
            raise ValueError('Resolução da configuração difere da referência.')
        self.pixel_threshold = float(config.get('pixel_threshold', 25))
        self.occupied_ratio = float(config.get('occupied_ratio', .2))
        self.free_ratio = float(config.get('free_ratio', .1))
        self.stable_frames = config.get('stable_frames', 5)
        if not 0 <= self.free_ratio < self.occupied_ratio <= 1:
            raise ValueError('Exige 0 <= free_ratio < occupied_ratio <= 1.')
        if not 0 < self.pixel_threshold < 255:
            raise ValueError('pixel_threshold deve estar entre 0 e 255.')
        if not isinstance(self.stable_frames, int) or self.stable_frames < 1:
            raise ValueError('stable_frames deve ser inteiro positivo.')
        spaces = config['spaces']
        if not spaces:
            raise ValueError('Cadastre pelo menos uma vaga.')
        self.spaces = []
        ids = set()
        for space in spaces:
            name = str(space['id'])
            points_raw = np.asarray(space['points'], dtype=float)
            if (not name or name in ids or points_raw.ndim != 2 or
                    points_raw.shape[0] < 3 or points_raw.shape[1] != 2 or
                    not np.isfinite(points_raw).all() or
                    not np.equal(points_raw, np.floor(points_raw)).all()):
                raise ValueError('Identificador duplicado ou polígono inválido.')
            points = points_raw.astype(np.int32)
            if (np.any(points < 0) or np.any(points[:, 0] >= w) or
                    np.any(points[:, 1] >= h) or not cv2.isContourConvex(points) or
                    cv2.contourArea(points) < 4):
                raise ValueError('Use um polígono convexo dentro da imagem.')
            mask = np.zeros((h, w), np.uint8)
            cv2.fillPoly(mask, [points], 255)
            self.spaces.append({'id': name, 'points': points, 'mask': mask > 0,
                                'state': 'indefinida', 'candidate': None, 'count': 0})
            ids.add(name)
        self.reference = self._gray(reference)

    @staticmethod
    def _gray(frame):
        return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0)

    def process(self, frame, instant=False):
        if frame.shape != self.shape:
            raise ValueError('Imagem alterou a resolução. Refaça a calibração.')
        diff = cv2.absdiff(self.reference, self._gray(frame))
        changed = (diff > self.pixel_threshold).astype(np.uint8)
        changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        results = []
        for space in self.spaces:
            ratio = float(changed[space['mask']].mean())
            target = ('ocupada' if ratio >= self.occupied_ratio else
                      'livre' if ratio <= self.free_ratio else None)
            if instant:
                space['state'] = target or 'indefinida'
            elif target is None or target == space['state']:
                space['candidate'], space['count'] = None, 0
            else:
                space['count'] = space['count'] + 1 if space['candidate'] == target else 1
                space['candidate'] = target
                if space['count'] >= self.stable_frames:
                    space['state'] = target
                    space['candidate'], space['count'] = None, 0
            results.append({'id': space['id'], 'state': space['state'], 'ratio': ratio})
        return results

    def annotate(self, frame, results):
        out = frame.copy()
        colors = {'livre': (45, 200, 60), 'ocupada': (50, 65, 230), 'indefinida': (0, 200, 255)}
        for space, result in zip(self.spaces, results):
            pts = space['points']
            cv2.polylines(out, [pts], True, colors[result['state']], 3)
            x, y = pts.min(axis=0)
            label = f"{space['id']} {result['state']} {result['ratio']:.0%}"
            cv2.putText(out, label, (int(x), max(60, int(y) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, .48, colors[result['state']], 1, cv2.LINE_AA)
        counts = {state: sum(r['state'] == state for r in results) for state in colors}
        cv2.rectangle(out, (0, 0), (out.shape[1], 40), (25, 25, 25), -1)
        text = ' | '.join(f'{k}: {v}' for k, v in counts.items())
        cv2.putText(out, text, (12, 27), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 1, cv2.LINE_AA)
        return out


def run(args):
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    detector = Detector(read_image(args.reference), config)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    image_mode = Path(args.source).suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
    capture = writer = None
    try:
        if image_mode:
            first = read_image(args.source)
            fps = 1.
        else:
            source = int(args.source) if args.source.isdigit() else args.source
            capture = cv2.VideoCapture(source)
            if not capture.isOpened():
                raise ValueError('Não foi possível abrir o vídeo ou a câmera.')
            ok, first = capture.read()
            if not ok:
                raise ValueError('Fonte sem quadros legíveis.')
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            fps = fps if np.isfinite(fps) and fps > 0 else 25.
            writer = cv2.VideoWriter(str(output / 'video_anotado.mp4'), cv2.VideoWriter_fourcc(*'mp4v'),
                                     fps, (first.shape[1], first.shape[0]))
            if not writer.isOpened():
                raise ValueError('Não foi possível criar o vídeo de saída.')
        frame_number = 0
        frame = first
        with (output / 'ocupacao.csv').open('w', encoding='utf-8', newline='') as stream:
            log = csv.writer(stream)
            log.writerow(['quadro', 'tempo_video_s', 'vaga', 'estado', 'fracao_alterada'])
            while frame is not None:
                results = detector.process(frame, instant=image_mode)
                annotated = detector.annotate(frame, results)
                for result in results:
                    log.writerow([frame_number, round(frame_number / fps, 3), result['id'],
                                  result['state'], round(result['ratio'], 5)])
                if image_mode:
                    write_image(output / 'imagem_anotada.png', annotated)
                else:
                    writer.write(annotated)
                write_image(output / 'ultimo_quadro.png', annotated)
                frame_number += 1
                if args.show:
                    cv2.imshow('Vagas - Q para sair', annotated)
                    if cv2.waitKey(0 if image_mode else 1) & 0xff == ord('q'):
                        break
                if image_mode:
                    break
                ok, frame = capture.read()
                if not ok:
                    break
        print(f'{frame_number} quadro(s) processado(s). Saída: {output.resolve()}')
        return frame_number
    finally:
        if capture is not None:
            capture.release()
        if writer is not None:
            writer.release()
        if args.show:
            cv2.destroyAllWindows()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True, help='Imagem, vídeo ou índice da câmera (0).')
    p.add_argument('--reference', required=True, help='Imagem com TODAS as vagas cadastradas vazias.')
    p.add_argument('--config', required=True, help='JSON com polígonos e parâmetros.')
    p.add_argument('--output', default='resultados')
    p.add_argument('--show', action='store_true', help='Exibir janela local OpenCV.')
    args = p.parse_args()
    try:
        run(args)
    except (ValueError, OSError, KeyError, TypeError, cv2.error) as error:
        p.exit(1, f'Erro: {error}\n')


if __name__ == '__main__':
    main()
