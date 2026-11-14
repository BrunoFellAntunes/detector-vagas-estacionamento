"""Janela nativa para apresentar a ocupação das vagas no vídeo analisado."""
from pathlib import Path
import sys
import json
import os
import subprocess

from PySide6.QtCore import Qt,QProcess,QProcessEnvironment,QSignalBlocker,QTimer
from PySide6.QtGui import QColor,QFont,QFontDatabase,QKeySequence,QPainter,QPixmap,QIcon,QShortcut
from PySide6.QtWidgets import (QApplication,QButtonGroup,QComboBox,QFileDialog,QFrame,
    QHBoxLayout,QLabel,QListWidget,QListWidgetItem,QMainWindow,QProgressBar,QPushButton,
    QScrollArea,QSizePolicy,QSlider,QStackedWidget,QTextBrowser,QVBoxLayout,QWidget)

from app.componentes import VideoCanvas,icon
from app.modelo import LABELS,load_session
from app.reproducao import PlaybackController

APP_ROOT=Path(__file__).resolve().parent


def configure_application(application):
    if not application.property('parking_fonts_loaded'):
        for name in ['Sora','Manrope']:
            if QFontDatabase.addApplicationFont(str(APP_ROOT/'fonts'/f'{name}.ttf'))<0:
                raise ValueError(f'Fonte {name} não encontrada. Reinstale os arquivos do projeto.')
        application.setProperty('parking_fonts_loaded',True)
    font=QFont('Manrope');font.setPixelSize(13)
    application.setFont(font)
    application.setStyle('Fusion')
    stylesheet=(APP_ROOT/'estilo.qss').read_text(encoding='utf-8')
    application.setStyleSheet(stylesheet.replace('@APP_ROOT@',APP_ROOT.as_posix()))
    application.setApplicationName('Vaga — Monitoramento de estacionamento')
    pixmap=QPixmap(64,64);pixmap.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pixmap);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor('#355bd5'))
    painter.drawRoundedRect(2,2,60,60,14,14)
    painter.setPen(QColor('#ffffff'));font=QFont('Sora');font.setPixelSize(42);font.setBold(True)
    painter.setFont(font);painter.drawText(pixmap.rect(),Qt.AlignmentFlag.AlignCenter,'P');painter.end()
    application.setWindowIcon(QIcon(pixmap))


def label(text,name=None,wrap=False):
    result=QLabel(text)
    if name:result.setObjectName(name)
    result.setWordWrap(wrap)
    return result


def button(text,symbol=None,role=None):
    result=QPushButton(text)
    if role:result.setProperty('role',role)
    if symbol:result.setIcon(icon(symbol,'#ffffff' if role=='primary' else '#c5d3ea' if role=='nav' else '#3b5276'))
    result.setCursor(Qt.CursorShape.PointingHandCursor)
    return result


def time_text(seconds):
    seconds=max(0,int(seconds))
    return f'{seconds//60:02}:{seconds%60:02}'


class MainWindow(QMainWindow):
    def __init__(self,root,session=None,output=None):
        super().__init__()
        self.root=Path(root)
        self.output=Path(output) if output else self.root/'resultados/carpark'
        self.session=None
        self.controller=None
        self._closing=False
        self._last_history=None
        self._state_cache={}
        self._process_log=''
        self.process=QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        environment=QProcessEnvironment.systemEnvironment()
        environment.insert('PYTHONIOENCODING','utf-8')
        self.process.setProcessEnvironment(environment)
        self.process.readyReadStandardOutput.connect(self._read_process)
        self.process.finished.connect(self._prepared)
        self.process.errorOccurred.connect(self._process_error)
        self.setWindowTitle('Vaga — Monitoramento de estacionamento')
        self.setMinimumSize(1060,700)
        geometry=QApplication.primaryScreen().availableGeometry()
        self.resize(min(1440,geometry.width()-60),min(900,geometry.height()-60))
        self._build()
        self.shortcuts=[]
        for key,action in [('F11',self.toggle_presentation),('Escape',self._escape)]:
            shortcut=QShortcut(QKeySequence(key),self)
            shortcut.activated.connect(action)
            self.shortcuts.append(shortcut)
        shortcut=QShortcut(QKeySequence('Space'),self.video)
        shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        shortcut.activated.connect(self._toggle_play)
        self.shortcuts.append(shortcut)
        if session is not None:self.set_session(session)
        else:QTimer.singleShot(80,self.prepare)

    def _build(self):
        root=QWidget();root.setObjectName('root');self.setCentralWidget(root)
        overall=QHBoxLayout(root);overall.setContentsMargins(0,0,0,0);overall.setSpacing(0)
        self.sidebar=QFrame();self.sidebar.setObjectName('sidebar');self.sidebar.setFixedWidth(196)
        side=QVBoxLayout(self.sidebar);side.setContentsMargins(18,25,18,18);side.setSpacing(10)
        side.addWidget(label('Vaga','brand'))
        side.addWidget(label('Monitoramento de\nestacionamento','brand_note'))
        side.addSpacing(24)
        self.nav_monitor=button('Monitoramento','grid','nav');self.nav_monitor.setCheckable(True)
        self.nav_about=button('Sobre o projeto','info','nav');self.nav_about.setCheckable(True)
        group=QButtonGroup(self);group.setExclusive(True);group.addButton(self.nav_monitor);group.addButton(self.nav_about)
        self.nav_monitor.setChecked(True)
        self.nav_monitor.clicked.connect(lambda:self.switch_page(0))
        self.nav_about.clicked.connect(lambda:self.switch_page(1))
        side.addWidget(self.nav_monitor);side.addWidget(self.nav_about);side.addStretch(1)
        side.addWidget(label('Últimas alterações','section_title'))
        self.history_empty=label('As mudanças aparecem conforme o vídeo avança.','small',True)
        side.addWidget(self.history_empty)
        self.history_list=QListWidget();self.history_list.setObjectName('history')
        self.history_list.setAccessibleName('Alterações de ocupação até o quadro atual')
        self.history_list.setFixedHeight(166)
        self.history_list.itemClicked.connect(self.jump_to_event)
        side.addWidget(self.history_list)
        side.addSpacing(15)
        side.addWidget(label('Unochapecó\nCiência da Computação · 2026','small',True))
        overall.addWidget(self.sidebar)

        content=QWidget();layout=QVBoxLayout(content);layout.setContentsMargins(24,20,24,16);layout.setSpacing(16)
        head=QHBoxLayout();head.setSpacing(10)
        titles=QVBoxLayout();titles.setSpacing(4)
        self.heading=label('Disponibilidade de vagas','heading')
        self.subtitle=label('Gravação de demonstração · mapa das vagas','subtitle')
        titles.addWidget(self.heading);titles.addWidget(self.subtitle)
        head.addLayout(titles,1)
        self.reprocess_button=button('Reprocessar','refresh','ghost')
        self.reprocess_button.setAccessibleName('Reprocessar o vídeo com o detector')
        self.reprocess_button.clicked.connect(self.prepare)
        self.presentation_button=button('Apresentar','expand','primary')
        self.presentation_button.setToolTip('Modo de apresentação · F11')
        self.presentation_button.clicked.connect(self.toggle_presentation)
        head.addWidget(self.reprocess_button);head.addWidget(self.presentation_button)
        layout.addLayout(head)

        self.metric_strip=QFrame();self.metric_strip.setObjectName('metrics')
        metrics=QHBoxLayout(self.metric_strip);metrics.setContentsMargins(22,14,22,14);metrics.setSpacing(18)
        self.free_value=self._metric(metrics,'Livres','metric_free')
        self._divider(metrics)
        self.occupied_value=self._metric(metrics,'Ocupadas','metric_occupied')
        self._divider(metrics)
        self.unknown_value=self._metric(metrics,'Em análise','metric_unknown')
        metrics.addStretch(1)
        note=label('Somente as vagas\ndestacadas são monitoradas.','small');note.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        metrics.addWidget(note)
        layout.addWidget(self.metric_strip)

        self.stack=QStackedWidget()
        monitor=QWidget();body=QHBoxLayout(monitor);body.setContentsMargins(0,0,0,0);body.setSpacing(18)
        video_panel=QFrame();video_panel.setObjectName('video_panel')
        vl=QVBoxLayout(video_panel);vl.setContentsMargins(12,12,12,12);vl.setSpacing(9)
        video_head=QHBoxLayout();video_head.addWidget(label('Visão do estacionamento','section_title'))
        video_head.addStretch(1);video_head.addWidget(label('Vídeo de terceiros','source_badge'))
        vl.addLayout(video_head)
        self.video=VideoCanvas();self.video.space_clicked.connect(self.select_space)
        vl.addWidget(self.video,1)
        self.busy=QProgressBar();self.busy.setRange(0,0);self.busy.setTextVisible(False);self.busy.hide()
        vl.addWidget(self.busy)
        seek_line=QHBoxLayout();seek_line.setSpacing(10)
        self.seek_slider=QSlider(Qt.Orientation.Horizontal);self.seek_slider.setRange(0,678)
        self.seek_slider.setTracking(False);self.seek_slider.setAccessibleName('Posição da reprodução em quadros')
        self.seek_slider.valueChanged.connect(self._seek)
        self.position_label=label('00:00 / 00:28','small');self.position_label.setMinimumWidth(91)
        seek_line.addWidget(self.seek_slider,1);seek_line.addWidget(self.position_label)
        vl.addLayout(seek_line)
        controls=QHBoxLayout();controls.setSpacing(8)
        self.play_button=button('Reproduzir','play','primary');self.play_button.setMinimumWidth(124)
        self.play_button.clicked.connect(self._toggle_play)
        self.restart_button=button('','restart');self.restart_button.setFixedWidth(39)
        self.restart_button.setAccessibleName('Reiniciar o vídeo');self.restart_button.setToolTip('Reiniciar o vídeo')
        self.restart_button.clicked.connect(self._restart)
        self.speed_combo=QComboBox();self.speed_combo.setAccessibleName('Velocidade da reprodução')
        for text,value in [('0,5×',.5),('1×',1.),('1,5×',1.5),('2×',2.)]:self.speed_combo.addItem(text,value)
        self.speed_combo.setCurrentIndex(1);self.speed_combo.setFixedWidth(74)
        self.speed_combo.currentIndexChanged.connect(self._speed_changed)
        self.overlay_button=button('Marcações','eye');self.overlay_button.setCheckable(True);self.overlay_button.setChecked(True)
        self.overlay_button.setAccessibleName('Mostrar ou ocultar marcações das vagas')
        self.overlay_button.clicked.connect(self._toggle_overlay)
        controls.addWidget(self.play_button);controls.addWidget(self.restart_button);controls.addWidget(self.speed_combo)
        controls.addStretch(1);controls.addWidget(self.overlay_button)
        vl.addLayout(controls)
        body.addWidget(video_panel,1)

        spaces_panel=QFrame();spaces_panel.setObjectName('spaces_panel');spaces_panel.setFixedWidth(252)
        sl=QVBoxLayout(spaces_panel);sl.setContentsMargins(15,15,15,15);sl.setSpacing(10)
        sl.addWidget(label('Vagas monitoradas','section_title'))
        self.filter_combo=QComboBox();self.filter_combo.setAccessibleName('Filtrar vagas por estado')
        for text,value in [('Todas as vagas',None),('Somente livres','livre'),('Somente ocupadas','ocupada'),('Em análise','indefinida')]:
            self.filter_combo.addItem(text,value)
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        sl.addWidget(self.filter_combo)
        self.space_scroll=QScrollArea();self.space_scroll.setWidgetResizable(True)
        self.space_scroll.viewport().setObjectName('spaces_viewport')
        self.space_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.space_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.space_scroll.setAccessibleName('Lista de todas as vagas monitoradas')
        rows_widget=QWidget();rows_widget.setObjectName('space_rows');self.rows_layout=QVBoxLayout(rows_widget)
        self.rows_layout.setContentsMargins(0,0,5,0);self.rows_layout.setSpacing(7)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.space_scroll.setWidget(rows_widget);sl.addWidget(self.space_scroll,1)
        self.empty_spaces=label('Nenhuma vaga neste estado no quadro atual.','muted',True);self.empty_spaces.hide()
        sl.addWidget(self.empty_spaces)
        self.selection_detail=label('Selecione uma vaga para destacá-la no vídeo.','selection_detail',True)
        self.selection_detail.setMinimumHeight(40);sl.addWidget(self.selection_detail)
        self.export_button=button('Exportar resultados','download');self.export_button.clicked.connect(self.export_results)
        sl.addWidget(self.export_button)
        body.addWidget(spaces_panel)
        self.stack.addWidget(monitor)
        about_panel=QFrame();about_panel.setObjectName('about_panel')
        about_layout=QHBoxLayout(about_panel);about_layout.setContentsMargins(12,10,12,10);about_layout.setSpacing(0)
        self.about=QTextBrowser();self.about.setMaximumWidth(800)
        self.about.setOpenExternalLinks(True);self.about.setAccessibleName('Descrição e resultados do projeto')
        about_layout.addWidget(self.about,1);about_layout.addStretch(0)
        self.stack.addWidget(about_panel)
        layout.addWidget(self.stack,1)
        footer=QHBoxLayout();self.footer=QWidget();self.footer.setLayout(footer);footer.setContentsMargins(0,0,0,0)
        footer.addWidget(label('Robótica e Visão Computacional','small'));footer.addStretch(1)
        self.status_label=label('Preparando a análise…','small');footer.addWidget(self.status_label)
        layout.addWidget(self.footer)
        overall.addWidget(content,1)
        self.space_rows={};self.state_labels={}
        self.control_widgets=[self.play_button,self.restart_button,self.speed_combo,self.seek_slider,
                              self.overlay_button,self.filter_combo,self.export_button,self.history_list,self.video]
        self._enable_controls(False)
        self._update_about()

    def _metric(self,layout,text,name):
        column=QHBoxLayout();column.setSpacing(11)
        value=label('—',name);value.setMinimumWidth(35)
        column.addWidget(value);column.addWidget(label(text,'metric_label'));column.addStretch(1)
        layout.addLayout(column,1)
        return value

    def _divider(self,layout):
        divider=QFrame();divider.setObjectName('divider');divider.setFixedSize(1,44);layout.addWidget(divider)

    def _enable_controls(self,enabled):
        for widget in self.control_widgets:widget.setEnabled(enabled)

    def set_session(self,session):
        if self.controller:
            self.controller.close();self.controller.deleteLater()
        self.session=session
        self.controller=PlaybackController(session,self)
        self.controller.frame_changed.connect(self._frame_changed)
        self.controller.playing_changed.connect(self._playing_changed)
        self.controller.failed.connect(self._show_playback_error)
        while self.rows_layout.count():
            item=self.rows_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self.space_rows={};self.state_labels={};self._state_cache={};self._last_history=None
        for space in session.spaces:
            name=space['id']
            row=button('',role='space');row.setProperty('selected',False)
            row.setAccessibleName(f'Destacar vaga {name}')
            row.clicked.connect(lambda checked=False,name=name:self.select_space(name))
            contents=QHBoxLayout(row);contents.setContentsMargins(8,4,8,4)
            name_label=label(name,'space_id');state_label=label('Em análise','space_state')
            for child in [name_label,state_label]:child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            contents.addWidget(name_label);contents.addStretch(1);contents.addWidget(state_label)
            self.space_rows[name]=row;self.state_labels[name]=state_label;self.rows_layout.addWidget(row)
        self.video.selected_space=None
        self.selection_detail.setText('Selecione uma vaga para destacá-la no vídeo.')
        self.seek_slider.setMaximum(session.frame_count-1)
        self.busy.hide();self.reprocess_button.setEnabled(True)
        self._enable_controls(True)
        self.subtitle.setText(f'Gravação de demonstração · {len(session.spaces)} vagas monitoradas')
        self.controller.set_speed(float(self.speed_combo.currentData()))
        self.controller.seek(min(60,session.frame_count-1))
        self.play_button.setFocus(Qt.FocusReason.OtherFocusReason)
        self.status_label.setText('Análise pronta · reprodução pausada')
        self._update_about()

    def _frame_changed(self,index,frame):
        results=self.session.snapshot(index)
        self.video.set_frame(frame,self.session.spaces,results)
        counts=self.session.counts(index)
        self.free_value.setText(str(counts['livre']))
        self.occupied_value.setText(str(counts['ocupada']))
        self.unknown_value.setText(str(counts['indefinida']))
        blocker=QSignalBlocker(self.seek_slider);self.seek_slider.setValue(index);del blocker
        self.position_label.setText(f'{time_text(index/self.session.fps)} / {time_text(self.session.frame_count/self.session.fps)}')
        for result in results:
            name=result['id'];state=result['state']
            if self._state_cache.get(name)!=state:
                self.state_labels[name].setText(LABELS[state])
                state_label=self.state_labels[name]
                state_label.setProperty('state',state)
                state_label.style().unpolish(state_label);state_label.style().polish(state_label)
                self.space_rows[name].setAccessibleName(f'Vaga {name}: {LABELS[state]}. Clique para destacar.')
                self._state_cache[name]=state
        self._apply_filter()
        self._update_detail()
        history=self.session.history(index)
        key=tuple((e['frame'],e['space'],e['state']) for e in history)
        if key!=self._last_history:
            self._last_history=key;self.history_list.clear()
            for event in reversed(history):
                item=QListWidgetItem(f"{event['space']} · {LABELS[event['state']]}\n{time_text(event['time'])}  ·  quadro {event['frame']}")
                item.setData(Qt.ItemDataRole.UserRole,event)
                item.setToolTip('Ir para esta alteração no vídeo')
                self.history_list.addItem(item)
            self.history_list.setVisible(bool(history));self.history_empty.setVisible(not history)

    def _playing_changed(self,playing):
        self.play_button.setText('Pausar' if playing else 'Reproduzir')
        self.play_button.setIcon(icon('pause' if playing else 'play','#ffffff'))
        self.status_label.setText('Reproduzindo gravação' if playing else 'Reprodução pausada')

    def _toggle_play(self):
        if self.controller and self.play_button.isEnabled():self.controller.toggle()

    def _restart(self):
        if self.controller:self.controller.restart()

    def _seek(self,value):
        if self.controller:self.controller.seek(value)

    def _speed_changed(self):
        if self.controller:self.controller.set_speed(float(self.speed_combo.currentData()))

    def _toggle_overlay(self,checked):
        self.video.show_overlays=checked;self.video.update()

    def _apply_filter(self):
        selected=self.filter_combo.currentData()
        visible=0
        for name,row in self.space_rows.items():
            show=selected is None or self._state_cache.get(name)==selected
            row.setVisible(show);visible+=show
        self.empty_spaces.setVisible(bool(self.session) and visible==0)

    def select_space(self,name):
        if not self.session or name not in self.space_rows:return
        self.video.selected_space=name;self.video.update()
        for key,row in self.space_rows.items():
            value=key==name
            if row.property('selected')!=value:
                row.setProperty('selected',value);row.style().unpolish(row);row.style().polish(row)
        self._update_detail()

    def _update_detail(self):
        name=self.video.selected_space
        if not name or not self.controller:return
        result=next(r for r in self.session.snapshot(self.controller.index) if r['id']==name)
        measure='Textura detectada' if self.session.method=='texture' else 'Área alterada'
        detail=f"{name} · {LABELS[result['state']]}\n{measure}: {result['ratio']:.0%}"
        if result.get('reason'):detail+='\n'+result['reason']
        self.selection_detail.setText(detail)

    def jump_to_event(self,item):
        if not self.controller:return
        event=item.data(Qt.ItemDataRole.UserRole)
        self.controller.pause();self.controller.seek(event['frame']);self.select_space(event['space'])

    def switch_page(self,index):
        if self.controller:self.controller.pause()
        self.stack.setCurrentIndex(index);self.metric_strip.setVisible(index==0)
        self.heading.setText('Disponibilidade de vagas' if index==0 else 'Sobre o projeto')
        self.subtitle.setText((f'Gravação de demonstração · {len(self.session.spaces)} vagas monitoradas' if self.session else 'Gravação de demonstração · mapa das vagas') if index==0 else 'Método, resultados e limites da demonstração')

    def toggle_presentation(self):
        if self.isFullScreen():
            self.showNormal();self.sidebar.show();self.footer.show()
            self.presentation_button.setText('Apresentar');self.presentation_button.setIcon(icon('expand','#ffffff'))
        else:
            self.sidebar.hide();self.footer.hide();self.showFullScreen()
            self.presentation_button.setText('Sair da apresentação');self.presentation_button.setIcon(icon('shrink','#ffffff'))
        if self.stack.currentIndex()==0:self.video.setFocus(Qt.FocusReason.OtherFocusReason)

    def _escape(self):
        if self.isFullScreen():self.toggle_presentation()
        elif self.controller:self.controller.pause()

    def prepare(self):
        if self._closing or self.process.state()!=QProcess.ProcessState.NotRunning:return
        if self.controller:
            self.controller.close();self.controller.deleteLater();self.controller=None
        self.session=None
        self._enable_controls(False);self.reprocess_button.setEnabled(False)
        self.busy.show();self._process_log=''
        self.history_list.clear();self.history_list.hide();self.history_empty.show()
        self.history_empty.setText('As mudanças aparecem conforme o vídeo avança.')
        self.selection_detail.setText('Aguardando a conclusão da análise.')
        for state_label in self.state_labels.values():
            state_label.setText('Aguardando');state_label.setProperty('state',None)
            state_label.style().unpolish(state_label);state_label.style().polish(state_label)
        self._update_about()
        self.video.clear('Analisando a gravação','O detector está conferindo os 679 quadros do vídeo.')
        for value in [self.free_value,self.occupied_value,self.unknown_value]:value.setText('—')
        self.status_label.setText('Processando o vídeo…')
        self.process.setWorkingDirectory(str(self.root))
        data=self.root/'dados/terceiros'
        self.process.start(sys.executable,[str(self.root/'detector.py'),'--source',str(data/'carPark.mp4'),
            '--reference',str(data/'referencia_carpark.png'),'--config',str(data/'vagas_completas_carpark.json'),
            '--output',str(self.output)])

    def _read_process(self):
        self._process_log+=bytes(self.process.readAllStandardOutput()).decode('utf-8',errors='replace')
        self._process_log=self._process_log[-10000:]

    def _prepared(self,exit_code,exit_status):
        if self._closing:return
        self._read_process()
        if exit_code!=0 or exit_status!=QProcess.ExitStatus.NormalExit:
            self._prepare_failed('A análise não foi concluída. Clique em Reprocessar para tentar novamente.')
            return
        try:
            from avaliar import evaluate
            data=self.root/'dados/terceiros'
            summary=json.loads((self.output/'resumo.json').read_text(encoding='utf-8'))
            expected=json.loads((data/'carPark.metadata.json').read_text(encoding='utf-8'))['quadros_decodificados']
            if summary['quadros_processados']!=expected or summary['interrompido_pelo_usuario']:
                raise ValueError('O vídeo não foi processado por completo. Tente reprocessar.')
            evaluation=evaluate(self.output/'ocupacao.csv',data/'rotulos_completos_carpark.csv')
            (self.output/'avaliacao.json').write_text(json.dumps(evaluation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            self.set_session(load_session(self.root,self.output))
        except (OSError,ValueError,KeyError,TypeError) as error:self._prepare_failed(str(error))

    def _process_error(self,error):
        if not self._closing and error==QProcess.ProcessError.FailedToStart:
            self._prepare_failed('Não foi possível iniciar o Python. Confira a instalação do aplicativo.')

    def _prepare_failed(self,message):
        self.busy.hide();self.reprocess_button.setEnabled(True)
        self.status_label.setText('Não foi possível preparar o vídeo')
        self.video.clear('A análise precisa de atenção',message)
        self.video.setToolTip(self._process_log[-3000:])

    def _show_playback_error(self,message):
        self.status_label.setText(message)

    def export_results(self):
        if not self.session:return
        self.controller.pause()
        filename,_=QFileDialog.getSaveFileName(self,'Exportar resultados',str(Path.home()/'resultados-vagas.zip'),'Arquivo ZIP (*.zip)')
        if not filename:return
        try:
            self.session.export(filename)
            self.status_label.setText('Resultados exportados com sucesso')
        except (OSError,ValueError) as error:self.status_label.setText(f'Não foi possível exportar: {error}')

    def _update_about(self):
        metrics='A análise ainda está sendo preparada.'
        if self.session:
            evaluation=self.session.evaluation
            coverage=f"{evaluation['cobertura']:.2%}".replace('.',',')
            concordance=f"{evaluation['concordancia_total']:.2%}".replace('.',',')
            metrics=(f"<b>{evaluation['amostras']} rótulos visuais</b> conferidos no mesmo clipe: "
                     f"{concordance} de concordância total e "
                     f"{coverage} de cobertura. Estados indefinidos permanecem no denominador. "
                     'A amostra é exploratória e não mede generalização para outros estacionamentos.')
        self.about.setHtml(f'''<html><body style="font-family:Manrope;color:#253b50;font-size:14px;line-height:1.6">
        <h1 style="font-family:Sora;font-size:26px;color:#192f49">Monitoramento inteligente de vagas</h1>
        <p>Projeto de Robótica e Visão Computacional da Unochapecó.<br>Docente: Wagner Titon.</p>
        <h2 style="font-family:Sora;font-size:17px">O que o aplicativo mostra</h2>
        <p>Mapa com 71 regiões cadastradas: 69 vagas e duas áreas centrais de ocupação ambígua. A janela sincroniza o quadro reproduzido com os estados calculados pelo detector, sem conexão com uma câmera ao vivo. A região acima da V59 está incluída como V69. A van central abrange V70 e V71: quando um mesmo objeto claro atravessa ambas, elas ficam em análise. Ilhas, corredores e áreas fora do enquadramento não entram na contagem.</p>
        <h2 style="font-family:Sora;font-size:17px">Como funciona</h2>
        <p>Python, OpenCV e NumPy medem a densidade de textura dentro de cada vaga usando suavização, limiarização adaptativa, filtro de mediana e dilatação. Dois limiares e cinco quadros consecutivos confirmam o estado, inclusive para carros que ficam parados durante toda a gravação. A interface nativa utiliza Qt. Não há modelo treinado. O percentual de textura não é uma probabilidade de ocupação.</p>
        <h2 style="font-family:Sora;font-size:17px">Resultados e limites</h2><p>{metrics}</p>
        <p>O quadro 678 fornece apenas a resolução do exemplo completo; não é uma referência vazia do mapa completo. Regiões e limiares foram calibrados neste mesmo clipe. Veículos lisos, pedestres, sombras e oclusões podem causar erros. O experimento anterior por referência vazia continua disponível no terminal. A coleta própria e a avaliação em gravações independentes ainda estão pendentes.</p>
        <h2 style="font-family:Sora;font-size:17px">Equipe</h2>
        <p>Vitor Rodi · Pedro Toigo · Bruno Fell Antunes · Edson Leandro Soares</p>
        <h2 style="font-family:Sora;font-size:17px">Origem do vídeo</h2>
        <p>Filmagem de terceiros obtida do repositório de Harsh Bafna. O crédito identifica a fonte de obtenção, não a autoria original da gravação. Mais informações em docs/FONTES_MIDIA.md.</p>
        <p><a style="color:#355bd5" href="https://github.com/VitorRodi/detector-vagas-estacionamento">Abrir o repositório do projeto</a></p>
        </body></html>''')

    def closeEvent(self,event):
        self._closing=True
        if self.controller:self.controller.close()
        if self.process.state()!=QProcess.ProcessState.NotRunning:
            # No Windows, o redirecionador de um ambiente virtual pode criar outro Python.
            # Encerrar a árvore do processo próprio impede deixar esse filho gravando arquivos.
            if os.name=='nt' and self.process.processId():
                try:
                    executable=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/taskkill.exe'
                    subprocess.run([str(executable),'/PID',str(self.process.processId()),'/T','/F'],
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW,timeout=5)
                except (OSError,subprocess.TimeoutExpired):self.process.kill()
            else:self.process.terminate()
            if self.process.state()!=QProcess.ProcessState.NotRunning and not self.process.waitForFinished(1500):
                self.process.kill();self.process.waitForFinished(2000)
        event.accept()
