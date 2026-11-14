import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
HAS_QT=importlib.util.find_spec('PySide6') is not None
if HAS_QT:
    from PySide6.QtWidgets import QApplication


class OneReadFailure:
    """Falha de leitura no limite do decoder, preservando o OpenCV real."""
    def __init__(self,capture):
        self.capture=capture
        self.fail_next=False

    def set(self,*args):return self.capture.set(*args)
    def release(self):return self.capture.release()

    def read(self):
        result=self.capture.read()
        if self.fail_next:
            self.fail_next=False
            return False,None
        return result


@unittest.skipUnless(HAS_QT,'Instale requirements-app.txt para verificar a reprodução Qt.')
class PlaybackFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])

    def setUp(self):
        from app.reproducao import PlaybackController
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        source=Path(self.tmp.name)/'quadros.avi'
        writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'MJPG'),10.,(160,120))
        self.assertTrue(writer.isOpened())
        for value in [30,50,70,90,110,130,150,170,190]:
            writer.write(np.full((120,160,3),value,np.uint8))
        writer.release()
        self.controller=PlaybackController(SimpleNamespace(source=source,frame_count=9,fps=10.))
        self.addCleanup(self.controller.close)
        self.capture=OneReadFailure(self.controller.capture)
        self.controller.capture=self.capture
        self.seen=[]
        self.controller.frame_changed.connect(lambda index,frame:self.seen.append((index,float(frame.mean()))))

    def test_resume_after_failed_seek_repositions_decoder(self):
        self.controller.seek(0)
        self.capture.fail_next=True
        self.controller.seek(5)
        self.controller.seek(1)
        self.assertEqual(self.seen[-1][0],1)
        self.assertAlmostEqual(self.seen[-1][1],50,delta=4,
                               msg='Imagem física não corresponde ao índice do quadro')

    def test_failed_rewind_does_not_restart_playback_timer(self):
        self.controller.seek(8)
        self.capture.fail_next=True
        self.controller.play()
        self.assertFalse(self.controller.playing)
        self.assertFalse(self.controller.timer.isActive())
