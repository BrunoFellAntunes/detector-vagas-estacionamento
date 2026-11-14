import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


class AppModelTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('app.modelo'),'Modelo do aplicativo ainda não implementado')
        from app.modelo import load_session
        self.load_session=load_session
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        data=self.root/'dados/terceiros'
        data.mkdir(parents=True)
        (data/'carPark.mp4').write_bytes(b'video')
        config={'width':200,'height':120,'spaces':[
            {'id':'V01','points':[[10,10],[80,10],[80,100],[10,100]]},
            {'id':'V02','points':[[110,10],[180,10],[180,100],[110,100]]}]}
        (data/'vagas_carpark.json').write_text(json.dumps(config),encoding='utf-8')
        (data/'carPark.metadata.json').write_text('{"quadros_decodificados": 3}',encoding='utf-8')
        self.out=self.root/'resultados/carpark'
        self.out.mkdir(parents=True)
        summary={'quadros_processados':3,'vagas_monitoradas':2,'fps_informado_fonte':24.,
                 'interrompido_pelo_usuario':False}
        (self.out/'resumo.json').write_text(json.dumps(summary),encoding='utf-8')
        (self.out/'avaliacao.json').write_text('{"amostras": 6}',encoding='utf-8')
        (self.out/'eventos.csv').write_text('quadro,tempo_video_s,vaga,estado_anterior,estado_atual\n1,0.042,V01,indefinida,ocupada\n1,0.042,V02,indefinida,livre\n2,0.083,V01,ocupada,livre\n',encoding='utf-8')
        self.rows=[(0,'V01','indefinida',.8),(0,'V02','indefinida',0),
                   (1,'V01','ocupada',.8),(1,'V02','livre',0),
                   (2,'V01','livre',0),(2,'V02','livre',0)]
        self.write_rows(self.rows)

    def write_rows(self,rows):
        with (self.out/'ocupacao.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.writer(stream)
            writer.writerow(['quadro','vaga','estado','fracao_alterada'])
            writer.writerows(rows)

    def test_snapshot_counts_follow_selected_frame_and_unknowns(self):
        session=self.load_session(self.root)
        self.assertEqual(session.counts(0),{'livre':0,'ocupada':0,'indefinida':2})
        self.assertEqual(session.counts(1),{'livre':1,'ocupada':1,'indefinida':0})
        self.assertEqual(session.counts(2),{'livre':2,'ocupada':0,'indefinida':0})
        self.assertEqual(session.frame_count,3)

    def test_history_omits_initialization_and_future_events(self):
        session=self.load_session(self.root)
        self.assertEqual(session.history(1),[])
        self.assertEqual([(e['frame'],e['space'],e['state']) for e in session.history(2)],[(2,'V01','livre')])

    def test_incomplete_duplicate_and_unknown_space_rows_are_rejected(self):
        variants=[self.rows[:-1],self.rows+[self.rows[-1]],self.rows+[(0,'INEXISTENTE','livre',0)]]
        for rows in variants:
            self.write_rows(rows)
            with self.subTest(rows=len(rows)),self.assertRaises(ValueError):self.load_session(self.root)

    def test_invalid_ratio_and_interrupted_analysis_are_rejected(self):
        self.write_rows(self.rows[:-1]+[(2,'V02','livre','nan')])
        with self.assertRaises(ValueError):self.load_session(self.root)
        self.write_rows(self.rows)
        path=self.out/'resumo.json'
        summary=json.loads(path.read_text(encoding='utf-8'))
        summary['interrompido_pelo_usuario']=True
        path.write_text(json.dumps(summary),encoding='utf-8')
        with self.assertRaises(ValueError):self.load_session(self.root)

    def test_export_includes_only_results_and_avoids_its_own_archive(self):
        session=self.load_session(self.root)
        (self.out/'ocupacao-antiga.csv').write_text('não exportar',encoding='utf-8')
        target=self.out/'resultados.zip'
        session.export(target)
        import zipfile
        with zipfile.ZipFile(target) as archive:
            self.assertIn('ocupacao.csv',archive.namelist())
            self.assertNotIn('resultados.zip',archive.namelist())
            self.assertNotIn('ocupacao-antiga.csv',archive.namelist())
