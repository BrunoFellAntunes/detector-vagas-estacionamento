"""Duplicação de regiões do mapa, independente da interface e do detector."""
from copy import deepcopy
import re


def duplicate_spaces(spaces, selected_id, dx, dy, copies, width, height):
    """Retorna uma cópia profunda do mapa acrescida das regiões deslocadas.

    Recebe regiões cadastradas com ``id`` e ``points`` em pixels da imagem.
    Cada nova região preserva os campos da origem, exceto id, points, setor
    e linha. Argumentos inválidos ou qualquer cópia fora da imagem produzem
    ValueError, sem alterar a entrada. Veja docs/DUPLICACAO.md.
    """
    for name, value in (('dx', dx), ('dy', dy), ('copies', copies),
                        ('width', width), ('height', height)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f'{name} deve ser um inteiro, sem booleanos.')
    if width <= 0 or height <= 0:
        raise ValueError('As dimensões da imagem devem ser positivas.')
    if not 1 <= copies <= 50:
        raise ValueError('A quantidade deve estar entre 1 e 50 cópias.')
    if dx == 0 and dy == 0:
        raise ValueError('O deslocamento não pode ser nulo: altere dx ou dy.')

    selected = next((space for space in spaces if space['id'] == selected_id), None)
    if selected is None:
        raise ValueError(f'A vaga selecionada {selected_id!r} não existe no mapa.')

    numbers = [int(space['id'][1:]) for space in spaces
               if re.fullmatch(r'V[0-9]+', space['id'])]
    next_number = max(numbers, default=0) + 1
    additions = []
    for index in range(1, copies + 1):
        points = [[x + index * dx, y + index * dy] for x, y in selected['points']]
        if any(not (0 <= x < width and 0 <= y < height) for x, y in points):
            raise ValueError(
                f'A cópia {index} sairia da imagem ({width} × {height}); '
                'nenhuma cópia foi criada.'
            )
        duplicate = deepcopy(selected)
        duplicate['id'] = f'V{next_number:02d}'
        duplicate['points'] = points
        duplicate.pop('setor', None)
        duplicate.pop('linha', None)
        additions.append(duplicate)
        next_number += 1

    return deepcopy(spaces) + additions
