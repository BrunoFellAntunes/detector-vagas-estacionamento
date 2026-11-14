"""Contratos de exportação de uma execução real, sem mocks de OpenCV."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


class ExecutionTests(unittest.TestCase):
    def test_video_exports_only_confirmed_state_changes_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            reference=np.full((120,200,3),60,np.uint8)
            cv2.imwrite(str(folder/'ref.png'),reference)
            config={'width':200,'height':120,'stable_frames':2,'spaces':[
                {'id':'V01','points':[[20,20],[90,20],[90,100],[20,100]]}]}
            (folder/'config.json').write_text(json.dumps(config),encoding='utf-8')
            video=cv2.VideoWriter(str(folder/'video.avi'),cv2.VideoWriter_fourcc(*'MJPG'),10.,(200,120))
            self.assertTrue(video.isOpened())
            for occupied in [False]*3+[True]*3+[False]*3:
                frame=reference.copy()
                if occupied:frame[30:90,30:80]=220
                video.write(frame)
            video.release()
            run=subprocess.run([sys.executable,str(ROOT/'detector.py'),'--source',str(folder/'video.avi'),
                                '--reference',str(folder/'ref.png'),'--config',str(folder/'config.json'),
                                '--output',str(folder/'out')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertTrue((folder/'out/eventos.csv').exists(),'Não exportou mudanças de estado')
            with (folder/'out/eventos.csv').open(encoding='utf-8',newline='') as f:
                events=list(csv.DictReader(f))
            self.assertEqual([(int(e['quadro']),e['estado_anterior'],e['estado_atual']) for e in events],
                             [(1,'indefinida','livre'),(4,'livre','ocupada'),(7,'ocupada','livre')])
            summary=json.loads((folder/'out/resumo.json').read_text(encoding='utf-8'))
            self.assertEqual(summary['quadros_processados'],9)
            self.assertEqual(summary['contagem_final'],{'livre':1,'ocupada':0,'indefinida':0})
            self.assertEqual(summary['eventos_confirmados'],3)
            self.assertAlmostEqual(summary['duracao_fonte_processada_s'],.9)
            self.assertGreater(summary['tempo_execucao_s'],0)
            self.assertGreater(summary['quadros_por_segundo_execucao'],0)
            self.assertFalse(summary['exibicao_interativa'])
            cap=cv2.VideoCapture(str(folder/'out/video_anotado.mp4'))
            decoded=0
            while cap.read()[0]:decoded+=1
            cap.release()
            self.assertEqual(decoded,9)

    def test_image_writes_summary_and_instant_initialization_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            cv2.imwrite(str(folder/'ref.png'),np.full((120,200,3),60,np.uint8))
            config={'width':200,'height':120,'spaces':[
                {'id':'V01','points':[[20,20],[90,20],[90,100],[20,100]]}]}
            (folder/'config.json').write_text(json.dumps(config),encoding='utf-8')
            run=subprocess.run([sys.executable,str(ROOT/'detector.py'),'--source',str(folder/'ref.png'),
                                '--reference',str(folder/'ref.png'),'--config',str(folder/'config.json'),
                                '--output',str(folder/'out')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertTrue((folder/'out/resumo.json').exists(),'Imagem não exportou resumo')
            data=json.loads((folder/'out/resumo.json').read_text(encoding='utf-8'))
            self.assertEqual(data['tipo_fonte'],'imagem')
            self.assertIsNone(data['duracao_fonte_processada_s'])
            self.assertEqual(data['eventos_confirmados'],1)
            # Uma falha após reabrir os CSVs não pode preservar relatórios da execução anterior.
            (folder/'out/avaliacao.json').write_text('{"amostras": 60}',encoding='utf-8')
            cv2.imwrite(str(folder/'bad.png'),np.full((80,200,3),60,np.uint8))
            failed=subprocess.run([sys.executable,str(ROOT/'detector.py'),'--source',str(folder/'bad.png'),
                                   '--reference',str(folder/'ref.png'),'--config',str(folder/'config.json'),
                                   '--output',str(folder/'out')],capture_output=True,text=True)
            self.assertNotEqual(failed.returncode,0)
            self.assertFalse((folder/'out/resumo.json').exists(),'Resumo antigo aparenta descrever a tentativa atual')
            self.assertFalse((folder/'out/avaliacao.json').exists(),'Avaliação antiga sobreviveu à nova tentativa')
