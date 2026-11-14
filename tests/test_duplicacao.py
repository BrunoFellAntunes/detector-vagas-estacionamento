"""Contrato da duplicação, sem dependência de Qt ou OpenCV."""
from copy import deepcopy
import unittest

from app.duplicacao import duplicate_spaces


class DuplicateSpacesTests(unittest.TestCase):
    def setUp(self):
        self.spaces = [{
            'id': 'V01', 'points': [[10, 10], [20, 12], [18, 20], [10, 18]],
            'setor': 'A', 'linha': 2, 'free_ratio': .05, 'occupied_ratio': .065,
            'metadata': {'tags': ['manual']},
        }]

    def duplicate(self, **kwargs):
        args = dict(selected_id='V01', dx=25, dy=2, copies=1, width=200, height=100)
        args.update(kwargs)
        return duplicate_spaces(self.spaces, **args)

    def test_one_copy_preserves_geometry_thresholds_and_clears_logical_position(self):
        result = self.duplicate()
        self.assertEqual(result[0], self.spaces[0])
        self.assertEqual(result[1], {
            'id': 'V02', 'points': [[35, 12], [45, 14], [43, 22], [35, 20]],
            'free_ratio': .05, 'occupied_ratio': .065,
            'metadata': {'tags': ['manual']},
        })

    def test_multiple_copies_use_original_as_origin(self):
        result = self.duplicate(copies=3)
        self.assertEqual([s['id'] for s in result], ['V01', 'V02', 'V03', 'V04'])
        for index, space in enumerate(result[1:], 1):
            self.assertEqual(space['points'], [[x+25*index, y+2*index]
                                             for x, y in self.spaces[0]['points']])

    def test_ids_with_gaps_padding_and_more_than_two_digits(self):
        for identifiers, expected in [
            (['V01', 'V09', 'V03'], ['V10', 'V11']),
            (['V01', 'V099', 'V100'], ['V101', 'V102']),
            (['V01', 'V0008', 'custom', 'V9x', 'v999'], ['V09', 'V10']),
            (['custom'], ['V01', 'V02']),
        ]:
            with self.subTest(identifiers=identifiers):
                spaces = [dict(deepcopy(self.spaces[0]), id=name) for name in identifiers]
                result = duplicate_spaces(spaces, identifiers[0], 1, 0, 2, 100, 100)
                self.assertEqual(result[:len(spaces)], spaces)
                self.assertEqual([s['id'] for s in result[len(spaces):]], expected)
                self.assertEqual(len({s['id'] for s in result}), len(result))

    def test_repeated_calls_do_not_collide(self):
        first = self.duplicate()
        second = duplicate_spaces(first, 'V02', 25, 0, 2, 200, 100)
        self.assertEqual([s['id'] for s in second], ['V01', 'V02', 'V03', 'V04'])
        self.assertEqual(second[2]['points'], [[60, 12], [70, 14], [68, 22], [60, 20]])

    def test_input_and_nested_data_are_independent(self):
        before = deepcopy(self.spaces)
        result = self.duplicate(copies=2)
        self.assertEqual(self.spaces, before)
        result[0]['points'][0][0] = 999
        result[0]['metadata']['tags'].append('original retornado')
        result[1]['points'][0][0] = 888
        result[1]['metadata']['tags'].append('cópia')
        self.assertEqual(self.spaces, before)
        self.assertEqual(result[2]['metadata'], before[0]['metadata'])
        self.assertEqual(result[2]['points'][0], [60, 14])
        self.spaces[0]['metadata']['tags'].append('entrada')
        self.assertEqual(result[2]['metadata']['tags'], ['manual'])

    def test_exact_edges_and_negative_offsets_are_allowed(self):
        result = self.duplicate(dx=-10, dy=-10, width=11, height=11)
        self.assertEqual(result[1]['points'], [[0, 0], [10, 2], [8, 10], [0, 8]])

    def test_each_edge_rejects_whole_operation_without_mutation(self):
        for dx, dy, width, height, copies in [
            (-11, 0, 100, 100, 1), (0, -11, 100, 100, 1),
            (80, 0, 100, 100, 1), (0, 80, 100, 100, 1),
            (25, 0, 70, 100, 2),
        ]:
            with self.subTest(dx=dx, dy=dy, copies=copies):
                before = deepcopy(self.spaces)
                with self.assertRaisesRegex(ValueError, 'cópia.*imagem'):
                    self.duplicate(dx=dx, dy=dy, width=width, height=height, copies=copies)
                self.assertEqual(self.spaces, before)

    def test_invalid_arguments(self):
        invalid = [{'selected_id': 'ausente'}, {'selected_id': None}, {'dx': 0, 'dy': 0}]
        for key in ('dx', 'dy', 'copies', 'width', 'height'):
            invalid.extend({key: value} for value in (True, False, 1.0, '1', None))
        for key in ('width', 'height'):
            invalid.extend({key: value} for value in (0, -1, float('inf'), float('nan')))
        invalid.extend({'copies': value} for value in (0, -1, 51))
        for args in invalid:
            with self.subTest(args=args):
                before = deepcopy(self.spaces)
                with self.assertRaises(ValueError):
                    self.duplicate(**args)
                self.assertEqual(self.spaces, before)

    def test_empty_map_has_no_selected_space(self):
        with self.assertRaisesRegex(ValueError, 'selecionada'):
            duplicate_spaces([], 'V01', 1, 0, 1, 100, 100)

    def test_fifty_copies_and_missing_optional_fields(self):
        self.spaces = [{'id': 'V01', 'points': [[0, 0], [2, 0], [2, 2], [0, 2]]}]
        result = self.duplicate(dx=3, dy=0, copies=50)
        self.assertEqual(len(result), 51)
        self.assertEqual(result[-1], {
            'id': 'V51', 'points': [[150, 0], [152, 0], [152, 2], [150, 2]],
        })


if __name__ == '__main__':
    unittest.main()
