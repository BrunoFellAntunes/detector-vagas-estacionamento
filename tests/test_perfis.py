"""Perfis locais: vídeo real, mapa independente e resultados reproduzíveis."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def make_video(path):
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),12,(320,180))
    if not writer.isOpened():raise RuntimeError('Codec de teste indisponível')
    for _ in range(12):writer.write(np.full((180,320,3),100,np.uint8))
    writer.release()


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('app.perfis'),'Cadastro de vídeos e mapas ainda não implementado')
        from app.perfis import ProfileStore,probe_video
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.video=self.root/'pátio.avi';make_video(self.video)
        self.store=ProfileStore(self.root/'perfis');self.probe=probe_video(self.video)
        self.config={'width':320,'height':180,'method':'texture','stable_frames':2,
                     'free_ratio':.11,'occupied_ratio':.12,'analysis_inset':0,
                     'spaces':[{'id':'V01','points':[[20,20],[110,20],[110,100],[20,100]]}]}

    def save(self,**kwargs):
        return self.store.save('Pátio da universidade',self.probe,self.config,**kwargs)

    def test_imported_video_map_and_reference_survive_reopening(self):
        profile=self.save()
        reopened=self.store.list()[0]
        self.assertEqual(reopened.id,profile.id)
        self.assertEqual(reopened.name,'Pátio da universidade')
        self.assertEqual(reopened.source,self.video.resolve())
        self.assertEqual(reopened.frame_count,12)
        self.assertEqual(json.loads(reopened.config.read_text())['spaces'][0]['points'][2],[110,100])
        self.assertEqual(cv2.imread(str(reopened.reference)).shape[:2],(180,320))
        self.assertEqual(len(self.store.list()),1)

    def test_moving_a_space_creates_a_new_analysis_revision(self):
        first=self.save()
        first.output.mkdir();(first.output/'resumo.json').write_text('{"antigo":true}')
        self.config['spaces'][0]['points']=[[150,20],[230,20],[230,100],[150,100]]
        second=self.save(existing=first)
        self.assertEqual(second.id,first.id)
        self.assertNotEqual(second.output,first.output)
        self.assertEqual(len(self.store.list()),1)
        self.assertFalse((second.output/'resumo.json').exists())
        self.assertTrue((first.output/'resumo.json').exists(),'Revisão anterior deve permanecer recuperável')

    def test_invalid_map_and_name_do_not_replace_a_saved_profile(self):
        saved=self.save()
        self.config['spaces'][0]['points'][0]=[-1,20]
        with self.assertRaises(ValueError):self.save(existing=saved)
        self.assertEqual(self.store.list()[0].config,saved.config)
        with self.assertRaises(ValueError):self.store.save(' ',self.probe,self.config)

    def test_missing_or_replaced_video_is_reported_before_analysis(self):
        saved=self.save()
        self.video.unlink()
        with self.assertRaisesRegex(ValueError,'vídeo'):saved.validate_source()
        self.video.write_bytes(b'arquivo diferente')
        with self.assertRaisesRegex(ValueError,'vídeo'):saved.validate_source()

    def test_custom_analysis_uses_its_own_video_without_demo_labels(self):
        from app.modelo import load_session
        profile=self.save()
        result=subprocess.run([sys.executable,str(ROOT/'detector.py'),'--source',str(profile.source),
            '--reference',str(profile.reference),'--config',str(profile.config),'--output',str(profile.output)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        session=load_session(ROOT,profile=profile)
        self.assertEqual(session.frame_count,12)
        self.assertEqual(session.counts(11),{'livre':1,'ocupada':0,'indefinida':0})
        self.assertTrue(session.source.samefile(self.video),'A sessão deve usar o vídeo importado, inclusive com caminhos curtos do Windows')
        self.assertEqual(session.evaluation,{},'Um vídeo novo não herda a avaliação do exemplo')
        target=self.root/'exportado.zip';session.export(target)
        with zipfile.ZipFile(target) as archive:
            self.assertIn('mapa.json',archive.namelist())
            self.assertNotIn('avaliacao.json',archive.namelist())


if __name__=='__main__':unittest.main()
