"""Interação com o mapa no tamanho da tela e persistência pelo diálogo Qt."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
HAS_QT=importlib.util.find_spec('PySide6') is not None
if HAS_QT:
    from PySide6.QtCore import QCoreApplication,QEvent,QPoint,Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication


@unittest.skipUnless(HAS_QT,'Instale requirements-app.txt para verificar o editor.')
class EditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt=QApplication.instance() or QApplication([])

    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('app.editor'),'Editor visual ainda não implementado')
        from app.editor import MapCanvas
        self.canvas=MapCanvas();self.canvas.resize(640,480);self.canvas.show()
        self.canvas.set_map(np.full((180,320,3),100,np.uint8),[])
        self.qt.processEvents();self.addCleanup(self.dispose,self.canvas)

    @staticmethod
    def dispose(widget):
        import shiboken6
        if shiboken6.isValid(widget):
            widget.close();widget.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)

    def point(self,x,y):
        rect=self.canvas.image_rect()
        return QPoint(round(rect.x()+x*rect.width()/320),round(rect.y()+y*rect.height()/180))

    def rectangle(self):
        self.canvas.set_tool('rectangle')
        QTest.mousePress(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(20,20))
        QTest.mouseMove(self.canvas,self.point(110,100))
        QTest.mouseRelease(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(110,100))

    def test_draw_move_corner_and_undo_keep_source_coordinates(self):
        self.rectangle()
        self.assertEqual(self.canvas.spaces[0]['points'],[[20,20],[110,20],[110,100],[20,100]])
        self.canvas.set_tool('select')
        QTest.mousePress(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(60,60))
        QTest.mouseMove(self.canvas,self.point(80,70))
        QTest.mouseRelease(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(80,70))
        self.assertEqual(self.canvas.spaces[0]['points'][0],[40,30])
        QTest.mousePress(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(40,30))
        QTest.mouseMove(self.canvas,self.point(30,25))
        QTest.mouseRelease(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(30,25))
        self.assertEqual(self.canvas.spaces[0]['points'][0],[30,25])
        self.canvas.undo()
        self.assertEqual(self.canvas.spaces[0]['points'][0],[40,30])
        self.canvas.redo()
        self.assertEqual(self.canvas.spaces[0]['points'][0],[30,25])
        self.canvas.delete_selected();self.assertEqual(self.canvas.spaces,[])
        self.canvas.undo();self.assertEqual(self.canvas.spaces[0]['id'],'V01')

    def test_letterbox_and_invalid_four_points_do_not_create_spaces(self):
        self.canvas.set_tool('polygon')
        QTest.mouseClick(self.canvas,Qt.MouseButton.LeftButton,pos=QPoint(10,5))
        self.assertEqual(self.canvas.pending_points,[])
        for x,y in [(10,10),(100,100),(10,100),(100,10)]:
            QTest.mouseClick(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(x,y))
        self.assertEqual(self.canvas.spaces,[])
        self.assertEqual(self.canvas.pending_points,[])
        for x,y in [(10,10),(100,20),(90,110),(20,100)]:
            QTest.mouseClick(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(x,y))
        self.assertEqual(self.canvas.spaces[0]['points'],[[10,10],[100,20],[90,110],[20,100]])

    def test_drag_outside_image_is_clamped_and_resize_keeps_geometry(self):
        self.rectangle();before=self.canvas.spaces[0]['points']
        self.canvas.resize(900,300);self.qt.processEvents()
        self.assertEqual(self.canvas.spaces[0]['points'],before)
        self.canvas.set_tool('select')
        QTest.mousePress(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(60,60))
        QTest.mouseMove(self.canvas,QPoint(0,0))
        QTest.mouseRelease(self.canvas,Qt.MouseButton.LeftButton,pos=QPoint(0,0))
        points=self.canvas.spaces[0]['points']
        self.assertTrue(all(0<=x<320 and 0<=y<180 for x,y in points))
        self.assertEqual(max(p[0] for p in points)-min(p[0] for p in points),90)

    def test_escape_cancels_an_unfinished_drag_without_losing_undo(self):
        self.rectangle();self.canvas.set_tool('select')
        QTest.mousePress(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(60,60))
        QTest.mouseMove(self.canvas,self.point(90,80))
        QTest.keyClick(self.canvas,Qt.Key.Key_Escape)
        QTest.mouseRelease(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(90,80))
        self.assertEqual(self.canvas.spaces[0]['points'][0],[20,20])
        self.canvas.undo();self.assertEqual(self.canvas.spaces,[])

    def test_panel_import_preview_save_and_reopen_profile(self):
        from app.editor import EditorPanel
        from app.perfis import ProfileStore
        from test_perfis import make_video
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);video=root/'pátio.avi';make_video(video)
            store=ProfileStore(root/'perfis')
            dialog=EditorPanel(ROOT,store=store);dialog.show();self.addCleanup(self.dispose,dialog)
            self.assertFalse(dialog.save_button.isEnabled())
            dialog.import_video(video)
            dialog.name_edit.setText('Meu estacionamento')
            dialog.canvas.set_map(dialog.frame,[{'id':'V01','points':[[20,20],[110,20],[110,100],[20,100]]}])
            self.qt.processEvents()
            dialog.preview_button.click()
            self.assertIn('Livre',dialog.preview_label.text())
            dialog.seek_frame(5)
            self.assertEqual(dialog.canvas.spaces[0]['points'][2],[110,100])
            self.assertTrue(dialog.save_button.isEnabled())
            dialog.save_button.click()
            self.assertIsNotNone(dialog.saved_profile,dialog.message.text())
            reopened=EditorPanel(ROOT,store=store,profile=dialog.saved_profile)
            reopened.show();self.addCleanup(self.dispose,reopened)
            self.assertEqual(reopened.canvas.spaces[0]['id'],'V01')
            self.assertEqual(reopened.name_edit.text(),'Meu estacionamento')
            reopened.canvas.select('V01')
            reopened.canvas.delete_selected()
            reopened.back_button.click()
            self.assertEqual(len(__import__('json').loads(store.list()[0].config.read_text())['spaces']),1)

    def test_delete_during_drag_cancels_the_gesture(self):
        self.rectangle();self.canvas.set_tool('select')
        QTest.mousePress(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(60,60))
        QTest.mouseMove(self.canvas,self.point(90,80))
        QTest.keyClick(self.canvas,Qt.Key.Key_Delete)
        QTest.mouseMove(self.canvas,self.point(100,90))
        QTest.mouseRelease(self.canvas,Qt.MouseButton.LeftButton,pos=self.point(100,90))
        self.assertEqual(self.canvas.spaces,[])
        self.canvas.undo();self.assertEqual(self.canvas.spaces[0]['points'][0],[20,20])

    def test_unavailable_profile_cannot_leave_the_wrong_name_selected(self):
        from app.editor import EditorPanel
        from app.perfis import ProfileStore,probe_video
        from test_perfis import make_video
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);first=root/'primeiro.avi';second=root/'segundo.avi'
            make_video(first);make_video(second)
            store=ProfileStore(root/'perfis')
            config={'width':320,'height':180,'method':'texture','free_ratio':.11,'occupied_ratio':.12,
                'spaces':[{'id':'V01','points':[[20,20],[110,20],[110,100],[20,100]]}]}
            a=store.save('A',probe_video(first),config);b=store.save('B',probe_video(second),config)
            panel=EditorPanel(ROOT,store=store,profile=a);self.addCleanup(self.dispose,panel)
            second.unlink()
            index=next(i for i in range(panel.profile_combo.count()) if getattr(panel.profile_combo.itemData(i),'id',None)==b.id)
            panel.profile_combo.setCurrentIndex(index)
            self.assertEqual(panel.profile_combo.currentData().id,a.id)
            self.assertEqual(panel.profile.id,a.id)
            self.assertIn('vídeo',panel.message.text())

    def test_main_window_analyzes_custom_profile_and_reprocesses_an_edited_map(self):
        from app.janela import MainWindow
        self.assertTrue(hasattr(MainWindow,'use_profile'),'Janela ainda não alterna para vídeos cadastrados')
        from app.perfis import ProfileStore,probe_video
        from test_perfis import make_video
        tmp=self.enterContext(tempfile.TemporaryDirectory())
        root=Path(tmp);video=root/'pátio.avi';make_video(video)
        store=ProfileStore(root/'perfis');info=probe_video(video)
        config={'width':320,'height':180,'method':'texture','stable_frames':2,
            'free_ratio':.11,'occupied_ratio':.12,'spaces':[{'id':'V01','points':[[20,20],[110,20],[110,100],[20,100]]}]}
        profile=store.save('Pátio próprio',info,config)
        window=MainWindow(ROOT,profile=profile);window.show();self.addCleanup(self.dispose,window)
        def wait_analysis():
            deadline=time.monotonic()+15
            while window.session is None and time.monotonic()<deadline:QTest.qWait(50)
            self.assertIsNotNone(window.session,window.status_label.text())
        wait_analysis()
        self.assertEqual(window.session.source,video)
        self.assertIn('Pátio próprio',window.subtitle.text())
        self.assertEqual(window.source_badge.text(),'Vídeo local')
        self.assertEqual(window.free_value.text(),'1')
        self.assertEqual(window.unknown_value.text(),'0')
        self.assertEqual(window.session.evaluation,{})
        self.assertIn('Sem avaliação rotulada',window.about.toPlainText())
        config['spaces'].append({'id':'V02','points':[[150,20],[230,20],[230,100],[150,100]]})
        changed=store.save('Pátio próprio',info,config,existing=profile)
        window.use_profile(changed)
        self.assertIsNone(window.session)
        self.assertFalse(window.play_button.isEnabled())
        wait_analysis()
        self.assertEqual(window.free_value.text(),'2')
        self.assertEqual(len(window.space_rows),2)
        self.assertEqual(window.session.output,changed.output)
        self.assertFalse((changed.output/'avaliacao.json').exists())
        window.open_editor()
        self.assertEqual(window.stack.currentWidget(),window.editor)
        self.assertIs(window.editor.window(),window,'O editor deve permanecer na janela principal')
        self.assertFalse(window.metric_strip.isVisible())
        self.assertEqual(window.heading.text(),'Vídeos e vagas')
        self.qt.processEvents()
        canvas=window.editor.canvas;canvas.set_tool('select')
        area=canvas.image_rect()
        def on_video(x,y):return QPoint(round(area.x()+x*area.width()/320),round(area.y()+y*area.height()/180))
        QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=on_video(60,60))
        QTest.mouseMove(canvas,on_video(90,80))
        QTest.keyClick(canvas,Qt.Key.Key_Escape)
        QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=on_video(90,80))
        self.assertEqual(canvas.spaces[0]['points'][0],[20,20],'Escape deve cancelar o gesto também dentro do painel principal')
        window.editor.back_button.click()
        self.assertEqual(window.stack.currentIndex(),0)
        window.open_editor()
        previous_output=window.editor.profile.output
        window.editor.save_button.click()
        self.assertEqual(window.stack.currentIndex(),0)
        self.assertEqual(window.session.output,previous_output,'Abrir perfil sem edições deve reutilizar a análise')


if __name__=='__main__':unittest.main()
