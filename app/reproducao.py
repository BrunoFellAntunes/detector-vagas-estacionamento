"""Reprodução local do vídeo, sincronizada aos quadros analisados."""
import cv2
from PySide6.QtCore import QObject,QTimer,Qt,Signal


class PlaybackController(QObject):
    frame_changed=Signal(int,object)
    playing_changed=Signal(bool)
    failed=Signal(str)

    def __init__(self,session,parent=None):
        super().__init__(parent)
        self.session=session
        self.capture=cv2.VideoCapture(str(session.source))
        if not self.capture.isOpened():
            raise ValueError('Não foi possível abrir a gravação. Confira o arquivo de vídeo deste estacionamento.')
        self.index=-1
        self._next_capture_index=0
        self.playing=False
        self.speed=1.
        self.timer=QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._advance)

    def seek(self,index):
        index=max(0,min(int(index),self.session.frame_count-1))
        if index!=self._next_capture_index:
            if not self.capture.set(cv2.CAP_PROP_POS_FRAMES,index):
                self._next_capture_index=None
                self.pause()
                self.failed.emit('A gravação não permite buscar esse instante.')
                return False
        ok,frame=self.capture.read()
        if not ok:
            self._next_capture_index=None
            self.pause()
            self.failed.emit('Não foi possível ler o quadro solicitado. Reprocesse ou confira o vídeo.')
            return False
        self._next_capture_index=index+1
        self.index=index
        self.frame_changed.emit(index,frame)
        return True

    def play(self):
        if self.index>=self.session.frame_count-1 and not self.seek(0):return
        self.playing=True
        self.timer.start(max(1,round(1000/(self.session.fps*self.speed))))
        self.playing_changed.emit(True)

    def pause(self):
        self.timer.stop()
        self.playing=False
        self.playing_changed.emit(False)

    def toggle(self):
        self.pause() if self.playing else self.play()

    def restart(self):
        self.pause()
        self.seek(0)

    def set_speed(self,value):
        if value not in (.5,1.,1.5,2.):raise ValueError('Velocidade não suportada.')
        self.speed=value
        if self.playing:self.timer.start(max(1,round(1000/(self.session.fps*self.speed))))

    def _advance(self):
        if self.index>=self.session.frame_count-1:
            self.pause()
            return
        self.seek(self.index+1)
        if self.index==self.session.frame_count-1:self.pause()

    def close(self):
        self.pause()
        self.capture.release()
