"""Editor visual de vagas e cadastro de vídeos, sem alterar a demonstração."""
from copy import deepcopy
import json
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QPointF,QRectF,Qt,QSignalBlocker,Signal
from PySide6.QtGui import QColor,QFont,QKeySequence,QPainter,QPen,QPolygonF,QShortcut
from PySide6.QtWidgets import (QButtonGroup,QComboBox,QDoubleSpinBox,QFileDialog,
    QFormLayout,QFrame,QHBoxLayout,QLabel,QLineEdit,QListWidget,QListWidgetItem,
    QMessageBox,QPushButton,QScrollArea,QSlider,QVBoxLayout,QWidget)

from app.componentes import COLORS,VideoCanvas,icon
from app.perfis import ProfileStore,probe_video
from detector import Detector


class MapCanvas(VideoCanvas):
    changed=Signal()
    selection_changed=Signal(str)
    notice=Signal(str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setAccessibleName('Editor de vagas: desenhe sobre o vídeo ou arraste os cantos de uma vaga')
        self.tool='rectangle';self.pending_points=[];self._drag=None
        self._undo=[];self._redo=[];self._preview=[];self._next_number=1
        self.message='Adicione um vídeo para começar'
        self.message_detail='Use uma gravação com a câmera parada.'

    def set_map(self,frame,spaces):
        self.set_frame(frame,[],[])
        self.spaces=deepcopy(spaces);self.selected_space=None
        self.pending_points=[];self._drag=None;self._undo=[];self._redo=[];self._preview=[]
        numbers=[int(s['id'][1:]) for s in spaces if s['id'].startswith('V') and s['id'][1:].isdigit()]
        self._next_number=max(numbers,default=0)+1
        self.changed.emit();self.selection_changed.emit('');self.update()

    def set_tool(self,tool):
        self._cancel_drag();self.tool=tool;self.update()
        self.setCursor(Qt.CursorShape.ArrowCursor if tool=='select' else Qt.CursorShape.CrossCursor)

    def _cancel_drag(self):
        if self._drag and self._drag[0]!='rectangle':self.spaces=self._drag[2]
        self.pending_points=[];self._drag=None;self.update()

    def _source_point(self,position,clamp=False):
        target=self.image_rect()
        if self.pixmap is None or (not clamp and not target.contains(position)):return None
        scale=target.width()/self.source_width
        return [max(0,min(self.source_width-1,round((position.x()-target.x())/scale))),
                max(0,min(self.source_height-1,round((position.y()-target.y())/scale)))]

    @staticmethod
    def _valid(points):
        array=np.asarray(points,np.int32)
        return len(points)>=3 and cv2.isContourConvex(array) and cv2.contourArea(array)>=4

    def _commit(self,before):
        if before!=self.spaces:
            self._undo.append(before);self._redo.clear();self._preview=[];self.changed.emit()
        self.update()

    def select(self,name):
        self.selected_space=name or None;self.selection_changed.emit(name or '');self.update()

    def delete_selected(self):
        self._cancel_drag()
        before=deepcopy(self.spaces)
        self.spaces=[s for s in self.spaces if s['id']!=self.selected_space]
        self.select(None);self._commit(before)

    def undo(self):
        self._cancel_drag()
        if self._undo:
            self._redo.append(deepcopy(self.spaces));self.spaces=self._undo.pop()
            name=self.selected_space if any(s['id']==self.selected_space for s in self.spaces) else (self.spaces[-1]['id'] if self.spaces else None)
            self._preview=[];self.select(name);self.changed.emit();self.update()

    def redo(self):
        if self._redo:
            self._undo.append(deepcopy(self.spaces));self.spaces=self._redo.pop()
            name=self.selected_space if any(s['id']==self.selected_space for s in self.spaces) else (self.spaces[-1]['id'] if self.spaces else None)
            self._preview=[];self.select(name);self.changed.emit();self.update()

    def _add(self,points):
        if not self._valid(points):
            self.notice.emit('Marque os quatro cantos em volta da vaga, sem cruzar as linhas.');return
        before=deepcopy(self.spaces)
        name=f'V{self._next_number:02}';self._next_number+=1
        self.spaces.append({'id':name,'points':points});self.select(name);self._commit(before)

    def mousePressEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton:return
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        point=self._source_point(event.position())
        if point is None:return
        if self.tool=='rectangle':self.pending_points=[point];self._drag=('rectangle',point)
        elif self.tool=='polygon':
            self.pending_points.append(point)
            if len(self.pending_points)==4:
                points=self.pending_points;self.pending_points=[];self._add(points)
        else:
            selected=next((s for s in self.spaces if s['id']==self.selected_space),None)
            scale=self.image_rect().width()/self.source_width
            corner=None
            if selected:
                corner=next((i for i,p in enumerate(selected['points']) if np.linalg.norm(np.array(p)-point)*scale<=9),None)
            name=selected['id'] if corner is not None else self.hit_test(event.position())
            self.select(name)
            if name:self._drag=('corner' if corner is not None else 'move',point,deepcopy(self.spaces),name,corner)
        self.update()

    def _move_drag(self,position):
        if not self._drag:return
        point=self._source_point(position,clamp=True)
        mode,start,*rest=self._drag
        if mode=='rectangle':self.pending_points=[start,point];return
        before,name,corner=rest
        original=next(s for s in before if s['id']==name)
        points=deepcopy(original['points'])
        if mode=='corner':points[corner]=point
        else:
            dx=max(-min(p[0] for p in points),min(point[0]-start[0],self.source_width-1-max(p[0] for p in points)))
            dy=max(-min(p[1] for p in points),min(point[1]-start[1],self.source_height-1-max(p[1] for p in points)))
            points=[[x+dx,y+dy] for x,y in points]
        if self._valid(points):next(s for s in self.spaces if s['id']==name)['points']=points

    def mouseMoveEvent(self,event):
        self._move_drag(event.position());self.update()

    def mouseReleaseEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton or not self._drag:return
        self._move_drag(event.position())
        if self._drag[0]=='rectangle':
            start,end=self.pending_points[0],self._source_point(event.position(),clamp=True)
            x1,x2=sorted([start[0],end[0]]);y1,y2=sorted([start[1],end[1]])
            scale=self.image_rect().width()/self.source_width
            if (x2-x1)*scale>=6 and (y2-y1)*scale>=6:self._add([[x1,y1],[x2,y1],[x2,y2],[x1,y2]])
            self.pending_points=[]
        else:self._commit(self._drag[2])
        self._drag=None;self.update()

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Delete,Qt.Key.Key_Backspace):self.delete_selected()
        elif event.key()==Qt.Key.Key_Escape:self._cancel_drag()
        elif event.matches(QKeySequence.StandardKey.Undo):self.undo()
        elif event.matches(QKeySequence.StandardKey.Redo):self.redo()
        else:super().keyPressEvent(event)

    def paintEvent(self,event):
        # A base mantém a imagem ajustada; o editor usa azul até a conferência pontual.
        super().paintEvent(event)
        if self.pixmap is None:return
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        target=self.image_rect();painter.setClipRect(target)
        scale=target.width()/self.source_width
        def screen(point):return QPointF(target.x()+point[0]*scale,target.y()+point[1]*scale)
        font=QFont('Manrope');font.setPixelSize(11);font.setBold(True);painter.setFont(font)
        results={r['id']:r for r in self._preview}
        for space in self.spaces:
            selected=space['id']==self.selected_space
            color=QColor(COLORS[results[space['id']]['state']] if space['id'] in results else '#6488f5')
            fill=QColor(color);fill.setAlpha(40 if selected else 18)
            painter.setPen(QPen(QColor('#ffffff') if selected else color,3 if selected else 2));painter.setBrush(fill)
            polygon=QPolygonF([screen(p) for p in space['points']]);painter.drawPolygon(polygon)
            top=polygon.boundingRect().topLeft()
            badge=QRectF(max(target.left(),min(top.x(),target.right()-46)),max(target.top(),top.y()),46,18)
            painter.fillRect(badge,QColor('#152a3b'));painter.setPen(color)
            painter.drawText(badge,Qt.AlignmentFlag.AlignCenter,space['id'])
            if selected:
                painter.setPen(QPen(QColor('#355bd5'),2));painter.setBrush(QColor('#ffffff'))
                for point in space['points']:painter.drawEllipse(screen(point),5,5)
        if self.pending_points:
            painter.setPen(QPen(QColor('#ffffff'),2,Qt.PenStyle.DashLine));painter.setBrush(Qt.BrushStyle.NoBrush)
            if self.tool=='rectangle' and len(self.pending_points)==2:
                painter.drawRect(QRectF(screen(self.pending_points[0]),screen(self.pending_points[1])).normalized())
            else:
                painter.drawPolyline(QPolygonF([screen(p) for p in self.pending_points]))
                for point in self.pending_points:painter.drawEllipse(screen(point),4,4)


def text(value,name=None):
    widget=QLabel(value);widget.setWordWrap(True);widget.setTextFormat(Qt.TextFormat.PlainText)
    if name:widget.setObjectName(name)
    return widget


class EditorPanel(QWidget):
    profile_saved=Signal(object)
    back_requested=Signal()

    def __init__(self,root,store=None,profile=None,parent=None):
        super().__init__(parent)
        self.root=Path(root);self.store=store or ProfileStore(self.root/'perfis')
        self.saved_profile=None;self.profile=None;self.video_info=None;self.frame=None
        self.config={};self._dirty=False;self._loading=False;self._combo_index=0
        self.setObjectName('map_editor')
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(10)
        self.import_button=QPushButton('Adicionar vídeo');self.import_button.setProperty('role','primary')
        self.import_button.clicked.connect(self.choose_video)
        choose=QHBoxLayout();choose.addWidget(text('Perfil salvo'))
        self.profile_combo=QComboBox();self.profile_combo.setAccessibleName('Escolher estacionamento salvo')
        self._populate_profiles()
        self.profile_combo.currentIndexChanged.connect(self._choose_profile)
        choose.addWidget(self.profile_combo,1);choose.addWidget(self.import_button);layout.addLayout(choose)
        body=QHBoxLayout();body.setSpacing(16)
        panel=QFrame();panel.setObjectName('video_panel');left=QVBoxLayout(panel)
        tools=QHBoxLayout();tools.setSpacing(6);group=QButtonGroup(self);self.tool_buttons={}
        for name,title in [('rectangle','Retângulo'),('polygon','4 pontos'),('select','Mover / ajustar')]:
            item=QPushButton(title);item.setCheckable(True);group.addButton(item)
            item.clicked.connect(lambda checked=False,name=name:self.set_tool(name))
            self.tool_buttons[name]=item;tools.addWidget(item)
        self.tool_buttons['rectangle'].setChecked(True);tools.addStretch(1)
        self.undo_button=QPushButton();self.redo_button=QPushButton()
        for item,title,symbol in [(self.undo_button,'Desfazer · Ctrl+Z','undo'),(self.redo_button,'Refazer · Ctrl+Y','redo')]:
            item.setFixedWidth(36);item.setAccessibleName(title);item.setToolTip(title);item.setIcon(icon(symbol))
        self.undo_button.clicked.connect(lambda:self.canvas.undo());self.redo_button.clicked.connect(lambda:self.canvas.redo())
        tools.addWidget(self.undo_button);tools.addWidget(self.redo_button);left.addLayout(tools)
        self.hint=text('Retângulo: clique e arraste sobre uma vaga.','small');left.addWidget(self.hint)
        self.canvas=MapCanvas();left.addWidget(self.canvas,1)
        self.canvas.changed.connect(self._map_changed);self.canvas.selection_changed.connect(self._selected)
        self.canvas.notice.connect(self.message_from_canvas)
        timeline=QHBoxLayout();self.frame_slider=QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setTracking(False);self.frame_slider.setAccessibleName('Escolher quadro para desenhar as vagas')
        self.frame_slider.valueChanged.connect(self.seek_frame)
        self.frame_label=text('Nenhum vídeo','small');timeline.addWidget(self.frame_slider,1);timeline.addWidget(self.frame_label)
        left.addLayout(timeline);self.video_label=text('O vídeo permanece na pasta original.','small');left.addWidget(self.video_label)
        body.addWidget(panel,1)
        settings=QScrollArea();settings.setObjectName('editor_settings');settings.setFixedWidth(264)
        settings.setWidgetResizable(True);settings.setFrameShape(QFrame.Shape.NoFrame)
        settings.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_content=QWidget();settings_content.setObjectName('editor_settings_content');settings.setWidget(settings_content)
        right=QVBoxLayout(settings_content);right.setContentsMargins(14,14,14,14);right.setSpacing(8)
        right.addWidget(text('Estacionamento','section_title'))
        self.name_edit=QLineEdit();self.name_edit.setMaxLength(80);self.name_edit.setPlaceholderText('Ex.: Estacionamento do campus')
        self.name_edit.setAccessibleName('Nome do estacionamento');self.name_edit.textChanged.connect(self._edited)
        right.addWidget(self.name_edit)
        self.count_label=text('Nenhuma vaga marcada','small');right.addWidget(self.count_label)
        self.space_list=QListWidget();self.space_list.setObjectName('editor_spaces')
        self.space_list.setMinimumHeight(90)
        self.space_list.setAccessibleName('Vagas cadastradas no vídeo')
        self.space_list.currentItemChanged.connect(self._list_selected);right.addWidget(self.space_list,1)
        self.delete_button=QPushButton('Excluir vaga selecionada');self.delete_button.clicked.connect(self.canvas.delete_selected)
        right.addWidget(self.delete_button)
        self.tuning_button=QPushButton('Ajustar detecção');self.tuning_button.setCheckable(True)
        right.addWidget(self.tuning_button)
        self.tuning=QWidget();tuning_layout=QVBoxLayout(self.tuning);tuning_layout.setContentsMargins(0,0,0,0)
        form=QFormLayout();self.free_spin=QDoubleSpinBox();self.occupied_spin=QDoubleSpinBox()
        for spin in [self.free_spin,self.occupied_spin]:
            spin.setRange(0,100);spin.setDecimals(1);spin.setSuffix(' %');spin.setSingleStep(.5)
            spin.valueChanged.connect(self._edited)
        self.free_spin.setValue(11);self.occupied_spin.setValue(12)
        self.free_spin.setAccessibleName('Limiar geral de vaga livre em percentual de textura')
        self.occupied_spin.setAccessibleName('Limiar geral de vaga ocupada em percentual de textura')
        form.addRow('Livre até',self.free_spin);form.addRow('Ocupada desde',self.occupied_spin);tuning_layout.addLayout(form)
        tuning_layout.addWidget(text('Limiares gerais de textura. Confira vagas vazias e ocupadas em vários instantes. Ajustes locais da demonstração são preservados.','small'))
        right.addWidget(self.tuning);self.tuning.hide();self.tuning_button.toggled.connect(self.tuning.setVisible)
        self.preview_button=QPushButton('Conferir neste quadro');self.preview_button.clicked.connect(self.preview)
        right.addWidget(self.preview_button)
        self.preview_label=text('A conferência vale só para o quadro escolhido.','small');right.addWidget(self.preview_label)
        body.addWidget(settings);layout.addLayout(body,1)
        self.message=text('Comece em Adicionar vídeo ou escolha um perfil salvo.','notice');layout.addWidget(self.message)
        actions=QHBoxLayout()
        self.back_button=QPushButton('Voltar');self.back_button.clicked.connect(self.back_requested.emit)
        actions.addWidget(self.back_button);actions.addWidget(text('Voltar mantém o rascunho nesta sessão.','small'),1)
        self.save_button=QPushButton('Salvar e analisar');self.save_button.setProperty('role','primary')
        self.save_button.clicked.connect(self.save_profile)
        actions.addWidget(self.save_button);layout.addLayout(actions)
        self._loading=False;self._dirty=False;self._refresh_controls()
        if self.store.errors:self.message.setText('Alguns perfis não puderam ser abertos. Adicione o vídeo novamente para cadastrá-lo.')
        if profile:
            index=next((i for i in range(self.profile_combo.count()) if getattr(self.profile_combo.itemData(i),'id',None)==profile.id),0)
            if index==0:
                self.profile_combo.addItem(profile.name,profile);index=self.profile_combo.count()-1
            self.profile_combo.setCurrentIndex(index)

    def _populate_profiles(self,identity=None):
        blocker=QSignalBlocker(self.profile_combo);self.profile_combo.clear()
        self.profile_combo.addItem('Novo estacionamento',None)
        self.profile_combo.addItem('Demonstração · criar uma cópia','demo')
        selected=0
        for profile in self.store.list():
            self.profile_combo.addItem(profile.name,profile)
            if profile.id==identity:selected=self.profile_combo.count()-1
        self.profile_combo.setCurrentIndex(selected);self._combo_index=selected;del blocker

    def set_tool(self,tool):
        self.canvas.set_tool(tool)
        self.hint.setText({'rectangle':'Retângulo: clique e arraste sobre uma vaga.',
            'polygon':'4 pontos: clique nos cantos em sequência, contornando a vaga.',
            'select':'Selecione uma vaga. Arraste o interior para mover ou os cantos para ajustar.'}[tool])

    def message_from_canvas(self,value):self.message.setText(value)

    def _discard(self):
        if not self._dirty:return True
        return QMessageBox.question(self,'Descartar alterações?','Há alterações não salvas neste mapa. Deseja descartá-las?',
            QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)==QMessageBox.StandardButton.Discard

    def _choose_profile(self,index):
        if index<0:return
        if not self._discard():
            blocker=QSignalBlocker(self.profile_combo);self.profile_combo.setCurrentIndex(self._combo_index);del blocker;return
        previous=self._combo_index
        item=self.profile_combo.itemData(index)
        try:
            if item=='demo':
                data=self.root/'dados/terceiros'
                self._load_video(data/'carPark.mp4',json.loads((data/'vagas_completas_carpark.json').read_text(encoding='utf-8')),'Cópia da demonstração')
            elif item:
                item.validate_source()
                self._load_video(item.source,json.loads(item.config.read_text(encoding='utf-8')),item.name,item)
            else:self._reset()
            self._combo_index=index
        except (OSError,ValueError,KeyError,TypeError) as error:
            blocker=QSignalBlocker(self.profile_combo);self.profile_combo.setCurrentIndex(previous);del blocker
            self.message.setText(str(error))

    def _reset(self):
        self._loading=True;self.video_info=None;self.profile=None;self.frame=None
        self.canvas.spaces=[];self.canvas._undo=[];self.canvas._redo=[];self.canvas._preview=[]
        self.canvas._cancel_drag();self.canvas.select(None)
        self.canvas.clear('Adicione um vídeo para começar','Use uma gravação com a câmera parada.')
        self.name_edit.clear();self.space_list.clear();self.count_label.setText('Nenhuma vaga marcada')
        self._dirty=False;self._loading=False;self._refresh_controls()

    def choose_video(self):
        filename,_=QFileDialog.getOpenFileName(self,'Adicionar vídeo de estacionamento','',
            'Vídeos (*.mp4 *.avi *.mov *.mkv *.m4v);;Todos os arquivos (*)')
        if filename and self._discard():self.import_video(filename)

    def import_video(self,source):
        try:
            self._load_video(source,None,Path(source).stem)
            blocker=QSignalBlocker(self.profile_combo);self.profile_combo.setCurrentIndex(0);del blocker
            self._combo_index=0;self._dirty=True
        except (OSError,ValueError,KeyError) as error:self.message.setText(str(error))

    def _load_video(self,source,config,name,profile=None):
        info=probe_video(source)
        config=deepcopy(config) if config else {'width':info.width,'height':info.height,'method':'texture',
            'texture_block_size':25,'texture_constant':16,'analysis_inset':1,'stable_frames':5,
            'free_ratio':.11,'occupied_ratio':.12,'spaces':[]}
        if config['spaces']:Detector(info.frame,config)
        self._loading=True;self.profile=profile;self.video_info=info;self.frame=info.frame;self.config=config
        self.name_edit.setText(name);self.free_spin.setValue(config.get('free_ratio',.11)*100)
        self.occupied_spin.setValue(config.get('occupied_ratio',.12)*100)
        self.canvas.set_map(info.frame,config['spaces'])
        blocker=QSignalBlocker(self.frame_slider);self.frame_slider.setRange(0,info.frame_count-1);self.frame_slider.setValue(0);del blocker
        self.frame_label.setText(f'Quadro 0 / {info.frame_count-1}')
        self.video_label.setText(f'{info.source.name} · {info.width} × {info.height} · {info.fps:g} FPS. Mantenha o vídeo na pasta original.')
        self.message.setText('Marque somente as vagas. Para outro enquadramento, faça um novo mapa.')
        self._loading=False;self._dirty=False;self._refresh_controls()

    def seek_frame(self,index):
        if not self.video_info:return
        capture=cv2.VideoCapture(str(self.video_info.source))
        try:
            if not capture.set(cv2.CAP_PROP_POS_FRAMES,index):raise ValueError('Este vídeo não permite buscar esse instante.')
            ok,frame=capture.read()
            if not ok:raise ValueError('Não foi possível ler este quadro. Escolha outro instante.')
            self.canvas._cancel_drag();spaces=self.canvas.spaces
            self.frame=frame;self.canvas.set_frame(frame,[],[]);self.canvas.spaces=spaces
            self.canvas._preview=[];self.canvas.update()
            self.frame_label.setText(f'Quadro {index} / {self.video_info.frame_count-1}')
            self.preview_label.setText('Confira novamente após mudar o quadro.')
        except ValueError as error:self.message.setText(str(error))
        finally:capture.release()

    def _map_changed(self):
        blocker=QSignalBlocker(self.space_list);self.space_list.clear()
        for space in self.canvas.spaces:
            item=QListWidgetItem(space['id']);item.setData(Qt.ItemDataRole.UserRole,deepcopy(space));self.space_list.addItem(item)
        del blocker
        self.count_label.setText(f'{len(self.canvas.spaces)} vagas marcadas')
        self._selected(self.canvas.selected_space or '')
        self._edited()

    def _selected(self,name):
        blocker=QSignalBlocker(self.space_list)
        for i in range(self.space_list.count()):
            item=self.space_list.item(i)
            if item.text()==name:self.space_list.setCurrentItem(item);break
        if not name:self.space_list.setCurrentRow(-1)
        del blocker;self.delete_button.setEnabled(bool(name))

    def _list_selected(self,current,previous):self.canvas.select(current.text() if current else None)

    def _edited(self,*args):
        if not self._loading:self._dirty=True
        self.canvas._preview=[];self.canvas.update();self._refresh_controls()

    def _refresh_controls(self):
        if not hasattr(self,'save_button'):return
        has_video=self.video_info is not None
        valid=has_video and bool(self.canvas.spaces) and bool(self.name_edit.text().strip()) and self.free_spin.value()<self.occupied_spin.value()
        self.save_button.setEnabled(valid);self.preview_button.setEnabled(valid)
        self.save_button.setText('Abrir análise' if self.profile and not self._dirty else 'Salvar e analisar')
        self.frame_slider.setEnabled(has_video)
        self.delete_button.setEnabled(bool(self.canvas.selected_space))
        self.undo_button.setEnabled(bool(self.canvas._undo));self.redo_button.setEnabled(bool(self.canvas._redo))

    def current_config(self):
        config=deepcopy(self.config);config['spaces']=deepcopy(self.canvas.spaces)
        config['free_ratio']=self.free_spin.value()/100;config['occupied_ratio']=self.occupied_spin.value()/100
        ids={s['id'] for s in config['spaces']}
        if 'ambiguous_groups' in config:
            config['ambiguous_groups']=[g for g in config['ambiguous_groups'] if set(g['spaces'])<=ids]
        return config

    def preview(self):
        try:
            results=Detector(self.frame,self.current_config()).process(self.frame,instant=True)
            self.canvas._preview=results;self.canvas.update()
            self.preview_label.setText(f"Livre: {sum(r['state']=='livre' for r in results)} · Ocupada: {sum(r['state']=='ocupada' for r in results)} · Em análise: {sum(r['state']=='indefinida' for r in results)}")
            self.message.setText('Conferência de um quadro, sem confirmação temporal. Compare com a imagem antes de salvar.')
        except (ValueError,KeyError,TypeError) as error:self.message.setText(f'Confira as marcações: {error}')

    def save_profile(self):
        if not self.save_button.isEnabled():return
        try:
            if self.profile and not self._dirty:
                self.profile.validate_source();self.saved_profile=self.profile
            else:
                self.saved_profile=self.store.save(self.name_edit.text(),self.video_info,self.current_config(),existing=self.profile,frame=self.frame)
            self.profile=self.saved_profile;self._dirty=False
            self._populate_profiles(self.profile.id);self._refresh_controls()
            self.profile_saved.emit(self.saved_profile)
        except (OSError,ValueError,KeyError,TypeError) as error:self.message.setText(f'Não foi possível salvar: {error}')
