import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import shutil

import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


class RealExampleTests(unittest.TestCase):
    def test_single_command_runs_from_another_directory_and_evaluates_real_clip(self):
        self.assertIsNotNone(importlib.util.find_spec('executar_exemplo'),'Exemplo em um comando ainda não implementado')
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'saida com espaços'
            run=subprocess.run([sys.executable,str(ROOT/'executar_exemplo.py'),'--output',str(out)],
                               cwd=tmp,capture_output=True,text=True,timeout=90)
            self.assertEqual(run.returncode,0,run.stderr)
            summary=json.loads((out/'resumo.json').read_text(encoding='utf-8'))
            self.assertEqual(summary['quadros_processados'],679)
            self.assertEqual(summary['vagas_monitoradas'],5)
            self.assertEqual(summary['contagem_final'],{'livre':5,'ocupada':0,'indefinida':0})
            self.assertEqual(summary['eventos_confirmados'],8)
            evaluation=json.loads((out/'avaliacao.json').read_text(encoding='utf-8'))
            self.assertEqual(evaluation['amostras'],60)
            self.assertEqual(evaluation['indefinidas'],5)
            self.assertEqual(evaluation['matriz_confusao'],{'VP':10,'VN':44,'FP':1,'FN':0})

    def test_incomplete_clip_cannot_be_reported_as_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for filename in ['executar_exemplo.py','detector.py','avaliar.py']:
                shutil.copy2(ROOT/filename,folder/filename)
            data=folder/'dados/terceiros'
            data.mkdir(parents=True)
            reference=np.full((120,200,3),60,np.uint8)
            cv2.imwrite(str(data/'referencia_carpark.png'),reference)
            config={'width':200,'height':120,'spaces':[
                {'id':'V01','points':[[20,20],[90,20],[90,100],[20,100]]}]}
            (data/'vagas_carpark.json').write_text(json.dumps(config),encoding='utf-8')
            (data/'carPark.metadata.json').write_text('{"quadros_decodificados": 10}',encoding='utf-8')
            (data/'rotulos_carpark.csv').write_text('quadro,vaga,estado\n0,V01,livre\n',encoding='utf-8')
            video=cv2.VideoWriter(str(data/'carPark.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),10.,(200,120))
            self.assertTrue(video.isOpened())
            for _ in range(9):video.write(reference)
            video.release()
            out=folder/'out'
            out.mkdir()
            (out/'avaliacao.json').write_text('{"amostras": 60}',encoding='utf-8')
            run=subprocess.run([sys.executable,str(folder/'executar_exemplo.py'),'--output',str(out)],
                               capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0,'Vídeo menor que a versão esperada foi aceito como completo')
            self.assertFalse((out/'avaliacao.json').exists(),'Resultado antigo permaneceu após a falha')
