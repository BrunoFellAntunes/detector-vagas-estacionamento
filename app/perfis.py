"""Vídeos e mapas locais. Cada edição tem uma pasta de análise independente."""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from uuid import UUID,uuid4

import cv2

from detector import Detector,write_image


@dataclass
class VideoInfo:
    source: Path
    width: int
    height: int
    fps: float
    frame_count: int
    size: int
    modified: int
    frame: object


def probe_video(source):
    source=Path(source).resolve()
    if not source.is_file():raise ValueError('O vídeo não foi encontrado. Selecione o arquivo novamente.')
    capture=cv2.VideoCapture(str(source))
    try:
        ok,frame=capture.read()
        fps=float(capture.get(cv2.CAP_PROP_FPS))
        count=float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if not ok or not math.isfinite(fps) or fps<=0 or not math.isfinite(count) or count<1:
            raise ValueError('Não foi possível ler o vídeo, sua duração ou FPS. Tente um arquivo MP4 ou AVI válido.')
        height,width=frame.shape[:2]
        stat=source.stat()
        return VideoInfo(source,width,height,fps,int(count),stat.st_size,stat.st_mtime_ns,frame)
    finally:capture.release()


@dataclass(frozen=True)
class Profile:
    id: str
    name: str
    source: Path
    config: Path
    reference: Path
    output: Path
    width: int
    height: int
    fps: float
    frame_count: int
    size: int
    modified: int
    config_hash: str

    def validate_source(self):
        try:stat=self.source.stat()
        except OSError as error:
            raise ValueError('O vídeo deste perfil não foi encontrado. Adicione-o novamente em Vídeos e vagas.') from error
        if (stat.st_size,stat.st_mtime_ns)!=(self.size,self.modified):
            raise ValueError('O vídeo foi alterado. Adicione-o novamente e confira as marcações.')
        if not self.config.is_file() or hashlib.sha256(self.config.read_bytes()).hexdigest()!=self.config_hash:
            raise ValueError('O mapa do perfil foi alterado fora do editor. Cadastre-o novamente para analisar.')


class ProfileStore:
    def __init__(self,directory):
        self.directory=Path(directory)
        self.errors=[]

    def list(self):
        profiles=[];self.errors=[]
        for path in sorted(self.directory.glob('*/perfil.json')):
            try:profiles.append(self._load(path))
            except (OSError,ValueError,KeyError,TypeError) as error:self.errors.append(f'{path.parent.name}: {error}')
        return sorted(profiles,key=lambda profile:profile.name.casefold())

    def _load(self,path):
        data=json.loads(path.read_text(encoding='utf-8'))
        if data['version']!=1:raise ValueError('Versão de perfil não suportada.')
        identity=str(UUID(data['id']));revision=str(UUID(data['revision']))
        if identity!=path.parent.name:raise ValueError('Identificação de perfil inválida.')
        if (not data['name'].strip() or data['width']<1 or data['height']<1 or data['frame_count']<1 or
                not math.isfinite(data['fps']) or data['fps']<=0):raise ValueError('Metadados do vídeo inválidos.')
        folder=path.parent/'revisoes'/revision
        return Profile(identity,data['name'],Path(data['source']),folder/'mapa.json',folder/'referencia.png',
            folder/'resultados',data['width'],data['height'],data['fps'],data['frame_count'],
            data['size'],data['modified'],data['config_hash'])

    def save(self,name,video,config,existing=None,frame=None):
        name=name.strip()
        if not name or len(name)>80:raise ValueError('Dê um nome ao estacionamento, com até 80 caracteres.')
        if (video.width,video.height)!=(config['width'],config['height']):
            raise ValueError('A resolução do mapa difere do vídeo.')
        if config.get('method')!='texture':raise ValueError('O editor utiliza análise por textura.')
        reference=video.frame if frame is None else frame
        Detector(reference,config)
        stat=video.source.stat()
        if (stat.st_size,stat.st_mtime_ns)!=(video.size,video.modified):
            raise ValueError('O vídeo foi alterado durante o cadastro. Adicione-o novamente.')
        identity=existing.id if existing else str(uuid4())
        identity=str(UUID(identity));revision=str(uuid4())
        folder=self.directory/identity/'revisoes'/revision
        folder.mkdir(parents=True)
        encoded=(json.dumps(config,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        (folder/'mapa.json').write_bytes(encoded)
        write_image(folder/'referencia.png',reference)
        data={'version':1,'id':identity,'revision':revision,'name':name,'source':str(video.source),
            'width':video.width,'height':video.height,'fps':video.fps,'frame_count':video.frame_count,
            'size':video.size,'modified':video.modified,'config_hash':hashlib.sha256(encoded).hexdigest()}
        manifest=folder.parent.parent/'perfil.json'
        temporary=manifest.with_suffix('.json.tmp')
        try:
            temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            temporary.replace(manifest)
        finally:temporary.unlink(missing_ok=True)
        return self._load(manifest)
