"""Elementos visuais da janela de apresentação."""
import cv2
from PySide6.QtCore import Qt,QPointF,QRectF,Signal
from PySide6.QtGui import QColor,QFont,QIcon,QImage,QPainter,QPainterPath,QPen,QPixmap,QPolygonF
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget,QSizePolicy

COLORS={'livre':'#31b77b','ocupada':'#ed7168','indefinida':'#efbd54'}
LABELS={'livre':'Livre','ocupada':'Ocupada','indefinida':'Em análise'}

PATHS={
 'play':'<path d="m8 5 11 7-11 7z"/>',
 'pause':'<path d="M8 5v14M16 5v14"/>',
 'restart':'<path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/>',
 'expand':'<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',
 'shrink':'<path d="M3 8h5V3M21 8h-5V3M8 21v-5H3M16 21v-5h5"/>',
 'grid':'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
 'info':'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
 'download':'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
 'eye':'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
 'refresh':'<path d="M20 8a9 9 0 0 0-15-3L3 8m0-5v5h5M4 16a9 9 0 0 0 15 3l2-3m0 5v-5h-5"/>',
 'chevron':'<path d="m7 10 5 5 5-5"/>',
}


def icon(name,color='#3b4f67',size=20):
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</svg>'
    pixmap=QPixmap(size,size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pixmap)
    QSvgRenderer(svg.encode()).render(painter)
    painter.end()
    return QIcon(pixmap)


class VideoCanvas(QWidget):
    space_clicked=Signal(str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setObjectName('video_canvas')
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.setMinimumSize(360,220)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName('Vídeo do estacionamento com as vagas monitoradas')
        self.pixmap=None
        self.spaces=[]
        self.results=[]
        self.source_width=1100
        self.source_height=720
        self.selected_space=None
        self.show_overlays=True
        self.message='Preparando a demonstração'
        self.message_detail='A análise do vídeo será iniciada em instantes.'

    def set_frame(self,frame,spaces,results):
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        self.source_height,self.source_width=rgb.shape[:2]
        image=QImage(rgb.data,self.source_width,self.source_height,rgb.strides[0],QImage.Format.Format_RGB888)
        self.pixmap=QPixmap.fromImage(image.copy())
        self.spaces=spaces
        self.results=results
        self.update()

    def clear(self,title,detail=''):
        self.pixmap=None
        self.message=title
        self.message_detail=detail
        self.update()

    def image_rect(self):
        scale=min(self.width()/self.source_width,self.height()/self.source_height)
        width,height=self.source_width*scale,self.source_height*scale
        return QRectF((self.width()-width)/2,(self.height()-height)/2,width,height)

    def paintEvent(self,event):
        painter=QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area=QRectF(self.rect())
        path=QPainterPath()
        path.addRoundedRect(area,10,10)
        painter.setClipPath(path)
        painter.fillRect(area,QColor('#192e3e'))
        if self.pixmap is None:
            painter.setPen(QColor('#f3f7fc'))
            font=QFont('Sora');font.setPixelSize(21);font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.drawText(area.adjusted(22,-18,-22,-18),Qt.AlignmentFlag.AlignCenter,self.message)
            painter.setPen(QColor('#b5c9dc'))
            font=QFont('Manrope');font.setPixelSize(13);painter.setFont(font)
            painter.drawText(area.adjusted(22,45,-22,45),Qt.AlignmentFlag.AlignCenter,self.message_detail)
            return
        target=self.image_rect()
        painter.drawPixmap(target,self.pixmap,QRectF(self.pixmap.rect()))
        scale=target.width()/self.source_width
        compact=len(self.spaces)>12
        for space,result in zip(self.spaces,self.results) if self.show_overlays else []:
            selected=space['id']==self.selected_space
            points=QPolygonF([QPointF(target.x()+x*scale,target.y()+y*scale) for x,y in space['points']])
            color=QColor(COLORS[result['state']])
            fill=QColor(color);fill.setAlpha((24 if compact else 46) if not selected else 88)
            painter.setBrush(fill)
            painter.setPen(QPen(QColor('#ffffff') if selected else color,3 if selected else 2))
            painter.drawPolygon(points)
            font=QFont('Manrope');font.setPixelSize(10 if compact and not selected else 12);font.setWeight(QFont.Weight.Bold)
            painter.setFont(font)
            text=space['id'] if compact and not selected else f"{space['id']} · {LABELS[result['state']]}"
            metrics=painter.fontMetrics()
            width=metrics.horizontalAdvance(text)+14
            x=max(target.left()+3,min(points.boundingRect().left(),target.right()-width-3))
            y=points.boundingRect().top()+2 if compact and not selected else max(target.top()+3,points.boundingRect().top()-25)
            label=QRectF(x,y,width,16 if compact and not selected else 21)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor('#152a3b'))
            painter.drawRoundedRect(label,4,4)
            painter.setPen(color)
            painter.drawText(label,Qt.AlignmentFlag.AlignCenter,text)
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor('#6488f5'),3))
            painter.drawRoundedRect(area.adjusted(1,1,-1,-1),10,10)

    def focusInEvent(self,event):
        super().focusInEvent(event);self.update()

    def focusOutEvent(self,event):
        super().focusOutEvent(event);self.update()

    def hit_test(self,position):
        if self.pixmap is None:return None
        target=self.image_rect()
        if not target.contains(position):return None
        scale=target.width()/self.source_width
        point=((position.x()-target.x())/scale,(position.y()-target.y())/scale)
        import numpy as np
        for space in self.spaces:
            if cv2.pointPolygonTest(np.asarray(space['points'],dtype=np.int32),point,False)>=0:
                return space['id']
        return None

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            name=self.hit_test(event.position())
            if name:self.space_clicked.emit(name)
        super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.hit_test(event.position()) else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)
