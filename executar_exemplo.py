"""Executa e avalia o exemplo real com cinco vagas previamente cadastradas."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    root=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=root/'resultados/carpark')
    p.add_argument('--show',action='store_true',help='Abrir janela; espaço pausa, Q ou Esc encerra.')
    p.add_argument('--completo',action='store_true',help='Analisar o mapa completo por textura, sem referência vazia global.')
    args=p.parse_args()
    data=root/'dados/terceiros'
    config_name='vagas_completas_carpark.json' if args.completo else 'vagas_carpark.json'
    labels_name='rotulos_completos_carpark.csv' if args.completo else 'rotulos_carpark.csv'
    command=[sys.executable,str(root/'detector.py'),'--source',str(data/'carPark.mp4'),
             '--reference',str(data/'referencia_carpark.png'),'--config',str(data/config_name),
             '--output',str(args.output)]
    if args.show:command.append('--show')
    try:
        subprocess.run(command,check=True)
        # Uma execução interrompida não deve ser avaliada como se cobrisse o clipe completo.
        summary=json.loads((args.output/'resumo.json').read_text(encoding='utf-8'))
        if summary['interrompido_pelo_usuario']:
            print('Execução interrompida; avaliação da amostra completa não realizada.')
            return
        metadata=json.loads((data/'carPark.metadata.json').read_text(encoding='utf-8'))
        expected=metadata['quadros_decodificados']
        if summary['quadros_processados']!=expected:
            p.exit(1,f"Vídeo incompleto: {summary['quadros_processados']} quadros; esperados {expected}. "
                     'A avaliação não foi realizada.\n')
        subprocess.run([sys.executable,str(root/'avaliar.py'),'--predicoes',str(args.output/'ocupacao.csv'),
                        '--rotulos',str(data/labels_name),
                        '--output',str(args.output/'avaliacao.json')],check=True)
        print('Exemplo concluído. Resultados em',args.output.resolve())
    except subprocess.CalledProcessError as error:
        p.exit(error.returncode,'A execução não foi concluída. Consulte o erro acima.\n')


if __name__=='__main__':
    main()
