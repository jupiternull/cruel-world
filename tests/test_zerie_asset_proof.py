import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame

from zerie_asset_proof import SAMPLES, build_proof, character_directory, discover_characters


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / 'assets/vendor/zerie'


class ZerieAssetProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_discovers_and_validates_free_samples(self):
        characters = discover_characters(ASSET_ROOT)

        self.assertEqual([character['id'] for character in characters], [
            'soldier', 'orc', 'demon_a', 'blood_monster_a',
        ])
        self.assertEqual(
            sum(sheet['frame_count'] for character in characters for sheet in character['sheets']),
            151,
        )
        for sample, character in zip(SAMPLES, characters):
            self.assertEqual(len(character['sheets']), len(sample['animations']))
            self.assertEqual(
                [(sheet['animation'], sheet['frame_count']) for sheet in character['sheets']],
                list(sample['animations']),
            )
            for sheet in character['sheets']:
                self.assertEqual(sheet['frame_size'], [100, 100])
                self.assertEqual(sheet['sheet_size'], [sheet['frame_count'] * 100, 100])

    def test_generation_is_deterministic_and_does_not_change_sources(self):
        source_paths = [
            path for sample in SAMPLES
            for animation, _ in sample['animations']
            for path in [character_directory(ASSET_ROOT, sample) / f"{sample['name']}_{animation}.png"]
        ]
        source_hashes = {
            path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths
        }
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / 'first'
            second = Path(directory) / 'second'
            first_manifest, first_contact = build_proof(ASSET_ROOT, first)
            second_manifest, second_contact = build_proof(ASSET_ROOT, second)

            self.assertEqual(
                json.loads(first_manifest.read_text(encoding='utf-8')),
                json.loads(second_manifest.read_text(encoding='utf-8')),
            )
            first_image = pygame.image.load(str(first_contact))
            second_image = pygame.image.load(str(second_contact))
            self.assertEqual(first_image.get_size(), (4008, 3404))
            self.assertEqual(first_image.get_size(), second_image.get_size())
            self.assertEqual(
                pygame.image.tostring(first_image, 'RGBA'),
                pygame.image.tostring(second_image, 'RGBA'),
            )
            self.assertEqual(
                source_hashes,
                {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths},
            )

    def test_missing_source_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, 'soldier/Idle: missing'):
            discover_characters(ROOT / 'assets/vendor/missing-zerie')


if __name__ == '__main__':
    unittest.main()
