"""Testes de comportamento com imagens controladas, sem representar campo real."""
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('detector'), 'Detector ainda não implementado')
        from detector import Detector
        self.Detector = Detector
        self.ref = np.full((100, 200, 3), 80, np.uint8)
        self.config = {'width': 200, 'height': 100, 'pixel_threshold': 25,
                       'occupied_ratio': .2, 'free_ratio': .1, 'stable_frames': 2,
                       'spaces': [{'id': 'V01', 'points': [[10, 10], [90, 10], [90, 90], [10, 90]]}]}

    def test_unchanged_space_is_free(self):
        d = self.Detector(self.ref, self.config)
        self.assertEqual(d.process(self.ref)[0]['state'], 'indefinida')
        self.assertEqual(d.process(self.ref)[0]['state'], 'livre')

    def test_parked_object_stays_occupied_without_motion(self):
        d = self.Detector(self.ref, self.config)
        frame = self.ref.copy()
        frame[20:80, 20:80] = 220
        for _ in range(10):
            result = d.process(frame)
        self.assertEqual(result[0]['state'], 'ocupada')

    def test_change_outside_space_does_not_count(self):
        d = self.Detector(self.ref, self.config)
        frame = self.ref.copy()
        frame[:, 110:] = 255
        d.process(frame)
        self.assertEqual(d.process(frame)[0]['state'], 'livre')

    def test_one_frame_disturbance_does_not_change_state(self):
        d = self.Detector(self.ref, self.config)
        d.process(self.ref)
        d.process(self.ref)
        frame = self.ref.copy()
        frame[20:80, 20:80] = 220
        self.assertEqual(d.process(frame)[0]['state'], 'livre')
        self.assertEqual(d.process(self.ref)[0]['state'], 'livre')

    def test_departure_returns_to_free(self):
        d = self.Detector(self.ref, self.config)
        frame = self.ref.copy()
        frame[20:80, 20:80] = 220
        d.process(frame)
        d.process(frame)
        d.process(self.ref)
        self.assertEqual(d.process(self.ref)[0]['state'], 'livre')

    def test_resolution_change_is_rejected(self):
        d = self.Detector(self.ref, self.config)
        with self.assertRaises(ValueError):
            d.process(np.zeros((80, 200, 3), np.uint8))

    def test_invalid_configurations_are_rejected(self):
        for patch in [{'free_ratio': .8}, {'stable_frames': 0}, {'spaces': []},
                      {'spaces': [{'id': 'V01', 'points': [[-1, 0], [40, 0], [40, 40]]}]},
                      {'spaces': self.config['spaces'] * 2}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.Detector(self.ref, {**self.config, **patch})

    def test_cli_image_exports_annotation_and_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cv2.imwrite(str(p / 'ref.png'), self.ref)
            (p / 'vagas.json').write_text(json.dumps(self.config), encoding='utf-8')
            r = subprocess.run([sys.executable, str(ROOT / 'detector.py'), '--source', str(p / 'ref.png'),
                                '--reference', str(p / 'ref.png'), '--config', str(p / 'vagas.json'),
                                '--output', str(p / 'saida')], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIsNotNone(cv2.imread(str(p / 'saida' / 'imagem_anotada.png')))
            with (p / 'saida' / 'ocupacao.csv').open(encoding='utf-8', newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['estado'], 'livre')


if __name__ == '__main__':
    unittest.main()
