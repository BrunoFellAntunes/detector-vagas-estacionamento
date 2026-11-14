import csv
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('avaliar'),'Avaliação ainda não implementada')
        from avaliar import evaluate
        self.evaluate=evaluate
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)

    def file(self,name,rows):
        path=self.folder/name
        with path.open('w',encoding='utf-8',newline='') as f:
            writer=csv.writer(f)
            writer.writerow(['quadro','vaga','estado'])
            writer.writerows(rows)
        return path

    def test_reports_confusion_and_coverage_without_discarding_unknowns(self):
        labels=self.file('labels.csv',[(0,'A','ocupada'),(1,'A','livre'),(2,'A','livre'),
                                      (3,'A','ocupada'),(4,'A','ocupada')])
        predictions=self.file('pred.csv',[(0,'A','ocupada'),(1,'A','livre'),(2,'A','ocupada'),
                                         (3,'A','livre'),(4,'A','indefinida')])
        report=self.evaluate(predictions,labels)
        self.assertEqual(report['matriz_confusao'],{'VP':1,'VN':1,'FP':1,'FN':1})
        self.assertEqual(report['amostras'],5)
        self.assertEqual(report['indefinidas'],1)
        self.assertEqual(report['cobertura'],.8)
        self.assertEqual(report['concordancia_total'],.4)
        self.assertEqual(report['acuracia_definidas'],.5)
        self.assertEqual(report['precisao_ocupada'],.5)
        self.assertEqual(report['revocacao_ocupada'],.5)
        self.assertEqual(report['f1_ocupada'],.5)

    def test_missing_prediction_is_an_error(self):
        labels=self.file('labels.csv',[(1,'A','livre')])
        predictions=self.file('pred.csv',[(0,'A','livre')])
        with self.assertRaises(ValueError):self.evaluate(predictions,labels)

    def test_duplicate_prediction_is_an_error(self):
        labels=self.file('labels.csv',[(0,'A','livre')])
        predictions=self.file('pred.csv',[(0,'A','livre'),(0,'A','ocupada')])
        with self.assertRaises(ValueError):self.evaluate(predictions,labels)

    def test_only_unknowns_do_not_produce_invented_zero_metrics(self):
        labels=self.file('labels.csv',[(0,'A','livre')])
        predictions=self.file('pred.csv',[(0,'A','indefinida')])
        result=self.evaluate(predictions,labels)
        self.assertEqual(result['cobertura'],0)
        self.assertEqual(result['concordancia_total'],0)
        self.assertIsNone(result['acuracia_definidas'])
        self.assertIsNone(result['f1_ocupada'])

    def test_unknown_ground_truth_and_empty_labels_are_rejected(self):
        predictions=self.file('pred.csv',[(0,'A','livre')])
        for name,rows in [('unknown.csv',[(0,'A','indefinida')]),('empty.csv',[])]:
            with self.subTest(name=name),self.assertRaises(ValueError):
                self.evaluate(predictions,self.file(name,rows))
