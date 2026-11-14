"""Fluxos do aplicativo com widgets Qt reais, inclusive em modo sem tela."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
HAS_QT=importlib.util.find_spec('PySide6') is not None
if HAS_QT:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication


@unittest.skipUnless(HAS_QT,'Instale requirements-app.txt para verificar a interface Qt.')
class AppWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt=QApplication.instance() or QApplication([])
        result=subprocess.run([sys.executable,str(ROOT/'executar_exemplo.py')],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stderr)

    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('app.janela'),'Janela do aplicativo ainda não implementada')
        from app.modelo import load_session
        from app.janela import MainWindow,configure_application
        configure_application(self.qt)
        self.window=MainWindow(ROOT,session=load_session(ROOT))
        self.window.resize(1440,900)
        self.window.show()
        self.qt.processEvents()
        self.addCleanup(self.window.close)

    def test_counts_follow_seek_and_preserve_initial_unknowns(self):
        self.window.controller.seek(60)
        self.assertEqual(self.window.free_value.text(),'2')
        self.assertEqual(self.window.occupied_value.text(),'3')
        self.window.controller.seek(678)
        self.assertEqual(self.window.free_value.text(),'5')
        self.assertEqual(self.window.occupied_value.text(),'0')
        self.window.controller.seek(0)
        self.assertEqual(self.window.unknown_value.text(),'5')

    def test_filter_and_selection_highlight_the_actual_space(self):
        self.window.controller.seek(60)
        self.window.filter_combo.setCurrentIndex(1)
        self.qt.processEvents()
        visible=[name for name,row in self.window.space_rows.items() if row.isVisible()]
        self.assertEqual(visible,['V04','V05'])
        QTest.mouseClick(self.window.space_rows['V04'],Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.video.selected_space,'V04')
        self.assertIn('V04',self.window.selection_detail.text())
        self.assertIn('Livre',self.window.selection_detail.text())

    def test_space_activates_focused_navigation_instead_of_global_playback(self):
        self.window.nav_about.setFocus(Qt.FocusReason.TabFocusReason)
        QTest.keyClick(self.window.nav_about,Qt.Key.Key_Space)
        self.assertEqual(self.window.stack.currentIndex(),1)
        self.assertFalse(self.window.controller.playing)

    def test_play_pause_end_and_restart(self):
        self.window.controller.seek(60)
        QTest.mouseClick(self.window.play_button,Qt.MouseButton.LeftButton)
        QTest.qWait(130)
        self.assertGreater(self.window.controller.index,60)
        QTest.mouseClick(self.window.play_button,Qt.MouseButton.LeftButton)
        paused=self.window.controller.index
        QTest.qWait(100)
        self.assertEqual(self.window.controller.index,paused)
        self.window.controller.seek(677)
        self.window.controller.play()
        QTest.qWait(150)
        self.assertEqual(self.window.controller.index,678)
        self.assertFalse(self.window.controller.playing)
        QTest.mouseClick(self.window.restart_button,Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.controller.index,0)

    def test_history_rewinds_and_can_jump_to_an_event(self):
        self.window.controller.seek(400)
        self.assertEqual(self.window.history_list.count(),3)
        self.window.controller.seek(200)
        self.assertEqual(self.window.history_list.count(),1)
        item=self.window.history_list.item(0)
        self.window.jump_to_event(item)
        self.assertEqual(self.window.controller.index,147)
        self.assertEqual(self.window.video.selected_space,'V01')

    def test_presentation_restores_normal_window_and_overlay_toggle(self):
        QTest.mouseClick(self.window.presentation_button,Qt.MouseButton.LeftButton)
        self.assertTrue(self.window.isFullScreen())
        self.assertFalse(self.window.sidebar.isVisible())
        QTest.keyClick(self.window,Qt.Key.Key_Escape)
        self.qt.processEvents()
        self.assertFalse(self.window.isFullScreen())
        self.assertTrue(self.window.sidebar.isVisible())
        QTest.mouseClick(self.window.overlay_button,Qt.MouseButton.LeftButton)
        self.assertFalse(self.window.video.show_overlays)

    def test_reprocessing_disables_old_results_and_closes_the_worker(self):
        from PySide6.QtCore import QProcess
        with tempfile.TemporaryDirectory() as tmp:
            try:
                self.window.output=Path(tmp)
                self.window.prepare()
                self.assertFalse(self.window.play_button.isEnabled())
                self.assertFalse(self.window.history_list.isEnabled(),'Histórico antigo continua interativo durante nova análise')
                self.assertIsNone(self.window.session,'A tela ainda mantém a sessão anterior como resultado atual')
                QTest.qWait(100)
            finally:self.window.close()
            self.assertEqual(self.window.process.state(),QProcess.ProcessState.NotRunning)

    def test_startup_processes_the_clip_before_enabling_playback(self):
        from app.janela import MainWindow
        with tempfile.TemporaryDirectory() as tmp:
            window=MainWindow(ROOT,output=Path(tmp))
            window.show()
            try:
                deadline=time.monotonic()+45
                while window.session is None and time.monotonic()<deadline:QTest.qWait(50)
                self.assertIsNotNone(window.session,window.status_label.text())
                self.assertEqual(window.session.frame_count,679)
                self.assertTrue(window.play_button.isEnabled())
                self.assertEqual(window.free_value.text(),'2')
                self.assertTrue((Path(tmp)/'avaliacao.json').is_file())
            finally:window.close()

    def test_failed_preparation_keeps_retry_and_hides_availability(self):
        from app.janela import MainWindow
        with tempfile.TemporaryDirectory() as tmp:
            window=MainWindow(Path(tmp))
            window.show()
            try:
                QTest.qWait(150)
                deadline=time.monotonic()+8
                while not window.reprocess_button.isEnabled() and time.monotonic()<deadline:QTest.qWait(50)
                self.assertTrue(window.reprocess_button.isEnabled())
                self.assertFalse(window.play_button.isEnabled())
                self.assertEqual(window.free_value.text(),'—')
                self.assertIsNone(window.session)
                self.assertIn('atenção',window.video.message)
            finally:window.close()
