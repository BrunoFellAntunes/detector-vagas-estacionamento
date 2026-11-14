"""Leitura e validação dos resultados usados pela interface de apresentação."""
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
import zipfile

STATES=('livre','ocupada','indefinida')
LABELS={'livre':'Livre','ocupada':'Ocupada','indefinida':'Em análise'}


@dataclass
class Session:
    source: Path
    output: Path
    width: int
    height: int
    fps: float
    spaces: list
    frames: list
    events: list
    summary: dict
    evaluation: dict

    @property
    def frame_count(self):
        return len(self.frames)

    def snapshot(self,index):
        if not 0<=index<self.frame_count:
            raise ValueError('Quadro fora da gravação.')
        return self.frames[index]

    def counts(self,index):
        snapshot=self.snapshot(index)
        return {state:sum(r['state']==state for r in snapshot) for state in STATES}

    def history(self,index):
        return [event for event in self.events if event['frame']<=index and event['previous']!='indefinida']

    def export(self,target):
        target=Path(target)
        if target.suffix.lower()!='.zip':
            raise ValueError('Escolha um arquivo ZIP para exportar os resultados.')
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_suffix('.zip.tmp')
        try:
            with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
                for name in ['ocupacao.csv','eventos.csv','resumo.json','avaliacao.json',
                             'ultimo_quadro.png','video_anotado.mp4']:
                    source=self.output/name
                    if source.is_file():archive.write(source,name)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


def load_session(root,output=None):
    root=Path(root)
    data=root/'dados/terceiros'
    output=Path(output) if output is not None else root/'resultados/carpark'
    config=json.loads((data/'vagas_carpark.json').read_text(encoding='utf-8'))
    metadata=json.loads((data/'carPark.metadata.json').read_text(encoding='utf-8'))
    summary=json.loads((output/'resumo.json').read_text(encoding='utf-8'))
    evaluation=json.loads((output/'avaliacao.json').read_text(encoding='utf-8'))
    count=metadata['quadros_decodificados']
    fps=float(summary['fps_informado_fonte'])
    spaces=config['spaces']
    ids=[space['id'] for space in spaces]
    if (not spaces or len(set(ids))!=len(ids) or not math.isfinite(fps) or fps<=0 or
            summary.get('interrompido_pelo_usuario') or summary['quadros_processados']!=count or
            summary['vagas_monitoradas']!=len(ids) or count<1):
        raise ValueError('A análise está incompleta ou não corresponde às vagas cadastradas. Reprocesse o vídeo.')
    if not (data/'carPark.mp4').is_file():
        raise ValueError('O vídeo do exemplo não está disponível.')
    frames=[{} for _ in range(count)]
    with (output/'ocupacao.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            index=int(row['quadro'])
            name=row['vaga']
            state=row['estado']
            ratio=float(row['fracao_alterada'])
            if (not 0<=index<count or name not in ids or state not in STATES or
                    not math.isfinite(ratio) or not 0<=ratio<=1 or name in frames[index]):
                raise ValueError('Registro de ocupação inválido, duplicado ou fora da gravação.')
            frames[index][name]={'id':name,'state':state,'ratio':ratio}
    if any(set(frame)!=set(ids) for frame in frames):
        raise ValueError('Existem quadros sem todas as vagas. Reprocesse o vídeo.')
    snapshots=[[frame[name] for name in ids] for frame in frames]
    events=[]
    with (output/'eventos.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            index=int(row['quadro'])
            name=row['vaga']
            if (not 0<=index<count or name not in ids or row['estado_anterior'] not in STATES or
                    row['estado_atual']!=frames[index][name]['state']):
                raise ValueError('Evento não corresponde à análise disponível.')
            events.append({'frame':index,'time':index/fps,'space':name,
                           'previous':row['estado_anterior'],'state':row['estado_atual']})
    events.sort(key=lambda item:item['frame'])
    return Session(data/'carPark.mp4',output,int(config['width']),int(config['height']),
                   fps,spaces,snapshots,events,summary,evaluation)
