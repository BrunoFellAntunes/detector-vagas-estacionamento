"""Compara estados por quadro e vaga com rótulos fornecidos em CSV."""
import argparse
import csv
import json
from pathlib import Path


def read_states(path, allowed):
    records={}
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if not {'quadro','vaga','estado'} <= set(reader.fieldnames or []):
            raise ValueError(f'CSV sem colunas quadro, vaga e estado: {path}')
        for line,row in enumerate(reader,start=2):
            try:
                frame=int(row['quadro'])
            except (ValueError,TypeError):
                raise ValueError(f'Índice de quadro inválido na linha {line}: {path}') from None
            space=(row['vaga'] or '').strip()
            state=(row['estado'] or '').strip()
            key=(frame,space)
            if frame<0 or not space or state not in allowed or key in records:
                raise ValueError(f'Registro inválido ou duplicado na linha {line}: {path}')
            records[key]=state
    if not records:
        raise ValueError(f'CSV sem registros: {path}')
    return records


def evaluate(predictions_path,labels_path):
    predictions=read_states(predictions_path,{'livre','ocupada','indefinida'})
    labels=read_states(labels_path,{'livre','ocupada'})
    matrix={'VP':0,'VN':0,'FP':0,'FN':0}
    unknown=correct=0
    for key,expected in labels.items():
        if key not in predictions:
            raise ValueError(f'Predição ausente para quadro {key[0]}, vaga {key[1]}.')
        actual=predictions[key]
        if actual=='indefinida':
            unknown+=1
            continue
        if actual==expected:
            correct+=1
            matrix['VP' if expected=='ocupada' else 'VN']+=1
        else:
            matrix['FP' if actual=='ocupada' else 'FN']+=1
    total=len(labels)
    defined=total-unknown
    tp,fp,fn=matrix['VP'],matrix['FP'],matrix['FN']
    return {
        'amostras':total,'definidas':defined,'indefinidas':unknown,
        'cobertura':defined/total,'concordancia_total':correct/total,
        'acuracia_definidas':correct/defined if defined else None,
        'matriz_confusao':matrix,
        'precisao_ocupada':tp/(tp+fp) if tp+fp else None,
        'revocacao_ocupada':tp/(tp+fn) if tp+fn else None,
        'f1_ocupada':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
        'nota':'Matriz, precisao, revocacao e F1 consideram somente decisoes definidas. '
               'Concordancia total inclui indefinidas no denominador. '
               'Os resultados descrevem apenas os rotulos fornecidos.'
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--predicoes',required=True)
    p.add_argument('--rotulos',required=True)
    p.add_argument('--output',default='resultados/avaliacao.json')
    args=p.parse_args()
    try:
        result=evaluate(args.predicoes,args.rotulos)
        target=Path(args.output)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as error:
        p.exit(1,f'Erro: {error}\n')


if __name__=='__main__':
    main()
