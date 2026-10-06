import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from zerie_pack01_catalog import build_catalog, discover_characters, source_hashes


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / 'assets/vendor/zerie/pack01-full'


class ZeriePack01CatalogTests(unittest.TestCase):
    def test_discovers_all_roster_sources_from_the_pack(self):
        characters = discover_characters(ASSET_ROOT)

        self.assertEqual(len(characters), 22)
        self.assertEqual(len({character['id'] for character in characters}), 22)
        self.assertEqual([character['name'] for character in characters], sorted(
            (character['name'] for character in characters), key=str.casefold
        ))
        for character in characters:
            self.assertEqual(character['user_role'], '')
            self.assertTrue(character['actions'])
            self.assertTrue(character['shadow_variant']['present'])
            self.assertEqual(len(character['shadow_variant']['sheets']), len(character['sheets']))
            self.assertTrue(all(character['aseprite_sources'].values()))
            for sheet in character['sheets'] + character['shadow_variant']['sheets']:
                self.assertGreater(sheet['frame_count'], 0)
                self.assertEqual(sheet['frame_count'], sheet['frame_grid'][0] * sheet['frame_grid'][1])
                self.assertEqual(sheet['sheet_size'][0], sheet['frame_size'][0] * sheet['frame_grid'][0])
                self.assertEqual(sheet['sheet_size'][1], sheet['frame_size'][1] * sheet['frame_grid'][1])
                self.assertIsNotNone(sheet['alpha_visible_bounds'])
                with Image.open(ASSET_ROOT / sheet['source']) as source:
                    self.assertEqual(list(source.size), sheet['sheet_size'])
            self.assertTrue(all(not action.casefold().endswith('_effect') for action in character['actions']))

    def test_catalog_is_deterministic_and_keeps_sources_immutable(self):
        before = source_hashes(ASSET_ROOT)
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / 'first'
            second = Path(directory) / 'second'
            first_result = build_catalog(ASSET_ROOT, first)
            second_result = build_catalog(ASSET_ROOT, second)

            first_manifest = json.loads(first_result['manifest'].read_text(encoding='utf-8'))
            second_manifest = json.loads(second_result['manifest'].read_text(encoding='utf-8'))
            self.assertEqual(first_manifest, second_manifest)
            self.assertEqual(first_manifest['character_count'], 22)
            self.assertEqual(first_manifest['source_file_counts'], {'png': 398, 'aseprite': 44})
            self.assertEqual(len(first_manifest['shared_projectiles_and_effects']), 12)
            self.assertEqual(len(first_result['contact_sheets']), 3)
            self.assertEqual(
                [path.read_bytes() for path in first_result['contact_sheets']],
                [path.read_bytes() for path in second_result['contact_sheets']],
            )
            report = first_result['role_report'].read_text(encoding='utf-8')
            self.assertIn('assigns no gameplay roles', report)
            self.assertEqual(report.count('**User-owned role:**'), 22)
        self.assertEqual(before, source_hashes(ASSET_ROOT))


if __name__ == '__main__':
    unittest.main()
