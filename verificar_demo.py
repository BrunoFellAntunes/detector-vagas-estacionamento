"""Reproduz a conferência da saída simulada contra seu gabarito independente."""
import csv
import json
from pathlib import Path
import cv2

root = Path(__file__).resolve().parent
truth = json.loads((root/'dados/gabarito_simulado.json').read_text(encoding='utf-8'))
with (root/'resultados/video/ocupacao.csv').open(encoding='utf-8') as stream:
    rows = list(csv.DictReader(stream))
if len(rows) != 1440:
    raise SystemExit(f'Esperadas 1440 decisões; encontradas {len(rows)}.')
errors = []
seen = set()
for row in rows:
    number = int(row['quadro'])
    key = (number, row['vaga'])
    if key in seen or not 0 <= number < 240 or row['vaga'] not in {f'V{i:02}' for i in range(1,7)}:
        raise SystemExit('Registro duplicado, quadro ou vaga inválida.')
    seen.add(key)
    expected = 'ocupada' if row['vaga'] in truth[number]['ocupadas'] else 'livre'
    if row['estado'] != expected:
        errors.append((number, row['vaga'], row['estado'], expected))
warmup = sum(state == 'indefinida' for _, _, state, _ in errors)
transitions = len(errors) - warmup
if warmup != 24 or transitions != 8:
    raise SystemExit(f'Resultado diferente do esperado: {warmup} indefinidas e {transitions} divergentes.')
if any(n not in set(range(4)) | set(range(80,84)) | set(range(160,164)) for n, *_ in errors):
    raise SystemExit('Há divergências fora dos intervalos previstos de confirmação temporal.')
cap = cv2.VideoCapture(str(root/'resultados/video/video_anotado.mp4'))
count = 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    count += 1
cap.release()
if count != 240:
    raise SystemExit(f'Vídeo de saída incompleto: {count} quadros.')
summary = {'quadros': count, 'vagas': 6, 'decisoes': len(rows), 'concordantes': len(rows)-len(errors),
           'divergentes_ou_indefinidas': len(errors), 'aquecimento_indefinidas': warmup,
           'transicoes_com_atraso': transitions, 'concordancia_simulada': round((len(rows)-len(errors))/len(rows),6),
           'teste_em_campo': False}
(root/'resultados/verificacao_demo.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
