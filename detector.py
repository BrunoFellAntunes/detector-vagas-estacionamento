"""Protótipo acadêmico: ocupação por referência vazia ou textura da região.

Não detecta semanticamente automóveis. Sombras e objetos também alteram a vaga.
"""
import argparse
import csv
import json
from pathlib import Path
import time

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
        self.method = config.get('method', 'reference')
        self.texture_block_size = config.get('texture_block_size', 25)
        self.texture_constant = float(config.get('texture_constant', 16))
        self.analysis_inset = config.get('analysis_inset', 0)
        if self.method not in ('reference', 'texture'):
            raise ValueError('Método deve ser reference ou texture.')
        if (not isinstance(self.texture_block_size,int) or self.texture_block_size<3 or
                self.texture_block_size%2==0 or not np.isfinite(self.texture_constant) or
                not isinstance(self.analysis_inset,int) or not 0<=self.analysis_inset<=20):
            raise ValueError('Parâmetros de textura ou margem de análise inválidos.')
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
            local_free=float(space.get('free_ratio',self.free_ratio))
            local_occupied=float(space.get('occupied_ratio',self.occupied_ratio))
            if not 0<=local_free<local_occupied<=1:
                raise ValueError('Limiares da vaga exigem 0 <= livre < ocupada <= 1.')
            x,y,rw,rh=cv2.boundingRect(points)
            mask = np.zeros((rh,rw), np.uint8)
            cv2.fillPoly(mask, [points-[x,y]], 255)
            if self.analysis_inset:
                size=2*self.analysis_inset+1
                mask=cv2.erode(mask,np.ones((size,size),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0)
            if not mask.any():raise ValueError('Margem de análise removeu toda a vaga.')
            self.spaces.append({'id': name, 'points': points, 'mask': mask > 0,'bounds':(x,y,rw,rh),
                                'free_ratio':local_free,'occupied_ratio':local_occupied,
                                'state': 'indefinida', 'candidate': None, 'count': 0})
            ids.add(name)
        self.reference = self._gray(reference)

    @staticmethod
    def _gray(frame):
        return cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0)

    def process(self, frame, instant=False):
        if frame.shape != self.shape:
            raise ValueError('Imagem alterou a resolução. Refaça a calibração.')
        if self.method=='texture':
            gray=cv2.GaussianBlur(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY),(3,3),0)
            binary=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,self.texture_block_size,self.texture_constant)
            binary=cv2.medianBlur(binary,5)
            changed=(cv2.dilate(binary,np.ones((3,3),np.uint8))>0).astype(np.uint8)
        else:
            diff = cv2.absdiff(self.reference, self._gray(frame))
            changed = (diff > self.pixel_threshold).astype(np.uint8)
            changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        results = []
        for space in self.spaces:
            x,y,w,h=space['bounds']
            ratio = float(changed[y:y+h,x:x+w][space['mask']].mean())
            target = ('ocupada' if ratio >= space['occupied_ratio'] else
                      'livre' if ratio <= space['free_ratio'] else None)
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
            label = space['id'] if len(self.spaces)>12 else f"{space['id']} {result['state']} {result['ratio']:.0%}"
            text_y = int(y)+16 if len(self.spaces)>12 else max(60, int(y) - 8)
            (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, .48, 1)
            text_x = max(0, min(int(x), out.shape[1] - label_w - 5))
            cv2.rectangle(out, (text_x, text_y-label_h-5),
                          (text_x+label_w+5, text_y+baseline), (25,25,25), -1)
            cv2.putText(out, label, (text_x+2, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, .48, colors[result['state']], 1, cv2.LINE_AA)
        counts = {state: sum(r['state'] == state for r in results) for state in colors}
        cv2.rectangle(out, (0, 0), (out.shape[1], 40), (25, 25, 25), -1)
        text = f'Monitoradas: {len(results)} | ' + ' | '.join(f'{k}: {v}' for k, v in counts.items())
        cv2.putText(out, text, (12, 27), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 1, cv2.LINE_AA)
        return out


def run(args):
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    detector = Detector(read_image(args.reference), config)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    # Esses relatórios deixam de ser válidos quando uma nova execução começa.
    for name in ['resumo.json','avaliacao.json']:
        (output/name).unlink(missing_ok=True)
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
        event_count = 0
        previous_states = {space['id']: 'indefinida' for space in detector.spaces}
        interrupted = False
        started = time.perf_counter()
        window = 'Monitoramento de vagas - Espaco: pausa | Q: sair'
        if args.show:
            cv2.namedWindow(window, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window,min(first.shape[1],1280),min(first.shape[0],720))
        frame = first
        with ((output / 'ocupacao.csv').open('w', encoding='utf-8', newline='') as stream,
              (output / 'eventos.csv').open('w', encoding='utf-8', newline='') as event_stream):
            log = csv.writer(stream)
            measure='densidade_textura' if detector.method=='texture' else 'fracao_alterada'
            log.writerow(['quadro', 'tempo_video_s', 'vaga', 'estado', measure])
            events = csv.writer(event_stream)
            events.writerow(['quadro', 'tempo_video_s', 'vaga', 'estado_anterior', 'estado_atual'])
            while frame is not None:
                frame_started = time.perf_counter()
                results = detector.process(frame, instant=image_mode)
                annotated = detector.annotate(frame, results)
                if not image_mode:
                    cv2.rectangle(annotated, (0, annotated.shape[0]-25),
                                  (annotated.shape[1], annotated.shape[0]), (25,25,25), -1)
                    cv2.putText(annotated, f'Quadro {frame_number} | tempo da fonte: {frame_number/fps:.2f}s',
                                (10, annotated.shape[0]-8), cv2.FONT_HERSHEY_SIMPLEX, .45, (255,255,255), 1)
                for result in results:
                    log.writerow([frame_number, round(frame_number / fps, 3), result['id'],
                                  result['state'], round(result['ratio'], 5)])
                    before = previous_states[result['id']]
                    if before != result['state']:
                        events.writerow([frame_number, round(frame_number/fps, 3), result['id'],
                                         before, result['state']])
                        previous_states[result['id']] = result['state']
                        event_count += 1
                if image_mode:
                    write_image(output / 'imagem_anotada.png', annotated)
                else:
                    writer.write(annotated)
                frame_number += 1
                if args.show:
                    cv2.imshow(window, annotated)
                    delay = max(1, round(1000/fps - 1000*(time.perf_counter()-frame_started)))
                    key = cv2.waitKey(0 if image_mode else delay) & 0xff
                    if key == ord(' ') and not image_mode:
                        paused=annotated.copy()
                        cv2.rectangle(paused,(0,paused.shape[0]-25),(paused.shape[1],paused.shape[0]),(25,25,25),-1)
                        cv2.putText(paused,'PAUSADO | Espaco: continuar | Q/Esc: encerrar',
                                    (10,paused.shape[0]-8),cv2.FONT_HERSHEY_SIMPLEX,.45,(0,220,255),1)
                        cv2.imshow(window,paused)
                        while True:
                            key = cv2.waitKey(50) & 0xff
                            if key in (ord(' '), ord('q'), ord('Q'), 27) or cv2.getWindowProperty(window,cv2.WND_PROP_VISIBLE)<1:
                                break
                    if key in (ord('q'), ord('Q'), 27) or cv2.getWindowProperty(window,cv2.WND_PROP_VISIBLE)<1:
                        interrupted = True
                        break
                if image_mode:
                    break
                ok, frame = capture.read()
                if not ok:
                    break
        write_image(output / 'ultimo_quadro.png', annotated)
        elapsed = time.perf_counter() - started
        summary = {
            'metodo': detector.method,
            'tipo_fonte': 'imagem' if image_mode else 'camera' if args.source.isdigit() else 'video',
            'quadros_processados': frame_number,
            'vagas_monitoradas': len(detector.spaces),
            'fps_informado_fonte': None if image_mode else fps,
            'duracao_fonte_processada_s': None if image_mode else round(frame_number/fps,6),
            'contagem_final': {state: sum(r['state']==state for r in results)
                               for state in ['livre','ocupada','indefinida']},
            'eventos_confirmados': event_count,
            'tempo_execucao_s': round(elapsed,6),
            'quadros_por_segundo_execucao': round(frame_number/max(elapsed,1e-9),3),
            'exibicao_interativa': args.show,
            'interrompido_pelo_usuario': interrupted,
            'nota_tempo': 'Tempo inclui processamento, exportacao e eventual exibicao/pausa. '
                          'O tempo da fonte em camera depende do FPS informado pelo dispositivo.'
        }
        (output/'resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
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
