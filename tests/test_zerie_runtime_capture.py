import hashlib
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame

from capture_zerie_runtime import (
    CANDIDATE_SCALES, ENEMY_STATES, PLAYER_STATES, capture, frames_and_anchor,
    source_path,
)


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / 'assets' / 'vendor' / 'zerie'


class ZerieRuntimeCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        if not pygame.display.get_surface():
            pygame.display.set_mode((1, 1))

    def test_calibrated_bounds_are_groundable_at_gameplay_scale(self):
        player_frames, player_anchor = frames_and_anchor(
            ASSET_ROOT, 'soldier', PLAYER_STATES, 2.5
        )
        enemy_frames, enemy_anchor = frames_and_anchor(
            ASSET_ROOT, 'orc', ENEMY_STATES, 2.5
        )

        self.assertIn('Attack2', player_frames)
        self.assertIn('Take Hit', enemy_frames)
        self.assertEqual((player_anchor.height, enemy_anchor.height), (72, 72))
        self.assertGreater(player_anchor.width, 0)
        self.assertGreater(enemy_anchor.width, 0)

    def test_capture_uses_real_gameplay_dimensions_without_changing_sources(self):
        sources = [
            source_path(ASSET_ROOT, 'soldier', animation)
            for animation in set(PLAYER_STATES.values())
        ] + [
            source_path(ASSET_ROOT, 'orc', animation)
            for animation in set(ENEMY_STATES.values())
        ]
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}

        with tempfile.TemporaryDirectory() as directory:
            gameplay, comparison = capture(Path(directory), ASSET_ROOT)
            gameplay_image = pygame.image.load(str(gameplay))
            comparison_image = pygame.image.load(str(comparison))

        self.assertEqual(gameplay_image.get_size(), (800, 600))
        self.assertEqual(comparison_image.get_size(), (400 * len(CANDIDATE_SCALES), 342))
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources})


if __name__ == '__main__':
    unittest.main()
