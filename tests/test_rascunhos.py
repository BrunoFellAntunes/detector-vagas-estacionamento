"""Contrato de persistência local, sem interface nem leitura do vídeo."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rascunhos import DraftStore


class DraftStoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.directory = self.root / 'perfis' / 'rascunhos'
        self.store = DraftStore(self.directory)
        self.active = self.directory / 'rascunho.json'
        self.draft = {
            'version': 1, 'name': 'Pátio da São João',
            'source': str(self.root / 'vídeos' / 'gravação.avi'),
            'width': 320, 'height': 180, 'frame_index': 7,
            'config': {'width': 320, 'height': 180, 'method': 'texture',
                       'free_ratio': .11, 'occupied_ratio': .12,
                       'stable_frames': 5, 'analysis_inset': 1,
                       'spaces': [{'id': 'V01', 'sector': 'Pátio',
                                   'points': [[10, 10], [100, 10], [100, 90], [10, 90]]}]},
        }

    def test_missing_draft_returns_none_without_creating_directory(self):
        self.assertIsNone(self.store.load())
        self.assertIsNone(self.store.archive())
        self.assertFalse(self.directory.exists())

    def test_first_save_round_trip_utf8_and_no_input_mutation(self):
        original = deepcopy(self.draft)
        self.store.save(self.draft)
        self.assertEqual(DraftStore(str(self.directory)).load(), original)
        self.assertIn('São João', self.active.read_bytes().decode('utf-8'))
        self.assertIn('gravação.avi', self.active.read_text(encoding='utf-8'))
        self.assertEqual(self.draft, original)
        self.assertFalse((self.root / 'vídeos').exists())

    def test_second_save_replaces_active_and_reopens_latest(self):
        self.store.save(self.draft)
        self.draft['frame_index'] = 9
        self.draft['name'] = 'Outra edição'
        self.store.save(self.draft)
        self.assertEqual(self.store.load(), self.draft)
        self.assertEqual(list(self.directory.iterdir()), [self.active])

    def test_empty_map_and_unfinished_name_are_recoverable(self):
        self.draft['config']['spaces'] = []
        self.draft['name'] = ''
        self.store.save(self.draft)
        self.assertEqual(self.store.load(), self.draft)

    def test_optional_profile_id_is_preserved(self):
        for identity in [None, 'f9bb9ec2-9af5-4f71-9957-574e2be0ea86']:
            with self.subTest(identity=identity):
                self.draft['source_profile_id'] = identity
                self.store.save(self.draft)
                self.assertEqual(self.store.load(), self.draft)

    def test_existing_complete_demo_map_is_preserved(self):
        config = json.loads((ROOT / 'dados/terceiros/vagas_completas_carpark.json').read_text(encoding='utf-8'))
        self.draft.update(width=config['width'], height=config['height'], config=config)
        self.store.save(self.draft)
        self.assertEqual(self.store.load(), self.draft)

    def test_temporary_is_in_same_directory_and_complete_before_replacement(self):
        self.store.save(self.draft)
        before = self.active.read_bytes()
        self.draft['name'] = 'Atualização'
        import os
        replace = os.replace

        def inspect_then_replace(source, destination):
            self.assertEqual(Path(source).parent, self.directory)
            self.assertNotEqual(Path(source), self.active)
            self.assertEqual(Path(destination), self.active)
            self.assertEqual(self.active.read_bytes(), before)
            self.assertEqual(json.loads(Path(source).read_text(encoding='utf-8')), self.draft)
            replace(source, destination)

        with patch('app.rascunhos.os.replace', side_effect=inspect_then_replace):
            self.store.save(self.draft)
        self.assertEqual(self.store.load(), self.draft)

    def test_invalid_fields_are_rejected_before_replacing_previous(self):
        self.store.save(self.draft)
        previous = self.active.read_bytes()
        changes = [('version', 2), ('version', True), ('name', 'x' * 81),
                   ('name', None), ('source', ''), ('source', 'a\x00b'),
                   ('width', 0), ('width', True), ('height', -1),
                   ('frame_index', -1), ('frame_index', 1.5),
                   ('source_profile_id', '../perfil'), ('config', [])]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                invalid = deepcopy(self.draft)
                invalid[key] = value
                with self.assertRaisesRegex(ValueError, key):
                    self.store.save(invalid)
                self.assertEqual(self.active.read_bytes(), previous)
        for value in [[], None, {}, {'version': 1}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.save(value)

    def test_invalid_map_limits_and_types_are_rejected(self):
        changes = [('width', 321), ('height', True), ('method', 'reference'),
                   ('spaces', {}), ('free_ratio', .2), ('occupied_ratio', 2),
                   ('free_ratio', float('nan')), ('stable_frames', 0),
                   ('stable_frames', True), ('analysis_inset', 21),
                   ('texture_block_size', 4), ('texture_constant', float('inf')),
                   ('pixel_threshold', 255)]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                invalid = deepcopy(self.draft)
                invalid['config'][key] = value
                with self.assertRaisesRegex(ValueError, 'config'):
                    self.store.save(invalid)

    def test_invalid_polygons_and_duplicate_ids_are_rejected(self):
        polygons = [[], [[0, 0], [10, 10]],
                    [[-1, 0], [10, 0], [10, 10]],
                    [[0, 0], [320, 0], [0, 10]],
                    [[0, 0], [10, 0], [0, 180]],
                    [[0, 0], [1, 0], [0, 1]],
                    [[0, 0], [10, 10], [10, 0], [0, 10]],
                    [[0, 0], [10, 0], [5, 2], [10, 10], [0, 10]],
                    [[0.5, 0], [10, 0], [0, 10]],
                    [[True, 0], [10, 0], [0, 10]]]
        for points in polygons:
            with self.subTest(points=points):
                invalid = deepcopy(self.draft)
                invalid['config']['spaces'][0]['points'] = points
                with self.assertRaisesRegex(ValueError, 'points'):
                    self.store.save(invalid)
        invalid = deepcopy(self.draft)
        invalid['config']['spaces'] *= 2
        with self.assertRaisesRegex(ValueError, 'id'):
            self.store.save(invalid)
        invalid['config']['spaces'] = [None]
        with self.assertRaises(ValueError):
            self.store.save(invalid)

    def test_clockwise_polygon_and_local_thresholds_round_trip(self):
        self.draft['config']['spaces'][0]['points'].reverse()
        self.draft['config']['spaces'][0].update(free_ratio=.05, occupied_ratio=.08)
        self.store.save(self.draft)
        self.assertEqual(self.store.load(), self.draft)
        self.draft['config']['spaces'][0]['occupied_ratio'] = .01
        with self.assertRaisesRegex(ValueError, 'ratio'):
            self.store.save(self.draft)

    def test_ambiguity_groups_and_extra_map_metadata_are_preserved(self):
        second = deepcopy(self.draft['config']['spaces'][0])
        second['id'] = 'V02'
        self.draft['config']['spaces'].append(second)
        self.draft['config']['ambiguous_groups'] = [
            {'spaces': ['V01', 'V02'], 'reason': 'Veículo entre vagas',
             'brightness_threshold': 180, 'min_region_ratio': .08}]
        self.store.save(self.draft)
        self.assertEqual(self.store.load(), self.draft)
        for members in [['V01', 'ausente'], ['V01', 'V01'], []]:
            self.draft['config']['ambiguous_groups'][0]['spaces'] = members
            with self.subTest(members=members), self.assertRaises(ValueError):
                self.store.save(self.draft)

    def test_corrupted_unknown_version_and_invalid_utf8_remain_untouched(self):
        self.directory.mkdir(parents=True)
        invalid = deepcopy(self.draft)
        invalid['width'] = 0
        cases = [(b'{incompleto', 'JSON'), (b'\xff', 'UTF-8'),
                 (b'{"version":99}', 'version'), (b'[]', 'objeto'),
                 (json.dumps(invalid).encode(), 'width'),
                 (b'{"version":1,"version":2}', 'duplicad'),
                 (b'{"version":NaN}', 'JSON')]
        for content, message in cases:
            with self.subTest(content=content):
                self.active.write_bytes(content)
                with self.assertRaisesRegex(ValueError, message):
                    self.store.load()
                self.assertEqual(self.active.read_bytes(), content)

    def test_archive_removes_active_preserves_bytes_and_profile_revisions(self):
        profile = self.directory.parent / 'perfil-existente' / 'revisoes' / 'antiga'
        profile.mkdir(parents=True)
        revision = profile / 'mapa.json'
        revision.write_bytes(b'perfil original')
        self.store.save(self.draft)
        previous = self.active.read_bytes()
        archived = self.store.archive()
        self.assertIsInstance(archived, Path)
        self.assertEqual(archived.parent, self.directory / 'arquivados')
        self.assertEqual(archived.read_bytes(), previous)
        self.assertIsNone(self.store.load())
        self.assertEqual(revision.read_bytes(), b'perfil original')
        self.store.save(self.draft)
        another = self.store.archive()
        self.assertNotEqual(another, archived)
        self.assertEqual(archived.read_bytes(), previous)
        self.assertIsNone(self.store.archive())
        # Recuperação manual: copiar os bytes de volta ao caminho ativo.
        self.active.write_bytes(archived.read_bytes())
        self.assertEqual(self.store.load(), self.draft)

    def test_archive_can_preserve_a_corrupted_draft_for_manual_recovery(self):
        self.directory.mkdir(parents=True)
        self.active.write_bytes(b'JSON quebrado')
        archived = self.store.archive()
        self.assertEqual(archived.read_bytes(), b'JSON quebrado')
        self.assertIsNone(self.store.load())

    def test_failed_replacement_keeps_previous_and_removes_temporary(self):
        self.store.save(self.draft)
        before = self.active.read_bytes()
        self.draft['name'] = 'Novo'
        with patch('app.rascunhos.os.replace', side_effect=OSError('disco')):
            with self.assertRaisesRegex(OSError, 'salvar'):
                self.store.save(self.draft)
        self.assertEqual(self.active.read_bytes(), before)
        self.assertEqual(self.store.load()['name'], 'Pátio da São João')
        self.assertEqual(list(self.directory.iterdir()), [self.active])

    def test_partial_write_failure_keeps_previous_readable(self):
        self.store.save(self.draft)
        before = self.active.read_bytes()

        def fail_after_partial_write(data, stream, **kwargs):
            stream.write('{"version":')
            raise OSError('sem espaço')

        with patch('app.rascunhos.json.dump', side_effect=fail_after_partial_write):
            with self.assertRaisesRegex(OSError, 'salvar'):
                self.store.save(self.draft)
        self.assertEqual(self.active.read_bytes(), before)
        self.assertEqual(self.store.load(), self.draft)
        self.assertEqual(list(self.directory.iterdir()), [self.active])

    def test_fsync_failure_keeps_previous_readable(self):
        self.store.save(self.draft)
        with patch('app.rascunhos.os.fsync', side_effect=OSError('falha')):
            with self.assertRaisesRegex(OSError, 'salvar'):
                self.store.save(self.draft)
        self.assertEqual(self.store.load(), self.draft)

    def test_failed_first_save_leaves_no_active_draft(self):
        with patch('app.rascunhos.os.replace', side_effect=OSError('falha')):
            with self.assertRaises(OSError):
                self.store.save(self.draft)
        self.assertIsNone(self.store.load())
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_archive_failure_keeps_active_and_cleans_reservation(self):
        self.store.save(self.draft)
        with patch('app.rascunhos.os.replace', side_effect=OSError('falha')):
            with self.assertRaisesRegex(OSError, 'arquivar'):
                self.store.archive()
        self.assertEqual(self.store.load(), self.draft)
        self.assertEqual(list((self.directory / 'arquivados').iterdir()), [])

    def test_io_errors_are_distinct_from_missing_file(self):
        self.directory.mkdir(parents=True)
        self.active.mkdir()
        with self.assertRaisesRegex(OSError, 'ler'):
            self.store.load()

    def test_non_json_values_do_not_replace_previous(self):
        self.store.save(self.draft)
        previous = self.active.read_bytes()
        for value in [{1, 2}, float('nan'), (1, 2), {1: 'chave numérica'}]:
            with self.subTest(value=value):
                invalid = deepcopy(self.draft)
                invalid['config']['metadata'] = value
                with self.assertRaises(ValueError):
                    self.store.save(invalid)
                self.assertEqual(self.active.read_bytes(), previous)


if __name__ == '__main__':
    unittest.main()
