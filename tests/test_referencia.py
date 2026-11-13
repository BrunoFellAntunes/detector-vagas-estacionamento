"""Verifica extração de referência a partir de um vídeo, sem câmera física."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('extrair_referencia'), 'Extração ainda não implementada')

    def test_extracts_requested_frame_at_original_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            video = cv2.VideoWriter(str(folder/'entrada.avi'), cv2.VideoWriter_fourcc(*'MJPG'), 10., (160,120))
            self.assertTrue(video.isOpened())
            for color in [30, 80, 170]:
                video.write(np.full((120,160,3), color, np.uint8))
            video.release()
            command = [sys.executable, str(ROOT/'extrair_referencia.py'), '--video', str(folder/'entrada.avi'),
                       '--quadro', '2', '--output', str(folder/'referencia.png'), '--confirmar-vagas-vazias']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            frame = cv2.imread(str(folder/'referencia.png'))
            self.assertEqual(frame.shape, (120,160,3))
            self.assertAlmostEqual(float(frame.mean()), 170, delta=4)

    def test_requires_manual_confirmation_before_creating_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'referencia.png'
            result = subprocess.run([sys.executable, str(ROOT/'extrair_referencia.py'), '--video', 'nao-existe.mp4',
                                     '--output', str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('--confirmar-vagas-vazias', result.stderr)
            self.assertFalse(output.exists())

    def test_unreadable_video_does_not_create_a_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'referencia.png'
            result = subprocess.run([sys.executable, str(ROOT/'extrair_referencia.py'), '--video', 'nao-existe.mp4',
                                     '--output', str(output), '--confirmar-vagas-vazias'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
