"""Classificação por textura quando não existe referência vazia de toda a cena."""
from pathlib import Path
import sys
import unittest
import csv
import json
import subprocess
import tempfile

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from detector import Detector


class TextureTests(unittest.TestCase):
    def setUp(self):
        self.empty=np.full((120,200,3),120,np.uint8)
        self.parked=self.empty.copy()
        for x in range(24,85,8):
            cv2.line(self.parked,(x,24),(x,96),(20,20,20),3)
        self.config={'method':'texture','width':200,'height':120,
                     'occupied_ratio':.12,'free_ratio':.10,'stable_frames':2,
                     'spaces':[{'id':'V01','points':[[10,10],[100,10],[100,110],[10,110]]}]}

    def test_stationary_texture_is_occupied_even_if_present_in_reference(self):
        detector=Detector(self.parked,self.config)
        self.assertEqual(detector.process(self.parked)[0]['state'],'indefinida')
        self.assertEqual(detector.process(self.parked)[0]['state'],'ocupada')

    def test_empty_space_is_free_and_departure_confirms_after_stable_frames(self):
        detector=Detector(self.parked,self.config)
        detector.process(self.parked);detector.process(self.parked)
        self.assertEqual(detector.process(self.empty)[0]['state'],'ocupada')
        self.assertEqual(detector.process(self.empty)[0]['state'],'livre')

    def test_texture_outside_space_does_not_change_occupancy(self):
        detector=Detector(self.empty,self.config)
        outside=self.empty.copy()
        for x in range(130,190,8):cv2.line(outside,(x,0),(x,119),(0,0,0),3)
        self.assertEqual(detector.process(outside,instant=True)[0]['state'],'livre')

    def test_unknown_method_and_invalid_local_thresholds_are_rejected(self):
        for config in [dict(self.config,method='invented'),
                       dict(self.config,spaces=[dict(self.config['spaces'][0],free_ratio=.5,occupied_ratio=.2)]),
                       dict(self.config,texture_block_size=4)]:
            with self.subTest(config=config),self.assertRaises(ValueError):Detector(self.empty,config)

    def test_local_thresholds_are_applied_to_each_space(self):
        relaxed=dict(self.config['spaces'][0],free_ratio=.98,occupied_ratio=.99)
        normal=dict(self.config['spaces'][0],id='V02')
        detector=Detector(self.parked,dict(self.config,spaces=[relaxed,normal]))
        states=[r['state'] for r in detector.process(self.parked,instant=True)]
        self.assertEqual(states,['livre','ocupada'])

    def test_texture_cli_exports_the_correct_measure_and_method(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            cv2.imwrite(str(folder/'frame.png'),self.parked)
            (folder/'config.json').write_text(json.dumps(self.config),encoding='utf-8')
            result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'detector.py'),
                '--source',str(folder/'frame.png'),'--reference',str(folder/'frame.png'),
                '--config',str(folder/'config.json'),'--output',str(folder/'out')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            with (folder/'out/ocupacao.csv').open(encoding='utf-8') as stream:
                row=next(csv.DictReader(stream))
            self.assertIn('densidade_textura',row)
            self.assertNotIn('fracao_alterada',row)
            self.assertEqual(row['estado'],'ocupada')
            self.assertEqual(json.loads((folder/'out/resumo.json').read_text(encoding='utf-8'))['metodo'],'texture')

    def test_object_crossing_two_spaces_keeps_both_under_review(self):
        config=dict(self.config,spaces=[
            {'id':'V01','points':[[10,10],[95,10],[95,110],[10,110]]},
            {'id':'V02','points':[[105,10],[190,10],[190,110],[105,110]]}],
            ambiguous_groups=[{'spaces':['V01','V02'],'brightness_threshold':180,
                'min_region_ratio':.08,'reason':'Ocupação atravessando duas vagas'}])
        crossing=self.empty.copy();cv2.rectangle(crossing,(35,35),(165,85),(240,240,240),-1)
        detector=Detector(self.empty,config)
        for _ in range(8):results=detector.process(crossing)
        self.assertEqual([r['state'] for r in results],['indefinida','indefinida'])
        self.assertTrue(all(r.get('reason')=='Ocupação atravessando duas vagas' for r in results))
        # Remover o objeto elimina o motivo, mas exige novamente confirmação temporal.
        self.assertEqual([r['state'] for r in detector.process(self.empty)],['indefinida','indefinida'])
        results=detector.process(self.empty)
        self.assertEqual([r['state'] for r in results],['livre','livre'])
        self.assertTrue(all(not r.get('reason') for r in results))

    def test_separate_objects_do_not_trigger_cross_space_review(self):
        config=dict(self.config,spaces=[
            {'id':'V01','points':[[10,10],[95,10],[95,110],[10,110]]},
            {'id':'V02','points':[[105,10],[190,10],[190,110],[105,110]]}],
            ambiguous_groups=[{'spaces':['V01','V02'],'brightness_threshold':180,'min_region_ratio':.08}])
        separate=self.empty.copy()
        cv2.rectangle(separate,(25,30),(80,90),(240,240,240),-1)
        cv2.rectangle(separate,(120,30),(175,90),(240,240,240),-1)
        results=Detector(self.empty,config).process(separate,instant=True)
        self.assertTrue(all(not r.get('reason') for r in results))
        self.assertTrue(all(r['state']!='indefinida' for r in results))

    def test_invalid_ambiguity_groups_are_rejected(self):
        for group in [{'spaces':['V01','V99']},{'spaces':['V01','V01']},
                      {'spaces':['V01'],'min_region_ratio':0}]:
            with self.subTest(group=group),self.assertRaises(ValueError):
                Detector(self.empty,dict(self.config,ambiguous_groups=[group]))


if __name__=='__main__':unittest.main()
